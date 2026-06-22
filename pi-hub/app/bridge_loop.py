"""
Background tasks del puente Pi → EC2 (Fase 7 §7).

  - ec2_health_loop:      prueba GET /api/health cada EC2_HEALTH_CACHE_SECONDS.
  - config_poll_loop:     descarga config de EC2 y la guarda en config_cache.
  - heartbeat_loop:       manda heartbeat a EC2.
  - state_drain_loop:     vacía el snapshot pendiente de state_queue hacia
                           POST /api/device/sync/state.
  - telemetry_drain_loop: vacía telemetry_queue hacia
                           POST /api/device/sync/telemetry, en batches.
                           Agregado 21/jun/2026 — requiere que el ESP32-C5
                           empiece a publicar en mihogar/<casa>/telemetry.
  - alerts_drain_loop:    vacía alerts_queue hacia
                           POST /api/device/sync/alerts, de a una alerta.
                           Agregado 21/jun/2026 — requiere que el ESP32-C5
                           empiece a publicar en mihogar/<casa>/alerts.
  - commands_poll_loop:   DECISIÓN CERRADA DE EQUIPO (confirmada por Aldo,
                           21/jun/2026): se queda desactivado permanentemente.
                           GET /api/device/sync/commands es un stub que
                           siempre regresa []. El canal de comandos inmediatos
                           es MQTT, ya implementado y probado end-to-end.
                           /api/device/sync/* es solo sincronización diferida.
"""
import asyncio
import logging

from .backend_client import BackendClient
from .config import Settings
from .db import BridgeStore
from .mqtt_client import AckTimeout, BrokerUnavailable, MqttClient

logger = logging.getLogger(__name__)

_TELEMETRY_BATCH_SIZE = 50  # máximo de lecturas por POST /telemetry


class Ec2Health:
    def __init__(self) -> None:
        self._reachable = False
        self._lock = asyncio.Lock()

    async def set(self, reachable: bool) -> None:
        async with self._lock:
            self._reachable = reachable

    async def is_reachable(self) -> bool:
        async with self._lock:
            return self._reachable


async def ec2_health_loop(
    health: Ec2Health, client: BackendClient, settings: Settings,
) -> None:
    logger.info(
        "ec2_health_loop iniciado (intervalo=%ds)", settings.EC2_HEALTH_CACHE_SECONDS,
    )
    try:
        while True:
            reachable = await client.check_health()
            await health.set(reachable)
            logger.debug("ec2_health: reachable=%s", reachable)
            await asyncio.sleep(settings.EC2_HEALTH_CACHE_SECONDS)
    except asyncio.CancelledError:
        logger.info("ec2_health_loop cancelado limpiamente")
        raise


async def config_poll_loop(
    store: BridgeStore, client: BackendClient, settings: Settings,
) -> None:
    logger.info(
        "config_poll_loop iniciado (intervalo=%ds)", settings.CONFIG_POLL_SECONDS,
    )
    try:
        while True:
            payload = await client.download_config()
            if payload is None:
                logger.warning("config_poll: descarga falló, se mantiene el cache anterior")
            else:
                await store.set_config_cache(payload)
                logger.info("config_poll: config_cache actualizado")
            await asyncio.sleep(settings.CONFIG_POLL_SECONDS)
    except asyncio.CancelledError:
        logger.info("config_poll_loop cancelado limpiamente")
        raise


async def heartbeat_loop(client: BackendClient, settings: Settings) -> None:
    logger.info(
        "heartbeat_loop iniciado (intervalo=%ds)", settings.HEARTBEAT_SECONDS,
    )
    try:
        while True:
            await asyncio.sleep(settings.HEARTBEAT_SECONDS)
            ok = await client.post_heartbeat()
            logger.debug("heartbeat %s", "OK" if ok else "falló")
    except asyncio.CancelledError:
        logger.info("heartbeat_loop cancelado limpiamente")
        raise


async def state_drain_loop(
    store: BridgeStore, client: BackendClient, health: Ec2Health, settings: Settings,
) -> None:
    logger.info(
        "state_drain_loop iniciado (intervalo=%ds)", settings.DRAIN_INTERVAL_SECONDS,
    )
    try:
        while True:
            await asyncio.sleep(settings.DRAIN_INTERVAL_SECONDS)
            pending = await store.peek_state()
            if pending is None:
                continue
            zonas, attempts = pending
            if not await health.is_reachable():
                logger.debug("state_drain: EC2 no alcanzable, se mantiene en cola")
                continue
            results = await client.post_state_batch(zonas)
            if results is None:
                await store.bump_state_attempts()
                logger.warning(
                    "state_drain: envío falló (intento previo #%d), se reintenta luego",
                    attempts,
                )
                continue
            await store.clear_state()
            applied = sum(1 for r in results if r.get("status") == "applied")
            logger.info(
                "state_drain: sincronizado — %d/%d zonas applied",
                applied, len(results),
            )
    except asyncio.CancelledError:
        logger.info("state_drain_loop cancelado limpiamente")
        raise


