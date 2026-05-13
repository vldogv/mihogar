"""
Device Provisioning — Flujo de registro de nuevos dispositivos.

Flujo completo:
  1. Usuario en PWA → POST /provisioning/request → crea solicitud pendiente
  2. ESP32 master → GET /provisioning/pending → ve las solicitudes pendientes
  3. ESP32 master descubre el dispositivo en la red local
  4. ESP32 master → POST /provisioning/activate → confirma MAC, IP, firmware
  5. Backend marca dispositivo como "online" y registrado
  
Para Shelly Gen 4 específicamente:
  1. Usuario conecta el Shelly (se enciende en modo AP: ShellyXXXX)
  2. ESP32 master detecta la red AP del Shelly
  3. ESP32 master se conecta al Shelly AP y le manda las credenciales WiFi
  4. Shelly se conecta a la red WiFi del hogar
  5. ESP32 master lo descubre por mDNS/MQTT
  6. ESP32 master → POST /provisioning/activate con la MAC del Shelly
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user, require_admin, TokenData
from app.infrastructure.persistence.postgres.models import (
    CasaModel, ZonaModel, DispositivoModel,
)

router = APIRouter(prefix="/provisioning", tags=["Device Provisioning"])


# ── Auth helpers ─────────────────────────────────────────────

async def get_casa_from_device_token(
    x_device_token: str = Header(..., alias="X-Device-Token"),
    db: AsyncSession = Depends(get_db),
) -> CasaModel:
    result = await db.execute(
        select(CasaModel).where(CasaModel.id == x_device_token, CasaModel.activa == True)
    )
    casa = result.scalar_one_or_none()
    if not casa:
        raise HTTPException(status_code=401, detail="Device token inválido")
    return casa


# ══════════════════════════════════════════════════════════════
# SCHEMAS
# ══════════════════════════════════════════════════════════════

class ProvisioningRequest(BaseModel):
    """El usuario pide agregar un dispositivo desde la PWA."""
    zona_id: str
    tipo: str  # modulo_shelly, sensor_pir, sensor_crepuscular, camara_ip
    nombre: str


class ProvisioningResponse(BaseModel):
    dispositivo_id: str
    estado: str  # pending, provisioning, active, failed
    mensaje: str


class PendingDevice(BaseModel):
    """Lo que el ESP32 master ve como dispositivo pendiente de activar."""
    dispositivo_id: str
    zona_id: str
    zona_nombre: str
    tipo: str
    nombre: str
    created_at: str


class ActivateRequest(BaseModel):
    """El ESP32 master confirma que encontró y configuró el dispositivo."""
    dispositivo_id: str
    mac_address: str
    ip_local: Optional[str] = None
    firmware_version: Optional[str] = None


class ActivateResponse(BaseModel):
    dispositivo_id: str
    estado: str
    mensaje: str


class ShellyProvisionRequest(BaseModel):
    """
    Datos para provisionar un Shelly Gen 4 específicamente.
    El ESP32 master necesita:
    - Las credenciales WiFi para mandarlas al Shelly AP
    - El ID del dispositivo en la BD para activarlo después
    """
    dispositivo_id: str
    wifi_ssid: Optional[str] = None  # si no se manda, usa el de la casa
    wifi_password: Optional[str] = None


class ShellyProvisionResponse(BaseModel):
    dispositivo_id: str
    wifi_ssid: str
    wifi_password: str
    mqtt_broker_ip: Optional[str] = None  # IP del ESP32 master para MQTT
    mensaje: str


class ReplacementRequest(BaseModel):
    """Reemplazar un nodo que falló (mismo tipo, misma zona, nuevo hardware)."""
    dispositivo_id_viejo: str  # el que se va a reemplazar
    mac_address_nuevo: str
    ip_local: Optional[str] = None
    firmware_version: Optional[str] = None


# ══════════════════════════════════════════════════════════════
# 1. USUARIO PIDE AGREGAR DISPOSITIVO (desde PWA)
# ══════════════════════════════════════════════════════════════

@router.post("/request", response_model=ProvisioningResponse)
async def request_provisioning(
    body: ProvisioningRequest,
    current_user: TokenData = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    El admin solicita agregar un nuevo dispositivo a una zona.
    Se crea el registro en estado 'offline' (pendiente de activación).
    El ESP32 master lo verá en GET /pending y lo activará.
    """
    # Validar zona existe
    zona_result = await db.execute(
        select(ZonaModel).where(ZonaModel.id == body.zona_id)
    )
    zona = zona_result.scalar_one_or_none()
    if not zona:
        raise HTTPException(status_code=404, detail="Zona no encontrada")

    # Validar tipo
    tipos_validos = ["modulo_shelly", "sensor_pir", "sensor_crepuscular", "camara_ip"]
    if body.tipo not in tipos_validos:
        raise HTTPException(status_code=400, detail=f"Tipo inválido. Válidos: {tipos_validos}")

    # Crear dispositivo en estado offline (pendiente)
    nuevo = DispositivoModel(
        zona_id=body.zona_id,
        casa_id=str(zona.casa_id),
        tipo=body.tipo,
        nombre=body.nombre,
        estado="offline",  # pendiente hasta que el ESP32 lo active
        configuracion={"provisioning_status": "pending"},
    )
    db.add(nuevo)
    await db.flush()

    return ProvisioningResponse(
        dispositivo_id=str(nuevo.id),
        estado="pending",
        mensaje=f"Dispositivo '{body.nombre}' creado. Esperando activación del ESP32.",
    )


