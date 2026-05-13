"""GET /health — diagnóstico del mock."""
from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> dict:
    state = request.app.state.state
    settings = request.app.state.settings
    async with state.lock:
        return {
            "status": "ok",
            "casa_id": settings.MOCK_CASA_ID,
            "backend_url": settings.BACKEND_URL,
            "last_config_sync_at": state.last_config_sync_at,
            "zonas_count": len(state.zonas),
            "temporizadores_count": len(state.temporizadores),
            "dispositivos_count": len(state.dispositivos),
            "modo_nocturno_habilitado": (state.modo_nocturno or {}).get("habilitado"),
        }
