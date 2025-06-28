# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .routers import users, reservations, tables, promotions
from .database import create_db_tables, async_engine, get_db # Importar async_engine y get_db
from .config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=settings.PROJECT_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Eventos de la aplicación para conectar y desconectar la base de datos
@app.on_event("startup")
async def startup_event():
    print("Iniciando la aplicación y conectando la base de datos...")
    # create_db_tables() # Descomentar solo para la primera ejecución de desarrollo si no usas migraciones de create
    print("Base de datos lista para conexiones.")

@app.on_event("shutdown")
async def shutdown_event():
    print("Cerrando la aplicación y desconectando de la base de datos...")
    await async_engine.dispose() # Cierra las conexiones del pool
    print("Base de datos desconectada.")

# Inclusión de Routers
app.include_router(users.router)
app.include_router(reservations.router)
app.include_router(tables.router)
app.include_router(promotions.router)

# Manejador de errores global para HTTPException
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Manejador de errores para validación de solicitudes (Pydantic)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )

# Ruta raíz para verificar que la API está funcionando
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Reservation API"}