"""
Mi Hogar — FastAPI Entrypoint
Sistema de Domótica Inteligente
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import engine, Base

from app.interfaces.api.routes.auth_routes import router as auth_router
from app.interfaces.api.routes.panel_routes import router as panel_router
from app.interfaces.api.routes.horarios_routes import router as horarios_router
from app.interfaces.api.routes.consumo_routes import router as consumo_router
from app.interfaces.api.routes.dispositivos_routes import router as dispositivos_router
from app.interfaces.api.routes.usuarios_routes import router as usuarios_router
from app.interfaces.api.routes.device_sync_routes import router as device_sync_router
from app.interfaces.api.routes.provisioning_routes import router as provisioning_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    if settings.ENV == "development":
        # Actualiza los hashes bcrypt del seed con valores correctos
        from app.core.seeder import seed_dev_data
        try:
            await seed_dev_data()
        except Exception as e:
            print(f"[STARTUP] Seeder warning: {e}")
    yield
    # Shutdown
    await engine.dispose()


settings = get_settings()

app = FastAPI(
    title="Mi Hogar API",
    description="Sistema de Domótica Inteligente — Backend FastAPI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────
app.include_router(auth_router,         prefix="/api")
app.include_router(panel_router,        prefix="/api")
app.include_router(horarios_router,     prefix="/api")
app.include_router(consumo_router,      prefix="/api")
app.include_router(dispositivos_router, prefix="/api")
app.include_router(usuarios_router,     prefix="/api")
app.include_router(device_sync_router, prefix="/api")
app.include_router(provisioning_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "app": "Mi Hogar",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health():
    return {"status": "ok", "env": settings.ENV}
