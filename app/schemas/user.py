# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Esquemas Base
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "client" # 'client' o 'admin'
    is_active: bool = True

# Esquema para crear un usuario (incluye contraseña)
class UserCreate(UserBase):
    password: str = Field(min_length=8) # Campo para la contraseña en texto plano en la creación

# Esquema para actualizar un usuario (todos los campos opcionales)
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

# Esquema para leer/retornar un usuario (excluye contraseña hasheada)
class User(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Para Pydantic V2

# Esquema para el token de autenticación
class Token(BaseModel):
    access_token: str
    token_type: str

# Esquema para los datos del token (payload)
class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None # Para incluir el rol en el token