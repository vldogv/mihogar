"""
Background tasks del mock ESP32.

Tres loops independientes:
  - config_poll_loop: descarga config y actualiza estado in-memory.
  - heartbeat_loop:   manda heartbeat al backend.
  - telemetry_loop:   manda telemetría dummy random (opcional).

Todos son cancelables: en shutdown del lifespan se les hace .cancel()
y se hace await asyncio.gather(..., return_exceptions=True). Cada loop
captura CancelledError, loguea "cancelado limpiamente" y re-raisea
para que asyncio.gather lo cuente como cancelado.
"""
import asyncio
import logging
import random
from datetime import datetime, timezone

from .backend_client import BackendClient
from .config import Settings
from .state import InMemoryState

logger = logging.getLogger(__name__)


async def config_poll_loop(
    state: InMemoryState, client: BackendClient, settings: Settings,
) -> None:
    """Descarga config cada CONFIG_POLL_SECONDS.

    Para no spamear el log:
      - INFO solo cuando la config cambia (comparado por hash en state.replace_config)
      - DEBUG en pollings sin cambios
      - WARNING si la descarga falla
    """
    logger.info(
        "config_poll_loop iniciado (intervalo=%ds)", settings.CONFIG_POLL_SECONDS,
    )
    try:
        while True:
            payload = await client.download_config()
            if payload is None:
                logger.warning(
                    "config_poll: descarga falló, reintento en %ds",
                    settings.CONFIG_POLL_SECONDS,
                )
            else:
                changed = await state.replace_config(payload)
                if changed:
                    logger.info(
                        "config_poll: config actualizada — "
                        "zonas=%d temporizadores=%d dispositivos=%d",
                        len(state.zonas),
                        len(state.temporizadores),
                        len(state.dispositivos),
                    )
                else:
                    logger.debug("config_poll: sin cambios")
            await asyncio.sleep(settings.CONFIG_POLL_SECONDS)
    except asyncio.CancelledError:
        logger.info("config_poll_loop cancelado limpiamente")
        raise


async def heartbeat_loop(client: BackendClient, settings: Settings) -> None:
    """Manda heartbeat cada HEARTBEAT_SECONDS.

    Espera un intervalo antes del primero para no colisionar con el
    primer config_poll en el arranque.
    """
    logger.info(
        "heartbeat_loop iniciado (intervalo=%ds)", settings.HEARTBEAT_SECONDS,
    )
    try:
        while True:
            await asyncio.sleep(settings.HEARTBEAT_SECONDS)
            ok = await client.post_heartbeat()
            if ok:
                logger.debug("heartbeat OK")
            else:
                logger.warning("heartbeat falló")
    except asyncio.CancelledError:
        logger.info("heartbeat_loop cancelado limpiamente")
        raise


async def telemetry_loop(
    state: InMemoryState, client: BackendClient, settings: Settings,
) -> None:
    """Manda telemetría dummy random por zona cada TELEMETRY_SECONDS.

    Solo corre si MOCK_SEND_TELEMETRY=true. Valores plausibles:
      - luz_ambiente: 0-100
      - movimiento:   ~10% true
      - temperatura:  18-28 °C
      - estado_luz:   derivado del estado local de la zona

    Útil para llenar el dashboard durante desarrollo. NO refleja
    comportamiento del firmware real (en prod la telemetría va por MQTT,
    no por este endpoint).
    """
    logger.info(
        "telemetry_loop iniciado (intervalo=%ds)", settings.TELEMETRY_SECONDS,
    )
    try:
        while True:
            await asyncio.sleep(settings.TELEMETRY_SECONDS)
            async with state.lock:
                zonas_snapshot = list(state.zonas)
            if not zonas_snapshot:
                logger.debug("telemetry: sin zonas cargadas, skip")
                continue
            now_iso = datetime.now(timezone.utc).isoformat()
            lecturas = [
                {
                    "zona_id": z["zona_id"],
                    "timestamp": now_iso,
                    "luz_ambiente": random.randint(0, 100),
                    "movimiento": random.random() < 0.1,
                    "temperatura": round(random.uniform(18.0, 28.0), 1),
                    "estado_luz": "encendida" if z.get("encendida") else "apagada",
                }
                for z in zonas_snapshot
            ]
            ok = await client.post_telemetry(lecturas)
            if ok:
                logger.debug("telemetry: %d lecturas enviadas", len(lecturas))
            else:
                logger.warning("telemetry: envío falló")
    except asyncio.CancelledError:
        logger.info("telemetry_loop cancelado limpiamente")
        raise
