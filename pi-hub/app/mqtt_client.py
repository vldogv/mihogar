"""
Cliente MQTT del Pi-hub.

Responsabilidades:
  - Conectar al broker y mantener la conexión (reconnect con backoff).
  - Suscribir a info, state, status y ack/<req_id>.
  - Mantener el LastKnownState a partir de los retained de info/state.
  - Encolar cada `state` nuevo en BridgeStore.state_queue (puente Pi→EC2).
  - Exponer publish_command(topic_suffix, body) que: genera req_id, publica
    en mihogar/<casa>/cmd/<topic_suffix>, espera el ack en
    mihogar/<casa>/ack/<req_id> con timeout, devuelve el payload del ack.

El cliente expone publish_command como interfaz pública para los handlers
HTTP. Internamente mantiene un dict req_id → asyncio.Future que el listener
resuelve cuando llega el ack correspondiente.

Spec MQTT: docs/topics-mqtt-pi-esp32.md (BORRADOR).
"""
import asyncio
import json
import logging
import uuid
from typing import Any, Optional
from urllib.parse import urlparse

import aiomqtt

from .config import Settings
from .db import BridgeStore
from .state import LastKnownState

logger = logging.getLogger(__name__)

_BACKOFF_BASE = 1.0
_BACKOFF_MAX = 30.0


def _parse_broker_url(url: str) -> tuple[str, int]:
    if "://" in url:
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 1883
    else:
        if ":" in url:
            host_s, port_s = url.split(":", 1)
            host, port = host_s, int(port_s)
        else:
            host, port = url, 1883
    return host, port


class AckTimeout(Exception):
    """Se levantó timeout esperando un ack del ESP32."""


class BrokerUnavailable(Exception):
    """No hay conexión activa al broker en este momento."""


class MqttClient:
    def __init__(self, settings: Settings, state: LastKnownState, bridge_store: BridgeStore) -> None:
        self._settings = settings
        self._state = state
        self._bridge_store = bridge_store
        self._client: Optional[aiomqtt.Client] = None
        self._pending: dict[str, asyncio.Future] = {}
        self._task: Optional[asyncio.Task] = None
        self._prefix = f"mihogar/{settings.CASA_ID}"

    # ── Lifecycle ─────────────────────────────────────────────

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run(), name="pi-hub-mqtt")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        for fut in self._pending.values():
            if not fut.done():
                fut.set_exception(BrokerUnavailable("MQTT client stopped"))
        self._pending.clear()

    # ── Run loop ──────────────────────────────────────────────

    async def _run(self) -> None:
        host, port = _parse_broker_url(self._settings.MQTT_BROKER_URL)
        attempt = 0
        logger.info("Pi-hub MQTT: conectando a %s:%d (casa=%s)", host, port, self._settings.CASA_ID)
        try:
            while True:
                try:
                    async with aiomqtt.Client(
                        hostname=host,
                        port=port,
                        identifier=f"{self._settings.DEVICE_ID}-{self._settings.CASA_ID}",
                    ) as client:
                        self._client = client
                        attempt = 0
                        await client.subscribe(f"{self._prefix}/info", qos=1)
                        await client.subscribe(f"{self._prefix}/state", qos=1)
                        await client.subscribe(f"{self._prefix}/status", qos=1)
                        await client.subscribe(f"{self._prefix}/ack/+", qos=1)
                        logger.info("Pi-hub MQTT: suscripciones OK")
                        async for message in client.messages:
                            await self._handle_message(str(message.topic), message.payload)
                except aiomqtt.MqttError as exc:
                    self._client = None
                    wait = min(_BACKOFF_BASE * (2 ** attempt), _BACKOFF_MAX)
                    logger.warning(
                        "Pi-hub MQTT: caído (%s). Reintento en %.1fs", exc, wait,
                    )
                    attempt += 1
                    await asyncio.sleep(wait)
        except asyncio.CancelledError:
            self._client = None
            logger.info("Pi-hub MQTT: loop cancelado limpiamente")
            raise

    # ── Message handling ──────────────────────────────────────

    async def _handle_message(self, topic: str, payload_raw: bytes) -> None:
        try:
            body = json.loads(payload_raw.decode())
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            logger.warning("Pi-hub MQTT: payload no JSON en %s: %s", topic, exc)
            return

        if topic == f"{self._prefix}/state":
            await self._state.set_state(body)
            zonas = body.get("zonas", [])
            if zonas:
                await self._bridge_store.enqueue_state(zonas)
            logger.debug("Pi-hub MQTT: state actualizado")
        elif topic == f"{self._prefix}/info":
            await self._state.set_info(body)
            logger.debug("Pi-hub MQTT: info actualizada")
        elif topic == f"{self._prefix}/status":
            online = bool(body.get("online", False))
            await self._state.set_esp32_online(online)
            logger.info("Pi-hub MQTT: ESP32 status online=%s", online)
        elif topic.startswith(f"{self._prefix}/ack/"):
            req_id = topic.rsplit("/", 1)[-1]
            fut = self._pending.pop(req_id, None)
            if fut is None:
                logger.info("Pi-hub MQTT: ack tardío/desconocido req_id=%s — ignorado", req_id)
                return
            if not fut.done():
                fut.set_result(body)
        else:
            logger.debug("Pi-hub MQTT: mensaje en topic no suscrito %s", topic)

    # ── API pública ───────────────────────────────────────────

    async def publish_command(
        self, topic_suffix: str, body: dict[str, Any],
    ) -> dict[str, Any]:
        if self._client is None:
            raise BrokerUnavailable("No hay conexión activa al broker")

        req_id = str(uuid.uuid4())
        payload = dict(body)
        payload["req_id"] = req_id

        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending[req_id] = fut

        topic = f"{self._prefix}/cmd/{topic_suffix}"
        try:
            await self._client.publish(topic, payload=json.dumps(payload), qos=1)
            return await asyncio.wait_for(fut, timeout=self._settings.ACK_TIMEOUT_SECONDS)
        except asyncio.TimeoutError as exc:
            raise AckTimeout(f"No llegó ack en {self._settings.ACK_TIMEOUT_SECONDS}s") from exc
        finally:
            self._pending.pop(req_id, None)