# ══════════════════════════════════════════════════════════════
# 2. ESP32 CONSULTA DISPOSITIVOS PENDIENTES
# ══════════════════════════════════════════════════════════════

@router.get("/pending", response_model=list[PendingDevice])
async def get_pending_devices(
    casa: CasaModel = Depends(get_casa_from_device_token),
    db: AsyncSession = Depends(get_db),
):
    """
    ESP32 master consulta qué dispositivos están pendientes de provisionar.
    Retorna los que están en estado 'offline' sin MAC address (nunca activados).
    """
    result = await db.execute(
        select(DispositivoModel, ZonaModel)
        .join(ZonaModel, DispositivoModel.zona_id == ZonaModel.id)
        .where(
            DispositivoModel.casa_id == casa.id,
            DispositivoModel.activo == True,
            DispositivoModel.mac_address == None,  # nunca activado
            DispositivoModel.estado == "offline",
        )
    )

    return [
        PendingDevice(
            dispositivo_id=str(d.id),
            zona_id=str(d.zona_id),
            zona_nombre=z.nombre,
            tipo=str(d.tipo),
            nombre=d.nombre,
            created_at=d.created_at.isoformat() if d.created_at else "",
        )
        for d, z in result.all()
    ]


# ══════════════════════════════════════════════════════════════
# 3. ESP32 ACTIVA UN DISPOSITIVO
# ══════════════════════════════════════════════════════════════

@router.post("/activate", response_model=ActivateResponse)
async def activate_device(
    body: ActivateRequest,
    casa: CasaModel = Depends(get_casa_from_device_token),
    db: AsyncSession = Depends(get_db),
):
    """
    ESP32 master confirma que descubrió y configuró el dispositivo.
    Actualiza MAC, IP, firmware y cambia estado a 'online'.
    """
    result = await db.execute(
        select(DispositivoModel).where(
            DispositivoModel.id == body.dispositivo_id,
            DispositivoModel.casa_id == casa.id,
        )
    )
    disp = result.scalar_one_or_none()
    if not disp:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

    # Verificar que la MAC no esté ya registrada en otro dispositivo
    if body.mac_address:
        mac_check = await db.execute(
            select(DispositivoModel).where(
                DispositivoModel.mac_address == body.mac_address,
                DispositivoModel.id != body.dispositivo_id,
            )
        )
        if mac_check.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"MAC {body.mac_address} ya registrada en otro dispositivo",
            )

    disp.mac_address = body.mac_address
    disp.ip_local = body.ip_local
    disp.firmware_version = body.firmware_version
    disp.estado = "online"
    disp.ultimo_heartbeat = datetime.now(timezone.utc)
    disp.configuracion = {"provisioning_status": "active"}

    await db.flush()

    return ActivateResponse(
        dispositivo_id=str(disp.id),
        estado="online",
        mensaje=f"Dispositivo activado con MAC {body.mac_address}",
    )


