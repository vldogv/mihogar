"""
Background tasks del puente Pi → EC2 (Fase 7 §7).

  - ec2_health_loop:    prueba GET /api/health cada EC2_HEALTH_CACHE_SECONDS.
  - config_poll_loop:   descarga config de EC2 y la guarda en config_cache.
  - heartbeat_loop:     manda heartbeat a EC2.
  - state_drain_loop:   vacía el snapshot pendiente de state_queue hacia
                         POST /api/device/sync/state.
  - commands_poll_loop: DECISIÓN CERRADA DE EQUIPO (confirmada por Aldo,
                         21/jun/2026): se queda desactivado permanentemente,
                         no "pendiente de confirmar". GET /api/device/sync/
                         commands es un stub que siempre regresa [] y se
                         queda así a propósito — el canal de comandos
                         inmediatos del proyecto es MQTT (PWA → pi-hub →
                         MQTT → ESP32, ya implementado y probado
                         end-to-end). /api/device/sync/* es solo
                         sincronización diferida (telemetría/estado/config
                         vía polling de /config). Este loop y su mapeo de
                         comandos se dejan en el código como referencia,
                         pero no hay plan de activarlos.
"""
import asyncio
import logging

from .backend_client import BackendClient
from .config import Settings
from .db import BridgeStore
from .mqtt_client import AckTimeout, BrokerUnavailable, MqttClient

logger = logging.getLogger(__name__)


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


# Mapeo confirmado contra PendingCommand.comando en device_sync_routes.py.
# Se deja como referencia histórica — ver docstring del módulo: este loop
# no se activa, decisión cerrada de equipo.
# "actualizar_config" no mapea a un comando MQTT de zona — no se incluye.
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
    como código de referencia por si algún día se reconsidera; no hay
    plan de activarlo (COMMANDS_POLL_ENABLED se queda en false).
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
