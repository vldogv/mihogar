"""
MQTT loop del mock ESP32 — Fase 6.

Simula el comportamiento del ESP32 sobre el broker MQTT local de la Pi:
  - Al conectar: publica info y state con flag retained=true.
  - Suscribe a mihogar/<casa>/cmd/# para escuchar comandos del hub.
  - Aplica cada comando al InMemoryState (con LWW) y responde con ack en
    mihogar/<casa>/ack/<req_id>. Después republica state retained.

Topic spec en docs/topics-mqtt-pi-esp32.md (BORRADOR). Si la conexión cae,
hace reconnect con backoff exponencial (cap 30s).
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

import aiomqtt

from .config import Settings
from .state import InMemoryState

logger = logging.getLogger(__name__)

_BACKOFF_BASE = 1.0
_BACKOFF_MAX = 30.0


def _parse_broker_url(url: str) -> tuple[str, int]:
    """mqtt://host:port → (host, port). Acepta también host:port plano."""
    if "://" in url:
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 1883
    else:
        # "host:port" o "host"
        if ":" in url:
            host_s, port_s = url.split(":", 1)
            host, port = host_s, int(port_s)
        else:
            host, port = url, 1883
    return host, port


def _topic_prefix(casa_id: str) -> str:
    return f"mihogar/{casa_id}"


async def _publish_info_and_state(
    client: aiomqtt.Client, state: InMemoryState, casa_id: str,
) -> None:
    """Publica info y state retained al (re)conectar."""
    prefix = _topic_prefix(casa_id)

    async with state.lock:
        info = state.info
        state_payload = state.state_payload()

    if info is not None:
        await client.publish(
            f"{prefix}/info", payload=json.dumps(info), qos=1, retain=True,
        )
        logger.info("MQTT: info retained publicado")

    await client.publish(
        f"{prefix}/state", payload=json.dumps(state_payload), qos=1, retain=True,
    )
    logger.info("MQTT: state retained publicado (zonas=%d)", len(state_payload["zonas"]))

    # LWT online flag (LWT real lo configura el will= en connect; esto es el
    # corolario "estoy vivo")
    await client.publish(
        f"{prefix}/status", payload=json.dumps({"online": True}), qos=1, retain=True,
    )


