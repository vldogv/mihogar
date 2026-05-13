from app.core.dependencies import get_casa_repo
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user, require_admin_or_encargado, TokenData
from app.core.dependencies import (
    get_zona_repo, get_config_zona_repo, get_temporizador_repo,
    get_dispositivo_repo, get_modo_nocturno_repo, get_zona_nocturna_repo,
)
from app.domain.repositories.interfaces import (
    ZonaRepository, ConfigZonaRepository, TemporizadorRepository,
    DispositivoRepository, ModoNocturnoRepository, ZonaNocturnaRepository,
)
from app.domain.entities.models import ModoZona
from app.interfaces.schemas.dtos import (
    PanelResponse, ZonaConConfigResponse, ZonaResponse, ConfigZonaResponse,
    ToggleZonaRequest, CambiarModoRequest, ConfigZonaUpdateRequest, MessageResponse,
    SnapshotResponse, SnapshotCasaInfo, TemporizadorResponse,
    DispositivoResponse, ModoNocturnoResponse, ZonaNocturnaDTO,
)
from datetime import datetime, timezone
from typing import Optional

router = APIRouter(tags=["Panel y Zonas"])


@router.get("/casas/{casa_id}/panel", response_model=PanelResponse)
async def get_panel(
    casa_id: str,
    current_user: TokenData = Depends(get_current_user),
    zona_repo: ZonaRepository = Depends(get_zona_repo),
    config_repo: ConfigZonaRepository = Depends(get_config_zona_repo),
):
    """Panel de Control — resumen de todas las zonas con su estado."""
    if current_user.casa_id and current_user.casa_id != casa_id:
        raise HTTPException(status_code=403, detail="Sin acceso a esta casa")

    zonas = await zona_repo.get_by_casa(casa_id)
    configs = await config_repo.get_all_by_casa(casa_id)
    config_map = {c.zona_id: c for c in configs}

    items = []
    activas = 0
    for z in zonas:
        cfg = config_map.get(z.id)
        if cfg and cfg.encendida:
            activas += 1
        items.append(ZonaConConfigResponse(
            zona=ZonaResponse(
                id=z.id, nombre=z.nombre, tipo=str(z.tipo),
                icono=z.icono, orden=z.orden,
            ),
            config=ConfigZonaResponse(
                zona_id=z.id, encendida=cfg.encendida if cfg else False,
                modo=str(cfg.modo) if cfg else "automatico",
                umbral_oscuridad=cfg.umbral_oscuridad if cfg else 40,
                auto_encender=cfg.auto_encender if cfg else True,
                tiempo_apagado_auto=cfg.tiempo_apagado_auto if cfg else 60,
                luz_ambiente_actual=cfg.luz_ambiente_actual if cfg else None,
                movimiento_detectado=cfg.movimiento_detectado if cfg else False,
                temperatura_actual=cfg.temperatura_actual if cfg else None,
                updated_at=cfg.updated_at.isoformat() if cfg and cfg.updated_at else None,
            ) if cfg else None,
        ))

    return PanelResponse(zonas_activas=activas, zonas_total=len(zonas), zonas=items)


