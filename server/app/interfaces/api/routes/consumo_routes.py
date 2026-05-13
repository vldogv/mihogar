from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.security import require_admin_or_encargado, require_admin, get_current_user, TokenData
from app.core.dependencies import get_consumo_repo, get_alerta_repo, get_zona_repo, get_casa_repo
from app.domain.repositories.interfaces import (
    ConsumoRepository, AlertaRepository, ZonaRepository, CasaRepository,
)
from app.interfaces.schemas.dtos import (
    ConsumoResumenResponse, ConsumoDiarioDTO, HorasPicoDTO,
    ConsumoBimestralDTO, AlertaResponse, MessageResponse,
)

router = APIRouter(tags=["Consumo y Reportes"])


@router.get("/casas/{casa_id}/consumo/resumen", response_model=ConsumoResumenResponse)
async def get_consumo_resumen(
    casa_id: str,
    current_user: TokenData = Depends(require_admin_or_encargado),
    consumo_repo: ConsumoRepository = Depends(get_consumo_repo),
    casa_repo: CasaRepository = Depends(get_casa_repo),
):
    casa = await casa_repo.get_by_id(casa_id)
    if not casa:
        raise HTTPException(status_code=404, detail="Casa no encontrada")
    resumen = await consumo_repo.get_resumen(casa_id)
    resumen["corte_cfe_dia"] = casa.corte_cfe_dia
    return ConsumoResumenResponse(**resumen)


@router.get("/casas/{casa_id}/consumo/diario", response_model=list[ConsumoDiarioDTO])
async def get_consumo_diario(
    casa_id: str,
    desde: str = Query(..., description="YYYY-MM-DD"),
    hasta: str = Query(..., description="YYYY-MM-DD"),
    current_user: TokenData = Depends(require_admin_or_encargado),
    consumo_repo: ConsumoRepository = Depends(get_consumo_repo),
    zona_repo: ZonaRepository = Depends(get_zona_repo),
):
    datos = await consumo_repo.get_diario(casa_id, desde, hasta)
    zonas = await zona_repo.get_by_casa(casa_id)
    zona_map = {z.id: z.nombre for z in zonas}
    return [
        ConsumoDiarioDTO(
            zona_id=d.zona_id, zona_nombre=zona_map.get(d.zona_id),
            fecha=d.fecha.isoformat() if d.fecha else "",
            kwh_total=d.kwh_total, horas_encendido=d.horas_encendido,
        )
        for d in datos
    ]


@router.get("/casas/{casa_id}/consumo/horas-pico", response_model=list[HorasPicoDTO])
async def get_horas_pico(
    casa_id: str,
    current_user: TokenData = Depends(require_admin_or_encargado),
    consumo_repo: ConsumoRepository = Depends(get_consumo_repo),
    zona_repo: ZonaRepository = Depends(get_zona_repo),
):
    datos = await consumo_repo.get_horas_pico(casa_id)
    zonas = await zona_repo.get_by_casa(casa_id)
    zona_map = {z.id: z.nombre for z in zonas}
    return [
        HorasPicoDTO(
            zona_id=d.zona_id, zona_nombre=zona_map.get(d.zona_id),
            hora=d.hora, dia_semana=d.dia_semana,
            minutos_promedio=d.minutos_promedio,
        )
        for d in datos
    ]


@router.get("/casas/{casa_id}/consumo/bimestral", response_model=list[ConsumoBimestralDTO])
async def get_consumo_bimestral(
    casa_id: str,
    current_user: TokenData = Depends(require_admin_or_encargado),
    consumo_repo: ConsumoRepository = Depends(get_consumo_repo),
):
    datos = await consumo_repo.get_bimestral(casa_id)
    return [
        ConsumoBimestralDTO(
            bimestre=d.bimestre, anio=d.anio, kwh_total=d.kwh_total,
            costo_estimado=d.costo_estimado, horas_uso_dia=d.horas_uso_dia,
        )
        for d in datos
    ]


