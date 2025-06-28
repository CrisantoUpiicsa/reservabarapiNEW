# app/database.py
import os
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker # Importar para async
from sqlalchemy.sql import func # Para func.now()

from .config import settings

# --- Configuración de la conexión a la base de datos ---

# Define la ruta al certificado SSL raíz dentro del contenedor de Azure App Service.
# 'HOME' es una variable de entorno que apunta a '/home' en App Service.
# Tu aplicación se despliega en '/home/site/wwwroot'.
# El certificado debe estar en 'site/wwwroot/certs/DigiCertGlobalRootG2.crt.pem'.
# Usamos os.environ.get('HOME', '/app') como fallback seguro, aunque 'HOME' debería estar presente.
CERT_PATH = os.path.join(os.environ.get('HOME', '/app'), 'site', 'wwwroot', 'certs', 'DigiCertGlobalRootG2.crt.pem')

# Configuración de los argumentos de conexión.
connect_args = {}

# Verificar si el archivo del certificado existe antes de intentar usarlo.
# Esto es crucial para evitar errores si el archivo no se despliega correctamente.
if os.path.exists(CERT_PATH):
    connect_args["ssl"] = CERT_PATH
    connect_args["sslmode"] = "require" # asyncpg pide que sslmode esté presente con un valor válido
    print(f"DEBUG: Certificado SSL encontrado en: {CERT_PATH}. SSL configurado como 'require'.")
else:
    # Si el certificado no se encuentra, aún intentamos con sslmode=require.
    # Esto puede funcionar si el entorno de Azure maneja el SSL de forma transparente
    # o si el certificado ya está en el sistema operativo del contenedor.
    connect_args["sslmode"] = "require"
    print(f"ADVERTENCIA: Certificado SSL NO encontrado en: {CERT_PATH}. Se intentará conectar con sslmode='require'.")


# Asegúrate de que settings.DATABASE_URL no contenga ningún parámetro sslmode o ssl.
# Tu confirmación de que DATABASE_URL en Azure es limpia es excelente:
# "postgresql+asyncpg://adminuser:CrisantoUpíicsa2021@reservabar-postgres-server.postgres.database.azure.com:5432/postgres"

# Motor de base de datos asíncrono
# Se pasan los argumentos de conexión, incluyendo la configuración SSL/TLS.
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True, # Útil para ver las queries de SQLAlchemy en la consola
    connect_args=connect_args, # Pasa los argumentos de conexión SSL aquí
    future=True # Usar las API de SQLAlchemy más recientes
)

# SessionLocal asíncrono
AsyncSessionLocal = async_sessionmaker( # Cambiado de sessionmaker a async_sessionmaker
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession, # Usar AsyncSession
    expire_on_commit=False # Para no expirar objetos después del commit
)

Base = declarative_base()

# Dependencia para obtener una sesión de base de datos asíncrona
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Función para crear las tablas
# Esta función ahora es asíncrona y usa async_engine
async def create_db_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("DEBUG: Tablas de la base de datos creadas/verificadas.")

# --- Modelos ORM (SQLAlchemy) ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    role = Column(String, default="client", nullable=False) # 'client' o 'admin'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    reservations = relationship("Reservation", back_populates="owner")

class Table(Base):
    __tablename__ = "tables"
    id = Column(Integer, primary_key=True, index=True)
    table_number = Column(String, unique=True, index=True, nullable=False)
    capacity = Column(Integer, nullable=False)
    is_available = Column(Boolean, default=True)
    location = Column(String, nullable=True)
    reservations = relationship("Reservation", back_populates="table_obj")

class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    reservation_time = Column(DateTime(timezone=True), nullable=False)
    num_guests = Column(Integer, nullable=False)
    status = Column(String, default="pending", nullable=False)
    special_requests = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    owner = relationship("User", back_populates="reservations")
    table_obj = relationship("Table", back_populates="reservations")

class Promotion(Base):
    __tablename__ = "promotions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    discount_percentage = Column(Integer, nullable=True)
    code = Column(String, unique=True, nullable=True)