@router.get("/casas/{casa_id}/snapshot", response_model=SnapshotResponse)
async def get_snapshot(
    casa_id: str,
    current_user: TokenData = Depends(get_current_user),
    casa_repo = Depends(get_casa_repo),
    zona_repo: ZonaRepository = Depends(get_zona_repo),
    config_repo: ConfigZonaRepository = Depends(get_config_zona_repo),
    temporizador_repo: TemporizadorRepository = Depends(get_temporizador_repo),
    dispositivo_repo: DispositivoRepository = Depends(get_dispositivo_repo),
    modo_nocturno_repo: ModoNocturnoRepository = Depends(get_modo_nocturno_repo),
    zona_nocturna_repo: ZonaNocturnaRepository = Depends(get_zona_nocturna_repo),
):
    """
    Snapshot completo del estado de la casa para modo offline (PWA).

    Devuelve toda la información que la PWA necesita para renderizar UI sin
    conexión y reconciliar cambios cuando vuelva online: zonas con config
    (incluyendo updated_at para LWW), temporizadores, dispositivos y modo
    nocturno. `server_timestamp` sirve como ancla temporal.

    Auth: JWT del usuario. Mismo tenant check que el panel.
    """
    # TODO: aplicar tenant check completo para owners — ver auth audit pendiente (Fase 0 post-entrega)
    if current_user.casa_id and current_user.casa_id != casa_id:
        raise HTTPException(status_code=403, detail="Sin acceso a esta casa")

    casa = await casa_repo.get_by_id(casa_id)
    if not casa:
        raise HTTPException(status_code=404, detail="Casa no encontrada")

    # Zonas + config
    zonas = await zona_repo.get_by_casa(casa_id)
    configs = await config_repo.get_all_by_casa(casa_id)
    config_map = {c.zona_id: c for c in configs}
    zona_nombre_map = {z.id: z.nombre for z in zonas}

    zonas_dto: list[ZonaConConfigResponse] = []
    for z in zonas:
        cfg = config_map.get(z.id)
        zonas_dto.append(ZonaConConfigResponse(
            zona=ZonaResponse(
                id=z.id, nombre=z.nombre, tipo=str(z.tipo),
                icono=z.icono, orden=z.orden,
            ),
            config=ConfigZonaResponse(
                zona_id=z.id,
                encendida=cfg.encendida if cfg else False,
                modo=str(cfg.modo) if cfg else "automatico",
                umbral_oscuridad=cfg.umbral_oscuridad if cfg else 40,
                auto_encender=cfg.auto_encender if cfg else True,
                tiempo_apagado_auto=cfg.tiempo_apagado_auto if cfg else 60,
                luz_ambiente_actual=cfg.luz_ambiente_actual if cfg else None,
                movimiento_detectado=cfg.movimiento_detectado if cfg else False,
                temperatura_actual=cfg.temperatura_actual if cfg else None,
                updated_at=cfg.updated_at.isoformat() if cfg and cfg.updated_at else None,
            ) if cfg else None,
        ))

    # Temporizadores
    temporizadores = await temporizador_repo.get_by_casa(casa_id)
    temporizadores_dto = [
        TemporizadorResponse(
            id=t.id,
            zona_id=t.zona_id,
            zona_nombre=zona_nombre_map.get(t.zona_id),
            tipo=str(t.tipo),
            hora_inicio=t.hora_inicio.strftime("%H:%M") if t.hora_inicio else "00:00",
            hora_fin=t.hora_fin.strftime("%H:%M") if t.hora_fin else "00:00",
            dias={
                "lunes": t.lunes, "martes": t.martes, "miercoles": t.miercoles,
                "jueves": t.jueves, "viernes": t.viernes,
                "sabado": t.sabado, "domingo": t.domingo,
            },
            solo_si_oscuro=t.solo_si_oscuro,
            habilitado=t.habilitado,
        )
        for t in temporizadores
    ]

    # Dispositivos
    dispositivos = await dispositivo_repo.get_by_casa(casa_id)
    dispositivos_dto = [
        DispositivoResponse(
            id=d.id,
            zona_id=d.zona_id,
            zona_nombre=zona_nombre_map.get(d.zona_id),
            tipo=str(d.tipo),
            nombre=d.nombre,
            mac_address=d.mac_address,
            ip_local=d.ip_local,
            firmware_version=d.firmware_version,
            estado=str(d.estado),
        )
        for d in dispositivos
    ]

    # Modo nocturno (opcional)
    mn = await modo_nocturno_repo.get_by_casa(casa_id)
    modo_nocturno_dto: Optional[ModoNocturnoResponse] = None
    if mn:
        zonas_nocturnas = await zona_nocturna_repo.get_by_modo(mn.id)
        modo_nocturno_dto = ModoNocturnoResponse(
            habilitado=mn.habilitado,
            deteccion_inteligente=mn.deteccion_inteligente,
            hora_inicio=mn.hora_inicio.strftime("%H:%M") if mn.hora_inicio else "23:00",
            hora_fin=mn.hora_fin.strftime("%H:%M") if mn.hora_fin else "06:00",
            zonas=[
                ZonaNocturnaDTO(
                    zona_id=zn.zona_id,
                    zona_nombre=zona_nombre_map.get(zn.zona_id),
                    zona_tipo=None,  # disponible en zonas[].zona.tipo
                    habilitada=zn.habilitada,
                )
                for zn in zonas_nocturnas
            ],
        )

    return SnapshotResponse(
        server_timestamp=datetime.now(timezone.utc).isoformat(),
        casa=SnapshotCasaInfo(
            id=casa.id, nombre=casa.nombre, zona_horaria=casa.zona_horaria,
        ),
        zonas=zonas_dto,
        temporizadores=temporizadores_dto,
        dispositivos=dispositivos_dto,
        modo_nocturno=modo_nocturno_dto,
    )


@router.get("/casas/{casa_id}/zonas", response_model=list[ZonaResponse])
async def get_zonas(
    casa_id: str,
    current_user: TokenData = Depends(get_current_user),
    zona_repo: ZonaRepository = Depends(get_zona_repo),
):
    zonas = await zona_repo.get_by_casa(casa_id)
    return [
        ZonaResponse(id=z.id, nombre=z.nombre, tipo=str(z.tipo), icono=z.icono, orden=z.orden)
        for z in zonas
    ]


