"""
GET /health  — liveness mínimo, no requiere ESP32 vivo.
GET /info    — discovery: devuelve lo último que el ESP32 publicó en
                mihogar/<casa>/info. Si todavía no llegó nada, devuelve
                un shape básico con casa_id y capabilities vacías.
"""
from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> dict:
    settings = request.app.state.settings
    state = request.app.state.last_known
    esp32_online = await state.get_esp32_online()
    return {
        "status": "ok",
        "casa_id": settings.CASA_ID,
        "esp32_online": esp32_online,
    }


@router.get("/info")
async def info(request: Request) -> dict:
    settings = request.app.state.settings
    state = request.app.state.last_known
    info_payload = await state.get_info()
    if info_payload is None:
        # No llegó retained todavía. Devolvemos un shape mínimo válido.
        return {
            "device_id": "unknown",
            "casa_id": settings.CASA_ID,
            "firmware_version": "unknown",
            "capabilities": [],
        }
    # Aseguramos que casa_id del payload coincide con el configurado del hub.
    return {**info_payload, "casa_id": settings.CASA_ID}