async def _handle_command(
    client: aiomqtt.Client,
    state: InMemoryState,
    casa_id: str,
    topic: str,
    payload_raw: bytes,
) -> None:
    """Parsea un comando, aplica y publica ack + nuevo state."""
    prefix = _topic_prefix(casa_id)

    try:
        body = json.loads(payload_raw.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        logger.warning("MQTT: payload no es JSON válido en %s: %s", topic, exc)
        return

    req_id = body.get("req_id")
    if not req_id:
        logger.warning("MQTT: comando sin req_id en %s, ignorado", topic)
        return

    client_id = body.get("client_id")
    client_ts = body.get("client_timestamp")

    # Parse del topic: mihogar/<casa>/cmd/<resto>
    # resto puede ser: zones/<zona_id>/toggle, zones/<zona_id>/mode, scene/all-on, scene/all-off
    parts = topic.split("/")
    # Espera: ["mihogar", casa_id, "cmd", ...]
    if len(parts) < 4 or parts[0] != "mihogar" or parts[2] != "cmd":
        logger.warning("MQTT: topic inesperado %s", topic)
        return
    cmd_parts = parts[3:]

    ack_payload: dict[str, Any]

    if len(cmd_parts) == 3 and cmd_parts[0] == "zones" and cmd_parts[2] == "toggle":
        zona_id = cmd_parts[1]
        encendida = body.get("encendida")
        if encendida is None:
            logger.warning("MQTT: toggle sin 'encendida' en %s", topic)
            return
        status, server_ts = await state.try_apply_command(
            zona_id, encendida=bool(encendida), client_timestamp=client_ts,
        )
        ack_payload = {
            "req_id": req_id,
            "client_id": client_id,
            "zona_id": zona_id,
            "status": status,
            "server_timestamp": server_ts,
        }
    elif len(cmd_parts) == 3 and cmd_parts[0] == "zones" and cmd_parts[2] == "mode":
        zona_id = cmd_parts[1]
        modo = body.get("modo")
        if modo is None:
            logger.warning("MQTT: mode sin 'modo' en %s", topic)
            return
        status, server_ts = await state.try_apply_command(
            zona_id, modo=str(modo), client_timestamp=client_ts,
        )
        ack_payload = {
            "req_id": req_id,
            "client_id": client_id,
            "zona_id": zona_id,
            "status": status,
            "server_timestamp": server_ts,
        }
    elif cmd_parts == ["scene", "all-on"]:
        server_ts, afectadas = await state.apply_scene_all(True, client_ts)
        ack_payload = {
            "req_id": req_id,
            "client_id": client_id,
            "status": "applied",
            "server_timestamp": server_ts,
            "zonas_afectadas": afectadas,
        }
    elif cmd_parts == ["scene", "all-off"]:
        server_ts, afectadas = await state.apply_scene_all(False, client_ts)
        ack_payload = {
            "req_id": req_id,
            "client_id": client_id,
            "status": "applied",
            "server_timestamp": server_ts,
            "zonas_afectadas": afectadas,
        }
    else:
        logger.warning("MQTT: comando desconocido %s", topic)
        return

    # Publish ack
    await client.publish(
        f"{prefix}/ack/{req_id}",
        payload=json.dumps(ack_payload),
        qos=1,
        retain=False,
    )
    logger.info(
        "MQTT: ack publicado req_id=%s status=%s topic=%s",
        req_id, ack_payload.get("status"), topic,
    )

    # Re-publish state retained si hubo cambio efectivo
    if ack_payload.get("status") == "applied":
        async with state.lock:
            payload = state.state_payload()
        await client.publish(
            f"{prefix}/state", payload=json.dumps(payload), qos=1, retain=True,
        )


async def mqtt_loop(state: InMemoryState, settings: Settings) -> None:
    """Background task: conecta al broker MQTT, escucha comandos, publica state/ack.

    Reconexión con backoff exponencial en MqttError. Cancelable.
    """
    casa_id = settings.MOCK_CASA_ID
    host, port = _parse_broker_url(settings.MQTT_BROKER_URL)
    prefix = _topic_prefix(casa_id)
    will = aiomqtt.Will(
        topic=f"{prefix}/status",
        payload=json.dumps({"online": False}),
        qos=1,
        retain=True,
    )
    attempt = 0
    logger.info("MQTT loop iniciado — broker=%s:%d casa=%s", host, port, casa_id)
    try:
        while True:
            try:
                async with aiomqtt.Client(
                    hostname=host,
                    port=port,
                    identifier=f"mock-esp32-{casa_id}",
                    will=will,
                ) as client:
                    attempt = 0
                    await _publish_info_and_state(client, state, casa_id)
                    await client.subscribe(f"{prefix}/cmd/#", qos=1)
                    logger.info("MQTT: suscrito a %s/cmd/#", prefix)
                    try:
                        async for message in client.messages:
                            await _handle_command(
                                client, state, casa_id, str(message.topic), message.payload,
                            )
                    except asyncio.CancelledError:
                        # Graceful shutdown: el broker NO publica el LWT en
                        # disconnects limpios (spec MQTT), así que lo hacemos
                        # explícito acá para que el hub vea offline=false al
                        # bajar el mock con docker compose stop / SIGTERM.
                        try:
                            await client.publish(
                                f"{prefix}/status",
                                payload=json.dumps({"online": False}),
                                qos=1,
                                retain=True,
                            )
                            logger.info("MQTT: offline retained publicado (shutdown)")
                        except Exception as exc:  # noqa: BLE001 — best effort
                            logger.warning(
                                "MQTT: no se pudo publicar offline en shutdown: %s", exc,
                            )
                        raise
            except aiomqtt.MqttError as exc:
                wait = min(_BACKOFF_BASE * (2 ** attempt), _BACKOFF_MAX)
                logger.warning(
                    "MQTT: conexión caída (%s). Reintento en %.1fs", exc, wait,
                )
                attempt += 1
                await asyncio.sleep(wait)
    except asyncio.CancelledError:
        logger.info("MQTT loop cancelado limpiamente")
        raise
