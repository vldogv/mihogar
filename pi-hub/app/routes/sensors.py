"""
POST /sensors/pir      — S3 reporta detección de movimiento + luz
POST /sensors/camera   — S3 reporta resultado de inferencia de cámara (persona detectada o no)

Lógica de automatización:
  - Modo automatico:   PIR detecta movimiento + luz_ambiente < umbral → encender
  - Modo nocturno:     PIR detecta movimiento + cámara confirma persona → encender
  - Modo manual:       ignorar señales de sensores (usuario controla manualmente)
  - Modo temporizador: ignorar señales de sensores (temporizador controla)

El estado actual de la zona (modo, umbral_oscuridad) se lee del LastKnownState
que el pi-hub mantiene a partir del `state` retained del ESP32.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..mqtt_client import AckTimeout, BrokerUnavailable

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sensors", tags=["sensors"])


class PirBody(BaseModel):
    zona_id: str
    movimiento: bool
    luz_ambiente: Optional[int] = None   # 0-100, None si no hay sensor de luz


class CameraBody(BaseModel):
    zona_id: str
    persona_detectada: bool
    confianza: Optional[float] = None    # 0.0-1.0, de SageMaker


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _get_zona_state(request: Request, zona_id: str) -> Optional[dict]:
    """Lee el estado actual de la zona desde el LastKnownState del pi-hub."""
    last_known = request.app.state.last_known
    state = await last_known.get_state()
    if state is None:
        return None
    for zona in state.get("zonas", []):
        if zona.get("zona_id") == zona_id:
            return zona
    return None


async def _encender_zona(mqtt, zona_id: str) -> dict:
    """Publica comando toggle encendida=True al C5 via MQTT."""
    ack = await mqtt.publish_command(
        f"zones/{zona_id}/toggle",
        {"encendida": True, "client_timestamp": _now_iso()},
    )
    return ack


@router.post("/pir")
async def report_pir(body: PirBody, request: Request) -> dict:
    """S3 reporta detección de movimiento y nivel de luz.

    Decide si encender la zona según su modo actual:
    - automatico: movimiento + luz_ambiente < umbral_oscuridad → encender
    - nocturno:   movimiento solo no es suficiente → esperar confirmación de cámara
    - manual/temporizador: ignorar
    """
    mqtt = request.app.state.mqtt

    if not body.movimiento:
        # Sin movimiento — no hay nada que decidir
        logger.debug("PIR zona=%s: sin movimiento, ignorado", body.zona_id)
        return {"status": "ignored", "reason": "no_motion"}

    zona = await _get_zona_state(request, body.zona_id)
    if zona is None:
        logger.warning("PIR zona=%s: estado desconocido (ESP32 no conectado?)", body.zona_id)
        return {"status": "ignored", "reason": "zona_state_unknown"}

    modo = zona.get("modo", "manual")
    umbral = zona.get("umbral_oscuridad", 40)
    ya_encendida = zona.get("encendida", False)

    if ya_encendida:
        return {"status": "ignored", "reason": "already_on"}

    if modo == "automatico":
        # Encender si hay movimiento y está oscuro (o no hay sensor de luz)
        if body.luz_ambiente is None or body.luz_ambiente < umbral:
            logger.info(
                "PIR zona=%s: movimiento + oscuro (luz=%s umbral=%d) → encendiendo",
                body.zona_id, body.luz_ambiente, umbral,
            )
            try:
                ack = await _encender_zona(mqtt, body.zona_id)
                return {"status": "command_sent", "ack": ack.get("status")}
            except AckTimeout:
                raise HTTPException(status_code=504, detail="ack timeout") from None
            except BrokerUnavailable:
                raise HTTPException(status_code=503, detail="MQTT broker no disponible") from None
        else:
            return {"status": "ignored", "reason": "sufficient_light"}

    elif modo in ("manual", "temporizador"):
        return {"status": "ignored", "reason": f"mode_{modo}"}

    else:
        # Modo nocturno u otro — PIR solo no es suficiente, esperar cámara
        logger.debug(
            "PIR zona=%s modo=%s: movimiento recibido, esperando confirmación de cámara",
            body.zona_id, modo,
        )
        return {"status": "pending_camera", "reason": "nocturno_needs_camera"}


@router.post("/camera")
async def report_camera(body: CameraBody, request: Request) -> dict:
    """S3 reporta resultado de inferencia de cámara (SageMaker).

    En modo nocturno: persona detectada + movimiento previo → encender.
    En otros modos: solo se registra para telemetría, no dispara acción.
    """
    mqtt = request.app.state.mqtt

    zona = await _get_zona_state(request, body.zona_id)
    if zona is None:
        logger.warning("Camera zona=%s: estado desconocido", body.zona_id)
        return {"status": "ignored", "reason": "zona_state_unknown"}

    modo = zona.get("modo", "manual")
    ya_encendida = zona.get("encendida", False)

    logger.info(
        "Camera zona=%s modo=%s persona=%s confianza=%s",
        body.zona_id, modo, body.persona_detectada, body.confianza,
    )

    if ya_encendida:
        return {"status": "ignored", "reason": "already_on"}

    # Solo actúa en modo nocturno con persona confirmada
    if modo not in ("automatico", "manual", "temporizador") and body.persona_detectada:
        logger.info(
            "Camera zona=%s: persona detectada en modo nocturno → encendiendo",
            body.zona_id,
        )
        try:
            ack = await _encender_zona(mqtt, body.zona_id)
            return {"status": "command_sent", "ack": ack.get("status")}
        except AckTimeout:
            raise HTTPException(status_code=504, detail="ack timeout") from None
        except BrokerUnavailable:
            raise HTTPException(status_code=503, detail="MQTT broker no disponible") from None

    return {"status": "ignored", "reason": "no_action_needed"}
