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
