"""
POST /scene/all-on   — encender todo
POST /scene/all-off  — apagar todo
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..mqtt_client import AckTimeout, BrokerUnavailable

router = APIRouter(prefix="/scene", tags=["scene"])


class SceneBody(BaseModel):
    client_id: Optional[str] = None
    client_timestamp: Optional[str] = None


def _ack_to_response(ack: dict) -> dict:
    return {
        "client_id": ack.get("client_id"),
        "status": ack.get("status"),
        "server_timestamp": ack.get("server_timestamp"),
        "zonas_afectadas": ack.get("zonas_afectadas", []),
    }


async def _publish_scene(suffix: str, body: SceneBody, request: Request) -> dict:
    mqtt = request.app.state.mqtt
    try:
        ack = await mqtt.publish_command(
            suffix,
            {
                "client_id": body.client_id,
                "client_timestamp": body.client_timestamp,
            },
        )
    except AckTimeout:
        raise HTTPException(status_code=504, detail="ack timeout") from None
    except BrokerUnavailable:
        raise HTTPException(status_code=503, detail="MQTT broker no disponible") from None
    return _ack_to_response(ack)


@router.post("/all-on")
async def all_on(body: SceneBody, request: Request) -> dict:
    return await _publish_scene("scene/all-on", body, request)


@router.post("/all-off")
async def all_off(body: SceneBody, request: Request) -> dict:
    return await _publish_scene("scene/all-off", body, request)
