"""
Configuración environment-aware.
En desarrollo usa PostgreSQL local.
En producción usa RDS + DynamoDB + IoT Core.
"""

import os


class Settings:
    # Environment
    ENV = os.getenv("ENV", "development")
    DEBUG = ENV == "development"

    # Database (RDS en producción)
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://mihogar_admin:mihogar_pass@localhost:5432/mihogar"
    )

    # JWT Auth
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # AWS - General
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

    # AWS IoT Core
    AWS_IOT_ENDPOINT = os.getenv("AWS_IOT_ENDPOINT", "")  # xxxxx-ats.iot.region.amazonaws.com

    # DynamoDB
    DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "mihogar-sensor-events")
    DYNAMODB_COMMANDS_TABLE = os.getenv("DYNAMODB_COMMANDS_TABLE", "mihogar-device-commands")
    USE_DYNAMODB = os.getenv("USE_DYNAMODB", "false").lower() == "true"

    # S3
    S3_ML_BUCKET = os.getenv("S3_ML_BUCKET", "mihogar-ml-data")
    S3_PWA_BUCKET = os.getenv("S3_PWA_BUCKET", "mihogar-pwa")

    # SageMaker
    SAGEMAKER_PIPELINE = os.getenv("SAGEMAKER_PIPELINE", "mihogar-lighting-optimization")

    # CORS - origins permitidos
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if ENV == "production" else "DEBUG")


settings = Settings()
