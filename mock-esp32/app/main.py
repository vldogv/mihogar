"""
Mock ESP32 Master — FastAPI app.

Lifespan:
  - startup: instancia Settings (falla rápido si MOCK_CASA_ID no vino),
    arma logging stdlib con LOG_LEVEL, crea BackendClient + InMemoryState,
    lanza los background tasks (config_poll, heartbeat, telemetría opcional).
  - shutdown: cancela las tasks y las espera con gather(return_exceptions=True)
    para que docker compose down baje limpio sin colgarse.

Routes:
  - GET  /health         — diagnóstico
  - POST /mock/toggle/{zona_id}
  - POST /mock/state/batch
  - GET  /mock/state
"""
import asyncio
import json
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from .backend_client import BackendClient
from .config import Settings
from .mqtt_loop import mqtt_loop
from .routes import health as health_routes
from .routes import mock as mock_routes
from .state import InMemoryState
from .sync_loop import config_poll_loop, heartbeat_loop, telemetry_loop


def _setup_logging(level: str) -> None:
    """Logging stdlib a stdout con timestamps ISO."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        stream=sys.stdout,
        force=True,  # uvicorn ya configuró root logger; lo pisamos
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = Settings()  # ValidationError si falta MOCK_CASA_ID
    _setup_logging(settings.LOG_LEVEL)
    logger = logging.getLogger("mock-esp32")

    logger.info(
        "Mock ESP32 arrancando — backend=%s casa_id=%s telemetry=%s",
        settings.BACKEND_URL, settings.MOCK_CASA_ID, settings.MOCK_SEND_TELEMETRY,
    )

    state = InMemoryState()
    client = BackendClient(settings)

    # Cargar seed antes de arrancar loops, si está configurado.
    if settings.MOCK_SEED_FILE:
        seed_path = Path(settings.MOCK_SEED_FILE)
        if not seed_path.is_absolute():
            # Resuelvo relativo al package, no al CWD — así MOCK_SEED_FILE=
            # "app/fixtures/seed_state.json" funciona en standalone y compose.
            seed_path = Path(__file__).parent.parent / seed_path
        try:
            seed_payload = json.loads(seed_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Seed file %s no se pudo cargar: %s", seed_path, exc)
            raise
        await state.replace_config(seed_payload)
        logger.info(
            "Seed cargado de %s — zonas=%d dispositivos=%d",
            seed_path, len(state.zonas), len(state.dispositivos),
        )

    # Compartido con routes vía app.state
    app.state.settings = settings
    app.state.state = state
    app.state.client = client

    # Background tasks. Los loops de polling al backend principal se saltan
    # si MOCK_DISABLE_BACKEND_POLL=true (Fase 6 standalone) o si no hay
    # backend a mano. MQTT loop se prende con MOCK_MQTT_ENABLED.
    tasks: list[asyncio.Task] = []
    if not settings.MOCK_DISABLE_BACKEND_POLL:
        tasks.append(asyncio.create_task(
            config_poll_loop(state, client, settings), name="config-poll",
        ))
        tasks.append(asyncio.create_task(
            heartbeat_loop(client, settings), name="heartbeat",
        ))
        if settings.MOCK_SEND_TELEMETRY:
            tasks.append(asyncio.create_task(
                telemetry_loop(state, client, settings), name="telemetry",
            ))
    if settings.MOCK_MQTT_ENABLED:
        tasks.append(asyncio.create_task(
            mqtt_loop(state, settings), name="mqtt",
        ))
    app.state.background_tasks = tasks

    try:
        yield
    finally:
        # Shutdown
        logger.info("Mock ESP32 deteniendo — cancelando %d tasks", len(tasks))
        for task in tasks:
            task.cancel()
        # Esperar a que cada task acepte CancelledError. return_exceptions=True
        # para que una task que falle no aborte la limpieza de las otras.
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for task, result in zip(tasks, results):
            if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                logger.error(
                    "Task %s terminó con excepción: %s", task.get_name(), result,
                )
        await client.aclose()
        logger.info("Mock ESP32 detenido limpiamente")


app = FastAPI(
    title="Mi Hogar — Mock ESP32 Master",
    description=(
        "Simula al ESP32 Master para desarrollo y testing del modo offline. "
        "NO usar en producción."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_routes.router)
app.include_router(mock_routes.router)
