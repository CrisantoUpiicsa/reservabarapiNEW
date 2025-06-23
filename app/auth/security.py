# app/auth/security.py
from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from jose import JWTError, jwt

# Importar configuración
from ..config import settings
from ..schemas.user import TokenData # Importamos TokenData aquí

# Contexto para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Funciones de Hashing de Contraseñas ---
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
        return pwd_context.hash(password)

# --- Funciones para JWT (JSON Web Tokens) ---
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise JWTError("Invalid token: subject (email) missing") # Un error más específico si email falta
        return TokenData(email=email, role=role)
    except JWTError:    # FastAPI maneja las HTTPException en routers
        raise # Relanza el error para que FastAPI lo maneje si es necesario