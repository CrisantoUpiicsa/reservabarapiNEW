# app/crud/user.py
from typing import List, Optional, Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status, Depends
from jose import JWTError
from fastapi.security import OAuth2PasswordBearer # Importar directamente aquí

from ..models import user as user_models
from ..schemas import user as user_schemas
from ..auth import security
from ..database import get_db # Importar get_db para la dependencia de la sesión

# --- Definición de OAuth2 scheme (Debe ir aquí, a nivel global del módulo) ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")

# --- Operaciones de Lectura (GET) ---

async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(user_models.User).filter(user_models.User.id == user_id))
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(user_models.User).filter(user_models.User.email == email))
    return result.scalars().first()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(user_models.User).offset(skip).limit(limit))
    return result.scalars().all()

# --- Operaciones de Creación (POST) ---

async def create_user(db: AsyncSession, user: user_schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = user_models.User(
        email=user.email,
        hashed_password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_active=True
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# --- Autenticación ---

async def authenticate_user(db: AsyncSession, email: str, password: str):
    user = await get_user_by_email(db, email=email)
    if not user:
        return False
    if not security.verify_password(password, user.hashed_password):
        return False
    return user

# Esta función ahora recibirá la sesión 'db' como una dependencia también
async def get_current_user(db: AsyncSession, token: str):
    token_data = security.decode_access_token(token)
    user = await get_user_by_email(db, email=token_data.email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    return user

# get_current_active_user es una dependencia para proteger rutas
async def get_current_active_user(
    token: Annotated[str, Depends(oauth2_scheme)], # token viene del header Authorization
    db: Annotated[AsyncSession, Depends(get_db)] # db viene de la dependencia de la DB
):
    user = await get_current_user(db, token) # Pasar db a get_current_user
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")
    return user

# --- Operaciones de Actualización (PUT/PATCH) ---

async def update_user(db: AsyncSession, user_id: int, user_update: user_schemas.UserUpdate):
    db_user = await get_user(db, user_id)
    if not db_user:
        return None

    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# --- Operaciones de Eliminación (DELETE) ---

async def delete_user(db: AsyncSession, user_id: int):
    db_user = await get_user(db, user_id)
    if not db_user:
        return False
    await db.delete(db_user)
    await db.commit()
    return True