"""
GET /state — devuelve el último state que el ESP32 publicó (retained).
Si todavía no llegó nada → 503.
"""
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(tags=["state"])


@router.get("/state")
async def get_state(request: Request) -> dict:
    state = request.app.state.last_known
    payload = await state.get_state()
    if payload is None:
        raise HTTPException(
            status_code=503,
            detail="Hub aún no recibió state del ESP32",
        )
    return payload
