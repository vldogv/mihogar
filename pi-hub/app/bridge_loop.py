"""
Background tasks del puente Pi → EC2 (Fase 7 §7).

Cinco loops independientes, cancelables (mismo patrón que
mock-esp32/app/sync_loop.py):

  - ec2_health_loop:    prueba GET /api/health cada EC2_HEALTH_CACHE_SECONDS,
                         mantiene un flag cacheado que los demás loops leen
                         antes de intentar hablar con EC2.
  - config_poll_loop:   descarga config de EC2 y la guarda en config_cache.
  - heartbeat_loop:     manda heartbeat a EC2.
  - state_drain_loop:   vacía el snapshot pendiente de state_queue hacia
                         POST /api/device/sync/state.
  - commands_poll_loop: (DESHABILITADO por default) GET /api/device/sync/
                         commands y ejecuta cada uno vía
                         mqtt.publish_command() — el mismo mecanismo que ya
                         usan las rutas HTTP de zonas/escenas.
"""
import asyncio
import logging

from .backend_client import BackendClient
from .config import Settings
from .db import BridgeStore
from .mqtt_client import AckTimeout, BrokerUnavailable, MqttClient

logger = logging.getLogger(__name__)


class Ec2Health:
    """Flag cacheado de si EC2 respondió la última vez que se probó."""

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
    """Vacía el snapshot de state_queue hacia EC2 cuando esté alcanzable."""
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


_COMMAND_TOPIC_MAP = {
    "zona_toggle": lambda c: (f"zones/{c['zona_id']}/toggle", {"encendida": c["encendida"]}),
    "zona_mode": lambda c: (f"zones/{c['zona_id']}/mode", {"modo": c["modo"]}),
    "scene_all_on": lambda c: ("scene/all-on", {}),
    "scene_all_off": lambda c: ("scene/all-off", {}),
}


async def commands_poll_loop(
    client: BackendClient, mqtt: MqttClient, health: Ec2Health, settings: Settings,
) -> None:
    """Camino inverso: EC2 → ESP32. Contrato de /commands ASUMIDO.

    Desactivado por default (COMMANDS_POLL_ENABLED=false) hasta confirmar
    el schema real con Aldo.
    """
    logger.info(
        "commands_poll_loop iniciado (intervalo=%ds) — CONTRATO ASUMIDO, NO CONFIRMADO",
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
                await _execute_command(cmd, client, mqtt)
    except asyncio.CancelledError:
        logger.info("commands_poll_loop cancelado limpiamente")
        raise


async def _execute_command(cmd: dict, client: BackendClient, mqtt: MqttClient) -> None:
    tipo = cmd.get("tipo")
    builder = _COMMAND_TOPIC_MAP.get(tipo)
    command_id = cmd.get("command_id", "desconocido")
    if builder is None:
        logger.warning("commands_poll: tipo desconocido '%s' (command_id=%s)", tipo, command_id)
        await client.post_command_ack(command_id, "rejected", {"reason": f"tipo desconocido: {tipo}"})
        return
    try:
        topic_suffix, body = builder(cmd)
        ack = await mqtt.publish_command(topic_suffix, body)
        await client.post_command_ack(command_id, "delivered", ack)
        logger.info("commands_poll: command_id=%s entregado, ack status=%s", command_id, ack.get("status"))
    except AckTimeout:
        logger.warning("commands_poll: command_id=%s sin respuesta del ESP32 (timeout)", command_id)
        await client.post_command_ack(command_id, "timeout")
    except BrokerUnavailable:
        logger.warning("commands_poll: command_id=%s — broker MQTT no disponible", command_id)
        await client.post_command_ack(command_id, "broker_unavailable")
