"""
POST /zones/{zona_id}/toggle  — encender/apagar una zona
POST /zones/{zona_id}/mode    — cambiar el modo de una zona
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..mqtt_client import AckTimeout, BrokerUnavailable

router = APIRouter(prefix="/zones", tags=["zones"])


class ToggleBody(BaseModel):
    encendida: bool
    client_id: Optional[str] = None
    client_timestamp: Optional[str] = None


class ModeBody(BaseModel):
    modo: str
    client_id: Optional[str] = None
    client_timestamp: Optional[str] = None


def _ack_to_response(ack: dict) -> dict:
    """Filtra el req_id (interno) y devuelve la response del contrato HTTP."""
    return {
        "client_id": ack.get("client_id"),
        "zona_id": ack.get("zona_id"),
        "status": ack.get("status"),
        "server_timestamp": ack.get("server_timestamp"),
    }


@router.post("/{zona_id}/toggle")
async def toggle_zone(zona_id: str, body: ToggleBody, request: Request) -> dict:
    mqtt = request.app.state.mqtt
    try:
        ack = await mqtt.publish_command(
            f"zones/{zona_id}/toggle",
            {
                "encendida": body.encendida,
                "client_id": body.client_id,
                "client_timestamp": body.client_timestamp,
            },
        )
    except AckTimeout:
        raise HTTPException(status_code=504, detail="ack timeout") from None
    except BrokerUnavailable:
        raise HTTPException(status_code=503, detail="MQTT broker no disponible") from None
    return _ack_to_response(ack)


@router.post("/{zona_id}/mode")
async def mode_zone(zona_id: str, body: ModeBody, request: Request) -> dict:
    mqtt = request.app.state.mqtt
    try:
        ack = await mqtt.publish_command(
            f"zones/{zona_id}/mode",
            {
                "modo": body.modo,
                "client_id": body.client_id,
                "client_timestamp": body.client_timestamp,
            },
        )
    except AckTimeout:
        raise HTTPException(status_code=504, detail="ack timeout") from None
    except BrokerUnavailable:
        raise HTTPException(status_code=503, detail="MQTT broker no disponible") from None
    return _ack_to_response(ack)
