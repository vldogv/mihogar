from datetime import time
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import require_admin_or_encargado, get_current_user, TokenData
from app.core.dependencies import (
    get_temporizador_repo, get_modo_nocturno_repo,
    get_zona_nocturna_repo, get_zona_repo,
)
from app.domain.repositories.interfaces import (
    TemporizadorRepository, ModoNocturnoRepository,
    ZonaNocturnaRepository, ZonaRepository,
)
from app.domain.entities.models import Temporizador, ModoNocturno, ZonaNocturna, TipoTemporizador
from app.interfaces.schemas.dtos import (
    TemporizadorResponse, TemporizadorCreateRequest, TemporizadorUpdateRequest,
    ModoNocturnoResponse, ModoNocturnoUpdateRequest, ZonaNocturnaDTO, MessageResponse,
)

router = APIRouter(tags=["Horarios y Temporizadores"])


def _parse_time(s: str) -> time:
    parts = s.replace(" ", "").split(":")
    return time(int(parts[0]), int(parts[1]))


def _temp_to_response(t: Temporizador, zona_nombre: str = None) -> TemporizadorResponse:
    return TemporizadorResponse(
        id=t.id, zona_id=t.zona_id, zona_nombre=zona_nombre,
        tipo=str(t.tipo), hora_inicio=t.hora_inicio.strftime("%H:%M"),
        hora_fin=t.hora_fin.strftime("%H:%M"),
        dias={
            "lunes": t.lunes, "martes": t.martes, "miercoles": t.miercoles,
            "jueves": t.jueves, "viernes": t.viernes, "sabado": t.sabado, "domingo": t.domingo,
        },
        solo_si_oscuro=t.solo_si_oscuro, habilitado=t.habilitado,
    )


# ── Temporizadores ───────────────────────────────────────────

@router.get("/casas/{casa_id}/temporizadores", response_model=list[TemporizadorResponse])
async def get_temporizadores(
    casa_id: str,
    current_user: TokenData = Depends(get_current_user),
    temp_repo: TemporizadorRepository = Depends(get_temporizador_repo),
    zona_repo: ZonaRepository = Depends(get_zona_repo),
):
    temps = await temp_repo.get_by_casa(casa_id)
    zonas = await zona_repo.get_by_casa(casa_id)
    zona_map = {z.id: z.nombre for z in zonas}
    return [_temp_to_response(t, zona_map.get(t.zona_id)) for t in temps]


@router.post("/casas/{casa_id}/temporizadores", response_model=TemporizadorResponse)
async def create_temporizador(
    casa_id: str,
    body: TemporizadorCreateRequest,
    current_user: TokenData = Depends(get_current_user),
    temp_repo: TemporizadorRepository = Depends(get_temporizador_repo),
    zona_repo: ZonaRepository = Depends(get_zona_repo),
):
    zona = await zona_repo.get_by_id(body.zona_id)
    if not zona:
        raise HTTPException(status_code=404, detail="Zona no encontrada")

    temp = Temporizador(
        zona_id=body.zona_id, casa_id=casa_id,
        tipo=TipoTemporizador(body.tipo),
        hora_inicio=_parse_time(body.hora_inicio), hora_fin=_parse_time(body.hora_fin),
        lunes=body.lunes, martes=body.martes, miercoles=body.miercoles,
        jueves=body.jueves, viernes=body.viernes, sabado=body.sabado,
        domingo=body.domingo, solo_si_oscuro=body.solo_si_oscuro,
    )
    created = await temp_repo.create(temp)
    return _temp_to_response(created, zona.nombre)