@router.get("/zonas/{zona_id}", response_model=ZonaConConfigResponse)
async def get_zona_detail(
    zona_id: str,
    current_user: TokenData = Depends(get_current_user),
    zona_repo: ZonaRepository = Depends(get_zona_repo),
    config_repo: ConfigZonaRepository = Depends(get_config_zona_repo),
):
    zona = await zona_repo.get_by_id(zona_id)
    if not zona:
        raise HTTPException(status_code=404, detail="Zona no encontrada")
    cfg = await config_repo.get_by_zona(zona_id)
    return ZonaConConfigResponse(
        zona=ZonaResponse(id=zona.id, nombre=zona.nombre, tipo=zona.tipo.value, icono=zona.icono, orden=zona.orden),
        config=ConfigZonaResponse(
            zona_id=zona.id, encendida=cfg.encendida if cfg else False,
            modo=str(cfg.modo) if cfg else "automatico",
            umbral_oscuridad=cfg.umbral_oscuridad if cfg else 40,
            auto_encender=cfg.auto_encender if cfg else True,
            tiempo_apagado_auto=cfg.tiempo_apagado_auto if cfg else 60,
            luz_ambiente_actual=cfg.luz_ambiente_actual if cfg else None,
            movimiento_detectado=cfg.movimiento_detectado if cfg else False,
            temperatura_actual=cfg.temperatura_actual if cfg else None,
            updated_at=cfg.updated_at.isoformat() if cfg and cfg.updated_at else None,
        ) if cfg else None,
    )


@router.put("/zonas/{zona_id}/toggle", response_model=MessageResponse)
async def toggle_zona(
    zona_id: str,
    body: ToggleZonaRequest,
    current_user: TokenData = Depends(get_current_user),
    config_repo: ConfigZonaRepository = Depends(get_config_zona_repo),
):
    cfg = await config_repo.get_by_zona(zona_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="Configuración de zona no encontrada")
    cfg.encendida = body.encendida
    await config_repo.upsert(cfg)
    estado = "encendida" if body.encendida else "apagada"
    return MessageResponse(message=f"Zona {estado}")


@router.put("/zonas/{zona_id}/modo", response_model=MessageResponse)
async def cambiar_modo(
    zona_id: str,
    body: CambiarModoRequest,
    current_user: TokenData = Depends(require_admin_or_encargado),
    config_repo: ConfigZonaRepository = Depends(get_config_zona_repo),
):
    cfg = await config_repo.get_by_zona(zona_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    try:
        cfg.modo = ModoZona(body.modo)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Modo inválido: {body.modo}")
    await config_repo.upsert(cfg)
    return MessageResponse(message=f"Modo cambiado a {body.modo}")


@router.put("/zonas/{zona_id}/config", response_model=MessageResponse)
async def update_config_zona(
    zona_id: str,
    body: ConfigZonaUpdateRequest,
    current_user: TokenData = Depends(require_admin_or_encargado),
    config_repo: ConfigZonaRepository = Depends(get_config_zona_repo),
):
    cfg = await config_repo.get_by_zona(zona_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    if body.umbral_oscuridad is not None:
        cfg.umbral_oscuridad = body.umbral_oscuridad
    if body.auto_encender is not None:
        cfg.auto_encender = body.auto_encender
    if body.tiempo_apagado_auto is not None:
        cfg.tiempo_apagado_auto = body.tiempo_apagado_auto
    await config_repo.upsert(cfg)
    return MessageResponse(message="Configuración actualizada")


@router.post("/casas/{casa_id}/encender-todo", response_model=MessageResponse)
async def encender_todo(
    casa_id: str,
    current_user: TokenData = Depends(get_current_user),
    config_repo: ConfigZonaRepository = Depends(get_config_zona_repo),
):
    configs = await config_repo.get_all_by_casa(casa_id)
    for cfg in configs:
        cfg.encendida = True
        await config_repo.upsert(cfg)
    return MessageResponse(message=f"{len(configs)} zonas encendidas")


@router.post("/casas/{casa_id}/apagar-todo", response_model=MessageResponse)
async def apagar_todo(
    casa_id: str,
    current_user: TokenData = Depends(get_current_user),
    config_repo: ConfigZonaRepository = Depends(get_config_zona_repo),
):
    configs = await config_repo.get_all_by_casa(casa_id)
    for cfg in configs:
        cfg.encendida = False
        await config_repo.upsert(cfg)
    return MessageResponse(message=f"{len(configs)} zonas apagadas")


@router.put("/casas/{casa_id}/config", response_model=MessageResponse)
async def update_casa_config(
    casa_id: str,
    body: dict,
    current_user: TokenData = Depends(get_current_user),
    casa_repo = Depends(get_casa_repo),
):
    """Actualizar config de la casa (corte CFE, etc.)."""
    from app.core.dependencies import get_casa_repo as _gcr
    casa = await casa_repo.get_by_id(casa_id)
    if not casa:
        raise HTTPException(status_code=404, detail="Casa no encontrada")
    if "corte_cfe_dia" in body:
        casa.corte_cfe_dia = body["corte_cfe_dia"]
    await casa_repo.update(casa)
    return MessageResponse(message="Configuración actualizada")
