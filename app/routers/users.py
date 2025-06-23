# app/routers/users.py
from datetime import timedelta
from typing import List, Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession # Importar AsyncSession
from sqlalchemy import select # Importar select para consultas asíncronas

from ..crud import user as crud_user
from ..schemas import user as user_schemas
from ..database import get_db, create_db_tables # Mantener create_db_tables si lo usas
from ..auth import security

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# Endpoint para crear un nuevo usuario
@router.post("/", response_model=user_schemas.User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: user_schemas.UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    db_user = await crud_user.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")
    return await crud_user.create_user(db=db, user=user)

# Endpoint para obtener el token de acceso (login)
@router.post("/token", response_model=user_schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await crud_user.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Endpoint para obtener un usuario por ID (protegido)
@router.get("/{user_id}", response_model=user_schemas.User)
async def read_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[user_schemas.User, Depends(crud_user.get_current_active_user)]
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para acceder a este usuario"
        )
    db_user = await crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user

# Endpoint para obtener todos los usuarios (solo para administradores)
@router.get("/", response_model=List[user_schemas.User])
async def read_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[user_schemas.User,Depends(crud_user.get_current_active_user)],
    skip: int = 0,
    limit: int = 100):

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden ver todos los usuarios"
        )
    users = await crud_user.get_users(db, skip=skip, limit=limit)
    return users

# Endpoint para actualizar un usuario (protegido)
@router.put("/{user_id}", response_model=user_schemas.User)
async def update_user(
    user_id: int,
    user: user_schemas.UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)], # <-- Tu error apunta a esta línea o similar
    current_user: Annotated[user_schemas.User, Depends(crud_user.get_current_active_user)]
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este usuario"
        )
    db_user = await crud_user.update_user(db, user_id=user_id, user_update=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user

# Endpoint para eliminar un usuario (protegido)
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[user_schemas.User, Depends(crud_user.get_current_active_user)]
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este usuario"
        )
    success = await crud_user.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return

# Endpoint para obtener el usuario actual (protegido)
@router.get("/me/", response_model=user_schemas.User)
async def read_users_me(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[user_schemas.User, Depends(crud_user.get_current_active_user)]
):
    return current_user

# Endpoint para crear las tablas de la base de datos (solo desarrollo)
@router.post("/create-db-tables/", status_code=status.HTTP_200_OK, summary="Crea las tablas de la base de datos (solo para desarrollo/primera ejecución)", response_model=dict)
async def create_db_tables_endpoint(
    current_user: Annotated[user_schemas.User, Depends(crud_user.get_current_active_user)]
):
    """
    **Advertencia:** Este endpoint está diseñado para crear las tablas de la base de datos
    por primera vez durante el desarrollo.
    Debe ser protegido o eliminado en entornos de producción.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden crear las tablas de la base de datos."
        )
    await create_db_tables()
    return {"message": "Tablas de la base de datos creadas exitosamente."}