async def telemetry_drain_loop(
    store: BridgeStore, client: BackendClient, health: Ec2Health, settings: Settings,
) -> None:
    """Vacía telemetry_queue hacia POST /api/device/sync/telemetry.

    Procesa en batches de hasta _TELEMETRY_BATCH_SIZE lecturas por ciclo
    para no mandar payloads enormes en una sola llamada. Si EC2 no está
    alcanzable, deja la cola intacta para el siguiente ciclo.
    """
    logger.info(
        "telemetry_drain_loop iniciado (intervalo=%ds)", settings.DRAIN_INTERVAL_SECONDS,
    )
    try:
        while True:
            await asyncio.sleep(settings.DRAIN_INTERVAL_SECONDS)
            if not await health.is_reachable():
                logger.debug("telemetry_drain: EC2 no alcanzable, se mantiene en cola")
                continue
            batch = []
            row_ids = []
            for _ in range(_TELEMETRY_BATCH_SIZE):
                row = await store.peek_fifo("telemetry_queue")
                if row is None:
                    break
                row_id, lectura, _ = row
                batch.append(lectura)
                row_ids.append(row_id)
                await store.delete_fifo("telemetry_queue", row_id)
            if not batch:
                continue
            ok = await client.post_telemetry(batch)
            if ok:
                logger.info("telemetry_drain: %d lecturas enviadas", len(batch))
            else:
                logger.warning(
                    "telemetry_drain: envío de %d lecturas falló — ya se eliminaron de la cola "
                    "(telemetría es best-effort, no se reencola)", len(batch),
                )
    except asyncio.CancelledError:
        logger.info("telemetry_drain_loop cancelado limpiamente")
        raise


async def alerts_drain_loop(
    store: BridgeStore, client: BackendClient, health: Ec2Health, settings: Settings,
) -> None:
    """Vacía alerts_queue hacia POST /api/device/sync/alerts.

    Las alertas se envían de a una (no en batch) para que un fallo en
    una no bloquee el resto. A diferencia de la telemetría, las alertas
    sí se reintentan: si el envío falla, la fila se deja en la cola para
    el siguiente ciclo (no se borra).
    """
    logger.info(
        "alerts_drain_loop iniciado (intervalo=%ds)", settings.DRAIN_INTERVAL_SECONDS,
    )
    try:
        while True:
            await asyncio.sleep(settings.DRAIN_INTERVAL_SECONDS)
            if not await health.is_reachable():
                logger.debug("alerts_drain: EC2 no alcanzable, se mantiene en cola")
                continue
            while True:
                row = await store.peek_fifo("alerts_queue")
                if row is None:
                    break
                row_id, alerta, attempts = row
                ok = await client.post_alerts([alerta])
                if ok:
                    await store.delete_fifo("alerts_queue", row_id)
                    logger.info("alerts_drain: alerta tipo=%s enviada", alerta.get("tipo"))
                else:
                    logger.warning(
                        "alerts_drain: alerta tipo=%s falló (intento #%d), se reintenta",
                        alerta.get("tipo"), attempts,
                    )
                    break
    except asyncio.CancelledError:
        logger.info("alerts_drain_loop cancelado limpiamente")
        raise


_COMMAND_TOPIC_MAP = {
    "encender": lambda c: (f"zones/{c['zona_id']}/toggle", {"encendida": True}),
    "apagar": lambda c: (f"zones/{c['zona_id']}/toggle", {"encendida": False}),
    "cambiar_modo": lambda c: (
        f"zones/{c['zona_id']}/mode", {"modo": c.get("parametros", {}).get("modo")},
    ),
}


async def commands_poll_loop(
    client: BackendClient, mqtt: MqttClient, health: Ec2Health, settings: Settings,
) -> None:
    """Camino inverso EC2 → ESP32. NO SE USA — ver docstring del módulo.

    Decisión cerrada de equipo (Aldo, 21/jun/2026): el canal de comandos
    inmediatos es MQTT, ya implementado y probado. Este loop existe solo
    como código de referencia; no hay plan de activarlo
    (COMMANDS_POLL_ENABLED se queda en false permanentemente).
    """
    logger.info(
        "commands_poll_loop iniciado (intervalo=%ds) — NOTA: este camino fue descartado, ver docstring del módulo",
        settings.COMMANDS_POLL_SECONDS,
    )
    try:
        while True:
            await asyncio.sleep(settings.COMMANDS_POLL_SECONDS)
            if not await health.is_reachable():
                continue
            commands = await client.get_commands()
            if not commands:
                continue
            for cmd in commands:
                await _execute_command(cmd, mqtt)
    except asyncio.CancelledError:
        logger.info("commands_poll_loop cancelado limpiamente")
        raise


async def _execute_command(cmd: dict, mqtt: MqttClient) -> None:
    comando = cmd.get("comando")
    builder = _COMMAND_TOPIC_MAP.get(comando)
    cmd_id = cmd.get("id", "desconocido")
    if builder is None:
        logger.warning("commands_poll: comando no manejado '%s' (id=%s)", comando, cmd_id)
        return
    try:
        topic_suffix, body = builder(cmd)
        ack = await mqtt.publish_command(topic_suffix, body)
        logger.info("commands_poll: id=%s entregado al ESP32, ack status=%s", cmd_id, ack.get("status"))
    except AckTimeout:
        logger.warning("commands_poll: id=%s sin respuesta del ESP32 (timeout)", cmd_id)
    except BrokerUnavailable:
        logger.warning("commands_poll: id=%s — broker MQTT no disponible", cmd_id)