@router.get("/casas/{casa_id}/alertas", response_model=list[AlertaResponse])
async def get_alertas(
    casa_id: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(require_admin_or_encargado),
    alerta_repo: AlertaRepository = Depends(get_alerta_repo),
):
    alertas = await alerta_repo.get_by_casa(casa_id, limit)
    return [
        AlertaResponse(
            id=a.id, tipo=str(a.tipo), severidad=str(a.severidad),
            titulo=a.titulo, mensaje=a.mensaje, leida=a.leida,
            created_at=a.created_at.isoformat() if a.created_at else None,
        )
        for a in alertas
    ]


@router.put("/alertas/{alerta_id}/leer", response_model=MessageResponse)
async def mark_alerta_read(
    alerta_id: str,
    current_user: TokenData = Depends(require_admin_or_encargado),
    alerta_repo: AlertaRepository = Depends(get_alerta_repo),
):
    ok = await alerta_repo.mark_as_read(alerta_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return MessageResponse(message="Alerta marcada como leída")


@router.post("/casas/{casa_id}/consumo/cerrar-bimestre", response_model=MessageResponse)
async def cerrar_bimestre(
    casa_id: str,
    current_user: TokenData = Depends(require_admin),
    consumo_repo: ConsumoRepository = Depends(get_consumo_repo),
    casa_repo: CasaRepository = Depends(get_casa_repo),
):
    """
    Cierra el bimestre actual: suma consumo_diario y crea registro en consumo_bimestral.
    Se puede llamar manualmente o por un cron.
    """
    from datetime import date, timedelta
    from app.infrastructure.persistence.postgres.models import ConsumoBimestralModel
    from sqlalchemy import select, func
    
    casa = await casa_repo.get_by_id(casa_id)
    if not casa:
        raise HTTPException(status_code=404, detail="Casa no encontrada")
    
    hoy = date.today()
    bimestre_actual = (hoy.month - 1) // 2 + 1
    anio = hoy.year
    
    # Calcular fecha inicio del bimestre (2 meses atrás desde el corte)
    corte_dia = casa.corte_cfe_dia or 15
    mes_inicio = ((bimestre_actual - 1) * 2) + 1
    fecha_inicio = date(anio, mes_inicio, corte_dia)
    fecha_fin = hoy
    
    # Sumar consumo diario del periodo
    db = consumo_repo.db
    result = await db.execute(
        select(
            func.coalesce(func.sum(ConsumoDiarioModel.kwh_total), 0),
            func.coalesce(func.avg(ConsumoDiarioModel.horas_encendido), 0),
        ).where(
            ConsumoDiarioModel.casa_id == casa_id,
            ConsumoDiarioModel.fecha >= fecha_inicio,
            ConsumoDiarioModel.fecha <= fecha_fin,
        )
    )
    row = result.one()
    kwh_total = float(row[0])
    horas_promedio = float(row[1])
    
    # Estimar costo (tarifa CFE simplificada)
    costo = kwh_total * 3.6  # ~$3.6 MXN por kWh promedio
    
    # Upsert en consumo_bimestral
    existing = await db.execute(
        select(ConsumoBimestralModel).where(
            ConsumoBimestralModel.casa_id == casa_id,
            ConsumoBimestralModel.bimestre == bimestre_actual,
            ConsumoBimestralModel.anio == anio,
        )
    )
    bim = existing.scalar_one_or_none()
    
    if bim:
        bim.kwh_total = kwh_total
        bim.costo_estimado = costo
        bim.horas_uso_dia = horas_promedio
    else:
        nuevo = ConsumoBimestralModel(
            casa_id=casa_id,
            bimestre=bimestre_actual,
            anio=anio,
            kwh_total=kwh_total,
            costo_estimado=costo,
            horas_uso_dia=horas_promedio,
        )
        db.add(nuevo)
    
    await db.flush()
    return MessageResponse(message=f"Bimestre {bimestre_actual}/{anio} cerrado: {kwh_total:.1f} kWh, ${costo:.0f} MXN")
