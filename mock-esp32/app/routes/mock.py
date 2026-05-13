"""
Endpoints de testing — sin auth, solo desarrollo local.

POST /mock/toggle/{zona_id} — toggle simple, reenvía al backend con client_timestamp
POST /mock/state/batch      — batch crudo, útil para probar LWW con timestamps mezclados
GET  /mock/state            — dump del estado in-memory
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mock", tags=["mock"])


class ToggleRequest(BaseModel):
    encendida: bool
    client_id: Optional[str] = None
    client_timestamp: Optional[str] = None  # si no viene, el mock usa now()


class StateUpdate(BaseModel):
    zona_id: str
    encendida: Optional[bool] = None
    modo: Optional[str] = None
    client_id: Optional[str] = None
    client_timestamp: Optional[str] = None


class StateBatchRequest(BaseModel):
    updates: list[StateUpdate]


@router.post("/toggle/{zona_id}")
async def mock_toggle(zona_id: str, body: ToggleRequest, request: Request):
    state = request.app.state.state
    client = request.app.state.client

    zona = await state.get_zona(zona_id)
    if zona is None:
        raise HTTPException(
            status_code=404,
            detail=f"Zona {zona_id} no está en el snapshot local del mock",
        )

    client_timestamp = body.client_timestamp or datetime.now(timezone.utc).isoformat()
    update = {
        "zona_id": zona_id,
        "encendida": body.encendida,
        "client_id": body.client_id,
        "client_timestamp": client_timestamp,
    }
    logger.info(
        "mock_toggle zona=%s encendida=%s client_ts=%s",
        zona_id, body.encendida, client_timestamp,
    )

    results = await client.post_state_batch([update])
    if results is None:
        raise HTTPException(status_code=502, detail="Backend no respondió")

    item = results[0] if results else {}
    # Update optimista local si el backend dijo applied
    if item.get("status") == "applied":
        await state.update_local_zona(zona_id, encendida=body.encendida)

    return {"result": item, "local_updated": item.get("status") == "applied"}


@router.post("/state/batch")
async def mock_state_batch(body: StateBatchRequest, request: Request):
    state = request.app.state.state
    client = request.app.state.client

    updates = [u.model_dump() for u in body.updates]
    for u in updates:
        if not u.get("client_timestamp"):
            u["client_timestamp"] = datetime.now(timezone.utc).isoformat()

    results = await client.post_state_batch(updates)
    if results is None:
        raise HTTPException(status_code=502, detail="Backend no respondió")

    # Update optimista por cada applied
    for r in results:
        if r.get("status") == "applied":
            zona_id = r.get("zona_id")
            orig = next((u for u in updates if u["zona_id"] == zona_id), None)
            if orig:
                await state.update_local_zona(
                    zona_id,
                    encendida=orig.get("encendida"),
                    modo=orig.get("modo"),
                )

    return {"results": results}


@router.get("/state")
async def mock_state_dump(request: Request):
    state = request.app.state.state
    async with state.lock:
        return {
            "casa_id": state.casa_id,
            "casa_nombre": state.casa_nombre,
            "last_config_sync_at": state.last_config_sync_at,
            "zonas": state.zonas,
            "temporizadores": state.temporizadores,
            "dispositivos": state.dispositivos,
            "modo_nocturno": state.modo_nocturno,
        }