# ══════════════════════════════════════════════════════════════
# 4. DATOS PARA PROVISIONAR SHELLY GEN 4
# ══════════════════════════════════════════════════════════════

@router.post("/shelly-config", response_model=ShellyProvisionResponse)
async def get_shelly_provision_config(
    body: ShellyProvisionRequest,
    casa: CasaModel = Depends(get_casa_from_device_token),
    db: AsyncSession = Depends(get_db),
):
    """
    ESP32 master pide las credenciales WiFi para configurar un Shelly Gen 4.
    
    Flujo Shelly Gen 4:
    1. Shelly nuevo se enciende → crea AP "ShellyPlusXXXX"
    2. ESP32 master detecta la red AP
    3. ESP32 master pide este endpoint para obtener las credenciales
    4. ESP32 se conecta al AP del Shelly (192.168.33.1)
    5. ESP32 manda POST al Shelly con WiFi config + MQTT config
    6. Shelly se reinicia y se conecta a la red WiFi
    7. ESP32 lo descubre y llama POST /activate
    """
    # Verificar dispositivo existe
    result = await db.execute(
        select(DispositivoModel).where(
            DispositivoModel.id == body.dispositivo_id,
            DispositivoModel.casa_id == casa.id,
        )
    )
    disp = result.scalar_one_or_none()
    if not disp:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

    # Usar las credenciales de la casa, o las que mandó el request
    wifi_ssid = body.wifi_ssid or casa.wifi_ssid
    wifi_password = body.wifi_password or casa.wifi_password_enc

    if not wifi_ssid or not wifi_password:
        raise HTTPException(
            status_code=400,
            detail="No hay credenciales WiFi configuradas. Configura WiFi primero.",
        )

    # Marcar como "provisionando"
    disp.estado = "actualizando"
    disp.configuracion = {"provisioning_status": "provisioning"}
    await db.flush()

    return ShellyProvisionResponse(
        dispositivo_id=str(disp.id),
        wifi_ssid=wifi_ssid,
        wifi_password=wifi_password,
        mqtt_broker_ip=None,  # el ESP32 master ya sabe su propia IP
        mensaje="Credenciales listas para enviar al Shelly",
    )


# ══════════════════════════════════════════════════════════════
# 5. REEMPLAZAR NODO DAÑADO
# ══════════════════════════════════════════════════════════════

@router.post("/replace", response_model=ActivateResponse)
async def replace_device(
    body: ReplacementRequest,
    casa: CasaModel = Depends(get_casa_from_device_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Reemplazar un nodo que falló. Mantiene la misma zona, tipo y nombre,
    pero actualiza la MAC y pone el dispositivo online.
    El usuario reemplaza el módulo físico completo (sensor + ESP32 mini).
    """
    result = await db.execute(
        select(DispositivoModel).where(
            DispositivoModel.id == body.dispositivo_id_viejo,
            DispositivoModel.casa_id == casa.id,
        )
    )
    disp = result.scalar_one_or_none()
    if not disp:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

    # Verificar MAC no duplicada
    if body.mac_address_nuevo:
        mac_check = await db.execute(
            select(DispositivoModel).where(
                DispositivoModel.mac_address == body.mac_address_nuevo,
                DispositivoModel.id != body.dispositivo_id_viejo,
            )
        )
        if mac_check.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="MAC ya registrada en otro dispositivo")

    # Actualizar con el nuevo hardware
    disp.mac_address = body.mac_address_nuevo
    disp.ip_local = body.ip_local
    disp.firmware_version = body.firmware_version
    disp.estado = "online"
    disp.ultimo_heartbeat = datetime.now(timezone.utc)
    disp.configuracion = {"provisioning_status": "replaced", "replaced_at": datetime.now(timezone.utc).isoformat()}

    await db.flush()

    return ActivateResponse(
        dispositivo_id=str(disp.id),
        estado="online",
        mensaje=f"Dispositivo reemplazado con nueva MAC {body.mac_address_nuevo}",
    )
