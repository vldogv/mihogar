"""
Pi-hub — FastAPI app.

Expone el contrato HTTP local (docs/contrato-api-local-esp32.md) y le habla
al ESP32 por MQTT (docs/topics-mqtt-pi-esp32.md, BORRADOR).

Lifespan:
  - startup: Settings (falla si CASA_ID no vino), logging, LastKnownState,
    MqttClient.start() (lanza el background task de conexión).
  - shutdown: MqttClient.stop() (cancela task + futures pendientes).
"""
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .mqtt_client import MqttClient
from .routes import health as health_routes
from .routes import scenes as scenes_routes
from .routes import state as state_routes
from .routes import zones as zones_routes
from .state import LastKnownState


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        stream=sys.stdout,
        force=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()  # ValidationError si falta CASA_ID
    _setup_logging(settings.LOG_LEVEL)
    logger = logging.getLogger("pi-hub")
    logger.info(
        "Pi-hub arrancando — broker=%s casa_id=%s ack_timeout=%.1fs",
        settings.MQTT_BROKER_URL, settings.CASA_ID, settings.ACK_TIMEOUT_SECONDS,
    )

    last_known = LastKnownState()
    mqtt = MqttClient(settings, last_known)

    app.state.settings = settings
    app.state.last_known = last_known
    app.state.mqtt = mqtt

    await mqtt.start()
    try:
        yield
    finally:
        logger.info("Pi-hub deteniendo")
        await mqtt.stop()
        logger.info("Pi-hub detenido limpiamente")


app = FastAPI(
    title="Mi Hogar — Pi-hub",
    description=(
        "Servicio local que corre en la Raspberry Pi. Expone el contrato "
        "PWA↔hub (HTTP) y traduce a MQTT contra el ESP32."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS abierto para dev (PWA en localhost:3000). En prod la Pi servirá la PWA
# en el mismo origen, así que esto deja de ser necesario.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_routes.router)
app.include_router(state_routes.router)
app.include_router(zones_routes.router)
app.include_router(scenes_routes.router)
