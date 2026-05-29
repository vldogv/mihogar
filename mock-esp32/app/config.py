"""
Settings con pydantic-settings.

Lee .env del CWD (cuando se corre standalone con uvicorn desde mock-esp32/)
y variables de entorno del proceso (docker compose las pasa directo).
Las env vars tienen precedencia sobre el .env.

MOCK_CASA_ID es requerida: si no viene, la instanciación falla con
ValidationError al arranque del lifespan. Fail fast.
"""
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # URL del backend FastAPI principal.
    #   Standalone: http://localhost:8000
    #   Docker compose: http://server:8000 (red interna del compose)
    BACKEND_URL: str = "http://localhost:8000"

    # UUID de una casa real (X-Device-Token = casa.id). Requerida.
    MOCK_CASA_ID: str

    # Frecuencias de los background loops contra el backend principal.
    CONFIG_POLL_SECONDS: int = 15
    HEARTBEAT_SECONDS: int = 30

    # Si está, los loops de polling al backend (config/heartbeat/telemetry) NO
    # arrancan. Se asume modo Fase 6: el mock corre standalone contra un broker
    # MQTT, populado por seed file. Usalo cuando no quieras levantar el server
    # principal para probar el pi-hub.
    MOCK_DISABLE_BACKEND_POLL: bool = False

    # Path a un JSON seed con state inicial (zonas, dispositivos, info).
    # Si está, se carga al startup ANTES de cualquier loop. Estructura:
    # ver mock-esp32/app/fixtures/seed_state.json.
    MOCK_SEED_FILE: Optional[str] = None

    # Telemetría dummy random. Off por default — solo prender cuando
    # quieras ver el dashboard con data viva.
    MOCK_SEND_TELEMETRY: bool = False
    TELEMETRY_SECONDS: int = 60

    # ── MQTT (Fase 6) ─────────────────────────────────────────
    # Si MOCK_MQTT_ENABLED=true, arranca el mqtt_loop que conecta al broker,
    # publica state/info retained, suscribe a cmd/# y responde acks.
    MOCK_MQTT_ENABLED: bool = False
    MQTT_BROKER_URL: str = "mqtt://localhost:1883"

    # Logging stdlib
    LOG_LEVEL: str = "INFO"

    # Timeouts HTTP hacia el backend
    HTTP_TIMEOUT_SECONDS: float = 10.0
