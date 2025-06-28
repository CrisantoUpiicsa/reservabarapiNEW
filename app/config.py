# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Reserva Bar API"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "API para la gestión de reservas de mesas, usuarios y promociones de un bar."

    DATABASE_URL: str = "postgresql+asyncpg://adminuser:CrisantoUpíicsa2021@reservabar-postgres-server.postgres.database.azure.com:5432/postgres" # Usamos SQLite por defecto para desarrollo local fácil

    SECRET_KEY: str = "supersecretkey" # ¡CAMBIA ESTO EN PRODUCCIÓN! Usa una cadena aleatoria y compleja.
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Configuración para cargar desde un archivo .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()