@router.put("/temporizadores/{temporizador_id}", response_model=TemporizadorResponse)
async def update_temporizador(
    temporizador_id: str,
    body: TemporizadorUpdateRequest,
    current_user: TokenData = Depends(get_current_user),
    temp_repo: TemporizadorRepository = Depends(get_temporizador_repo),
):
    temp = await temp_repo.get_by_id(temporizador_id)
    if not temp:
        raise HTTPException(status_code=404, detail="Temporizador no encontrado")

    if body.hora_inicio is not None:
        temp.hora_inicio = _parse_time(body.hora_inicio)
    if body.hora_fin is not None:
        temp.hora_fin = _parse_time(body.hora_fin)
    for field in ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo", "solo_si_oscuro", "habilitado"]:
        val = getattr(body, field, None)
        if val is not None:
            setattr(temp, field, val)

    updated = await temp_repo.update(temp)
    return _temp_to_response(updated)


@router.delete("/temporizadores/{temporizador_id}", response_model=MessageResponse)
async def delete_temporizador(
    temporizador_id: str,
    current_user: TokenData = Depends(get_current_user),
    temp_repo: TemporizadorRepository = Depends(get_temporizador_repo),
):
    deleted = await temp_repo.delete(temporizador_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Temporizador no encontrado")
    return MessageResponse(message="Temporizador eliminado")


# ── Modo Nocturno ────────────────────────────────────────────

@router.get("/casas/{casa_id}/modo-nocturno", response_model=ModoNocturnoResponse)
async def get_modo_nocturno(
    casa_id: str,
    current_user: TokenData = Depends(require_admin_or_encargado),
    mn_repo: ModoNocturnoRepository = Depends(get_modo_nocturno_repo),
    zn_repo: ZonaNocturnaRepository = Depends(get_zona_nocturna_repo),
    zona_repo: ZonaRepository = Depends(get_zona_repo),
):
    modo = await mn_repo.get_by_casa(casa_id)
    if not modo:
        return ModoNocturnoResponse(
            habilitado=False, deteccion_inteligente=True,
            hora_inicio="23:00", hora_fin="06:00", zonas=[],
        )

    zonas_n = await zn_repo.get_by_modo(modo.id)
    all_zonas = await zona_repo.get_by_casa(casa_id)
    zona_map = {z.id: z for z in all_zonas}

    return ModoNocturnoResponse(
        habilitado=modo.habilitado,
        deteccion_inteligente=modo.deteccion_inteligente,
        hora_inicio=modo.hora_inicio.strftime("%H:%M") if modo.hora_inicio else "23:00",
        hora_fin=modo.hora_fin.strftime("%H:%M") if modo.hora_fin else "06:00",
        zonas=[
            ZonaNocturnaDTO(
                zona_id=zn.zona_id,
                zona_nombre=zona_map[zn.zona_id].nombre if zn.zona_id in zona_map else None,
                zona_tipo=zona_map[zn.zona_id].tipo.value if zn.zona_id in zona_map else None,
                habilitada=zn.habilitada,
            )
            for zn in zonas_n
        ],
    )


@router.put("/casas/{casa_id}/modo-nocturno", response_model=MessageResponse)
async def update_modo_nocturno(
    casa_id: str,
    body: ModoNocturnoUpdateRequest,
    current_user: TokenData = Depends(require_admin_or_encargado),
    mn_repo: ModoNocturnoRepository = Depends(get_modo_nocturno_repo),
    zn_repo: ZonaNocturnaRepository = Depends(get_zona_nocturna_repo),
):
    modo = await mn_repo.get_by_casa(casa_id)
    if not modo:
        modo = ModoNocturno(casa_id=casa_id)

    if body.habilitado is not None:
        modo.habilitado = body.habilitado
    if body.deteccion_inteligente is not None:
        modo.deteccion_inteligente = body.deteccion_inteligente
    if body.hora_inicio is not None:
        modo.hora_inicio = _parse_time(body.hora_inicio)
    if body.hora_fin is not None:
        modo.hora_fin = _parse_time(body.hora_fin)

    saved = await mn_repo.upsert(modo)

    if body.zonas is not None:
        zona_entities = [
            ZonaNocturna(zona_id=z.zona_id, habilitada=z.habilitada)
            for z in body.zonas
        ]
        await zn_repo.set_zonas(saved.id, zona_entities)

    return MessageResponse(message="Modo nocturno actualizado")
