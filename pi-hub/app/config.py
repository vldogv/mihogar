"""
Settings del Pi-hub.
Lee .env del CWD (standalone) o env vars (docker compose). Las env vars
tienen precedencia. CASA_ID es requerida — fail fast si no viene.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    # UUID de la casa que este hub controla. Requerida.
    CASA_ID: str
    # Broker MQTT al que el hub y el ESP32 se conectan.
    #   Standalone: mqtt://localhost:1883
    #   Docker compose: mqtt://mosquitto:1883
    MQTT_BROKER_URL: str = "mqtt://localhost:1883"
    # Identificador del cliente MQTT del hub (debe ser único en el broker).
    DEVICE_ID: str = "pi-hub"
    # Timeout para esperar el ack del ESP32 después de publicar un comando.
    ACK_TIMEOUT_SECONDS: float = 2.0
    # HTTP server.
    HTTP_PORT: int = 8081
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    # Logging stdlib
    LOG_LEVEL: str = "INFO"

    # ── Puente hacia EC2 (Fase 7 §7) ──────────────────────────
    BACKEND_URL: str = "http://localhost:8000"
    HTTP_TIMEOUT_SECONDS: float = 10.0
    CONFIG_POLL_SECONDS: int = 15
    HEARTBEAT_SECONDS: int = 30
    DRAIN_INTERVAL_SECONDS: int = 10
    EC2_HEALTH_CACHE_SECONDS: int = 30
    DB_PATH: str = "pi_hub_bridge.db"
    # Camino inverso EC2 → ESP32. Contrato de GET /commands ASUMIDO, no
    # confirmado con el backend real — dejar en false hasta validar con Aldo.
    COMMANDS_POLL_ENABLED: bool = False
    COMMANDS_POLL_SECONDS: int = 10
