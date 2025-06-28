# app/database.py
import os
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.sql import func # Para func.now()

from .config import settings

# --- Configuración de la conexión a la base de datos ---

# No necesitamos definir CERT_PATH ni connect_args aquí.
# La configuración SSL (sslmode=require) se maneja directamente en la DATABASE_URL
# según lo que hemos configurado en app/config.py.
# Esto simplifica la configuración y confía en que Azure y asyncpg gestionen la validación CA.

# Motor de base de datos asíncrono
# SQLAlchemy y asyncpg deberían leer sslmode=require directamente de la URL.
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True, # Útil para ver las queries de SQLAlchemy en la consola
    future=True # Usar las API de SQLAlchemy más recientes
)

# SessionLocal asíncrono
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
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