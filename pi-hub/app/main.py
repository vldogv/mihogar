"""
Pi-hub — FastAPI app.

Lifespan:
  - startup: Settings, logging, LastKnownState, BridgeStore (SQLite),
    BackendClient (HTTP hacia EC2), MqttClient.start(), y los background
    loops del puente Pi→EC2 (Fase 7 §7): ec2_health, config_poll,
    heartbeat, state_drain, telemetry_drain, alerts_drain.
  - shutdown: cancela todos los loops, MqttClient.stop(), cierra
    BackendClient.
"""
import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .backend_client import BackendClient
from .bridge_loop import (
    Ec2Health,
    alerts_drain_loop,
    commands_poll_loop,
    config_poll_loop,
    ec2_health_loop,
    heartbeat_loop,
    state_drain_loop,
    telemetry_drain_loop,
)
from .config import Settings
from .db import BridgeStore
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
    settings = Settings()
    _setup_logging(settings.LOG_LEVEL)
    logger = logging.getLogger("pi-hub")
    logger.info(
        "Pi-hub arrancando — broker=%s casa_id=%s backend=%s",
        settings.MQTT_BROKER_URL, settings.CASA_ID, settings.BACKEND_URL,
    )

    last_known = LastKnownState()
    bridge_store = BridgeStore(settings.DB_PATH)
    backend_client = BackendClient(settings)
    ec2_health = Ec2Health()
    mqtt = MqttClient(settings, last_known, bridge_store)

    app.state.settings = settings
    app.state.last_known = last_known
    app.state.mqtt = mqtt
    app.state.bridge_store = bridge_store

    await mqtt.start()

    tasks = [
        asyncio.create_task(ec2_health_loop(ec2_health, backend_client, settings), name="ec2-health"),
        asyncio.create_task(config_poll_loop(bridge_store, backend_client, settings), name="config-poll"),
        asyncio.create_task(heartbeat_loop(backend_client, settings), name="heartbeat"),
        asyncio.create_task(state_drain_loop(bridge_store, backend_client, ec2_health, settings), name="state-drain"),
        asyncio.create_task(telemetry_drain_loop(bridge_store, backend_client, ec2_health, settings), name="telemetry-drain"),
        asyncio.create_task(alerts_drain_loop(bridge_store, backend_client, ec2_health, settings), name="alerts-drain"),
    ]
    if settings.COMMANDS_POLL_ENABLED:
        tasks.append(
            asyncio.create_task(
                commands_poll_loop(backend_client, mqtt, ec2_health, settings), name="commands-poll",
            )
        )
        logger.warning("commands_poll_loop ACTIVO — contrato /commands no confirmado, verificar con Aldo")

    try:
        yield
    finally:
        logger.info("Pi-hub deteniendo")
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await mqtt.stop()
        await backend_client.aclose()
        logger.info("Pi-hub detenido limpiamente")


app = FastAPI(
    title="Mi Hogar — Pi-hub",
    description=(
        "Servicio local que corre en la Raspberry Pi. Expone el contrato "
        "PWA↔hub (HTTP), traduce a MQTT contra el ESP32, y sincroniza "
        "estado, telemetría y alertas hacia EC2 vía el puente SQLite (Fase 7 §7)."
    ),
    version="0.3.0",
    lifespan=lifespan,
)

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
