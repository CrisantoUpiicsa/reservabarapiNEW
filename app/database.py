# app/database.py
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession # Importar para async
from sqlalchemy.sql import func # Para func.now()

from .config import settings

# Configuración de la URL de la base de datos desde settings
# Para SQLite asíncrono: DATABASE_URL="sqlite+aiosqlite:///./sql_app.db"
# (Este valor debe estar en tu .env o en las variables de entorno de Replit)

# Motor de base de datos asíncrono
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True # Útil para ver las queries de SQLAlchemy en la consola
)

# SessionLocal asíncrono
AsyncSessionLocal = sessionmaker(
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