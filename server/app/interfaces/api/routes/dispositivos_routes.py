from fastapi import APIRouter, Depends, HTTPException
from app.core.security import require_admin, TokenData
from app.core.dependencies import get_dispositivo_repo, get_zona_repo, get_casa_repo
from app.domain.repositories.interfaces import (
    DispositivoRepository, ZonaRepository, CasaRepository,
)
from app.domain.entities.models import Dispositivo, TipoDispositivo
from app.interfaces.schemas.dtos import (
    DispositivoResponse, DispositivoCreateRequest, WifiConfigRequest, MessageResponse,
)

router = APIRouter(tags=["Equipos y Dispositivos"])


@router.get("/casas/{casa_id}/dispositivos", response_model=list[DispositivoResponse])
async def get_dispositivos(
    casa_id: str,
    current_user: TokenData = Depends(require_admin),
    disp_repo: DispositivoRepository = Depends(get_dispositivo_repo),
    zona_repo: ZonaRepository = Depends(get_zona_repo),
):
    dispositivos = await disp_repo.get_by_casa(casa_id)
    zonas = await zona_repo.get_by_casa(casa_id)
    zona_map = {z.id: z.nombre for z in zonas}
    return [
        DispositivoResponse(
            id=d.id, zona_id=d.zona_id, zona_nombre=zona_map.get(d.zona_id),
            tipo=str(d.tipo), nombre=d.nombre, mac_address=d.mac_address,
            ip_local=d.ip_local, firmware_version=d.firmware_version,
            estado=str(d.estado),
        )
        for d in dispositivos
    ]


@router.post("/casas/{casa_id}/dispositivos", response_model=DispositivoResponse)
async def create_dispositivo(
    casa_id: str,
    body: DispositivoCreateRequest,
    current_user: TokenData = Depends(require_admin),
    disp_repo: DispositivoRepository = Depends(get_dispositivo_repo),
    zona_repo: ZonaRepository = Depends(get_zona_repo),
):
    zona = await zona_repo.get_by_id(body.zona_id)
    if not zona:
        raise HTTPException(status_code=404, detail="Zona no encontrada")

    try:
        tipo = TipoDispositivo(body.tipo)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Tipo inválido: {body.tipo}")

    dispositivo = Dispositivo(
        zona_id=body.zona_id, casa_id=casa_id, tipo=tipo,
        nombre=body.nombre, mac_address=body.mac_address, ip_local=body.ip_local,
    )
    created = await disp_repo.create(dispositivo)
    return DispositivoResponse(
        id=created.id, zona_id=created.zona_id, zona_nombre=zona.nombre,
        tipo=createstr(d.tipo), nombre=created.nombre,
        mac_address=created.mac_address, ip_local=created.ip_local,
        firmware_version=created.firmware_version, estado=createstr(d.estado),
    )


@router.delete("/dispositivos/{dispositivo_id}", response_model=MessageResponse)
async def delete_dispositivo(
    dispositivo_id: str,
    current_user: TokenData = Depends(require_admin),
    disp_repo: DispositivoRepository = Depends(get_dispositivo_repo),
):
    ok = await disp_repo.delete(dispositivo_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return MessageResponse(message="Dispositivo eliminado")


@router.post("/casas/{casa_id}/wifi-config", response_model=MessageResponse)
async def save_wifi_config(
    casa_id: str,
    body: WifiConfigRequest,
    current_user: TokenData = Depends(require_admin),
    casa_repo: CasaRepository = Depends(get_casa_repo),
):
    casa = await casa_repo.get_by_id(casa_id)
    if not casa:
        raise HTTPException(status_code=404, detail="Casa no encontrada")

    casa.wifi_ssid = body.wifi_ssid
    casa.wifi_password_enc = body.wifi_password  # TODO: encrypt in production
    if body.nombre_instalacion:
        casa.nombre_instalacion = body.nombre_instalacion
    if body.zona_horaria:
        casa.zona_horaria = body.zona_horaria
    if body.email_alertas:
        casa.email_alertas = body.email_alertas

    await casa_repo.update(casa)
    return MessageResponse(message="Configuración WiFi guardada")
