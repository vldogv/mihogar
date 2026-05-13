"""
Endpoints de sincronización para el ESP32 Master.
El ESP32 se autentica con un device_token (API key por casa).

Flujo:
  1. ESP32 arranca → GET /sync/config → descarga toda la config
  2. ESP32 periódicamente → POST /sync/telemetry → sube lecturas de sensores
  3. ESP32 periódicamente → POST /sync/heartbeat → reporta que está vivo
  4. ESP32 detecta problema → POST /sync/alerts → manda alertas
  5. ESP32 periódicamente → GET /sync/commands → checa si hay comandos pendientes
  6. ESP32 después de SageMaker → GET /sync/ml-profile → descarga perfil aprendido
"""

from datetime import datetime, timezone, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, update as sa_update

from app.core.database import get_db
from app.infrastructure.persistence.postgres.models import (
    CasaModel, ZonaModel, ConfigZonaModel, TemporizadorModel,
    ModoNocturnoModel, ZonaNocturnaModel, DispositivoModel,
    ConsumoDiarioModel, AlertaModel, PerfilSagemakerModel,
)

router = APIRouter(prefix="/device/sync", tags=["Device Sync (ESP32)"])


# ── Autenticación por device token ───────────────────────────
# El ESP32 usa un header: X-Device-Token: <token>
# Por ahora el token es el ID de la casa (en producción sería un JWT o API key)

async def get_casa_from_device_token(
    x_device_token: str = Header(..., alias="X-Device-Token"),
    db: AsyncSession = Depends(get_db),
) -> CasaModel:
    """Valida el device token y retorna la casa."""
    result = await db.execute(
        select(CasaModel).where(CasaModel.id == x_device_token, CasaModel.activa == True)
    )
    casa = result.scalar_one_or_none()
    if not casa:
        raise HTTPException(status_code=401, detail="Device token inválido")
    return casa


# ══════════════════════════════════════════════════════════════
# 1. DESCARGAR CONFIGURACIÓN COMPLETA
# ══════════════════════════════════════════════════════════════
# El ESP32 llama esto al arrancar y periódicamente para sincronizar.
# Recibe TODO lo que necesita para operar offline.

class ZonaConfigSync(BaseModel):
    zona_id: str
    nombre: str
    tipo: str
    orden: int
    encendida: bool
    modo: str  # automatico, manual, temporizador
    umbral_oscuridad: int
    auto_encender: bool
    tiempo_apagado_auto: int  # segundos


class TemporizadorSync(BaseModel):
    id: str
    zona_id: str
    tipo: str
    hora_inicio: str  # HH:MM
    hora_fin: str
    dias: dict  # {lunes: bool, ...}
    solo_si_oscuro: bool
    habilitado: bool


class ModoNocturnoSync(BaseModel):
    habilitado: bool
    deteccion_inteligente: bool
    hora_inicio: str
    hora_fin: str
    zonas_habilitadas: list[str]  # lista de zona_ids


class DispositivoSync(BaseModel):
    id: str
    zona_id: str
    tipo: str
    nombre: str
    mac_address: Optional[str] = None


class MlProfileSync(BaseModel):
    zona_id: str
    umbral_sugerido: Optional[int] = None
    tiempo_apagado_sugerido: Optional[int] = None
    patron_detectado: Optional[str] = None
    confianza: Optional[float] = None


class FullConfigResponse(BaseModel):
    casa_id: str
    casa_nombre: str
    zona_horaria: str
    timestamp: str  # ISO 8601 - para que el ESP32 sepa cuándo se generó
    zonas: list[ZonaConfigSync]
    temporizadores: list[TemporizadorSync]
    modo_nocturno: Optional[ModoNocturnoSync] = None
    dispositivos: list[DispositivoSync]
    ml_profiles: list[MlProfileSync]


@router.get("/config", response_model=FullConfigResponse)
async def download_config(
    casa: CasaModel = Depends(get_casa_from_device_token),
    db: AsyncSession = Depends(get_db),
):
    """
    ESP32 descarga toda la configuración de la casa.
    Incluye zonas, config de sensores, temporizadores, modo nocturno,
    dispositivos registrados y perfiles de SageMaker.
    """
    casa_id = str(casa.id)

    # Zonas + config
    zonas_result = await db.execute(
        select(ZonaModel, ConfigZonaModel)
        .outerjoin(ConfigZonaModel, ZonaModel.id == ConfigZonaModel.zona_id)
        .where(ZonaModel.casa_id == casa.id, ZonaModel.activa == True)
        .order_by(ZonaModel.orden)
    )
    zonas = []
    for zona, config in zonas_result.all():
        zonas.append(ZonaConfigSync(
            zona_id=str(zona.id),
            nombre=zona.nombre,
            tipo=str(zona.tipo),
            orden=zona.orden,
            encendida=config.encendida if config else False,
            modo=str(config.modo) if config else "automatico",
            umbral_oscuridad=config.umbral_oscuridad if config else 40,
            auto_encender=config.auto_encender if config else True,
            tiempo_apagado_auto=config.tiempo_apagado_auto if config else 60,
        ))

    # Temporizadores
    temp_result = await db.execute(
        select(TemporizadorModel).where(TemporizadorModel.casa_id == casa.id)
    )
    temporizadores = []
    for t in temp_result.scalars().all():
        temporizadores.append(TemporizadorSync(
            id=str(t.id),
            zona_id=str(t.zona_id),
            tipo=str(t.tipo),
            hora_inicio=t.hora_inicio.strftime("%H:%M"),
            hora_fin=t.hora_fin.strftime("%H:%M"),
            dias={
                "lunes": t.lunes, "martes": t.martes, "miercoles": t.miercoles,
                "jueves": t.jueves, "viernes": t.viernes,
                "sabado": t.sabado, "domingo": t.domingo,
            },
            solo_si_oscuro=t.solo_si_oscuro,
            habilitado=t.habilitado,
        ))

    # Modo nocturno
    mn_result = await db.execute(
        select(ModoNocturnoModel).where(ModoNocturnoModel.casa_id == casa.id)
    )
    mn = mn_result.scalar_one_or_none()
    modo_nocturno = None
    if mn:
        zn_result = await db.execute(
            select(ZonaNocturnaModel).where(
                ZonaNocturnaModel.modo_nocturno_id == mn.id,
                ZonaNocturnaModel.habilitada == True,
            )
        )
        zonas_nocturnas = [str(zn.zona_id) for zn in zn_result.scalars().all()]
        modo_nocturno = ModoNocturnoSync(
            habilitado=mn.habilitado,
            deteccion_inteligente=mn.deteccion_inteligente,
            hora_inicio=mn.hora_inicio.strftime("%H:%M") if mn.hora_inicio else "23:00",
            hora_fin=mn.hora_fin.strftime("%H:%M") if mn.hora_fin else "06:00",
            zonas_habilitadas=zonas_nocturnas,
        )

    # Dispositivos
    disp_result = await db.execute(
        select(DispositivoModel).where(
            DispositivoModel.casa_id == casa.id,
            DispositivoModel.activo == True,
        )
    )
    dispositivos = [
        DispositivoSync(
            id=str(d.id), zona_id=str(d.zona_id), tipo=str(d.tipo),
            nombre=d.nombre, mac_address=d.mac_address,
        )
        for d in disp_result.scalars().all()
    ]

    # Perfiles ML
    ml_result = await db.execute(
        select(PerfilSagemakerModel).where(PerfilSagemakerModel.casa_id == casa.id)
    )
    ml_profiles = [
        MlProfileSync(
            zona_id=str(p.zona_id),
            umbral_sugerido=p.umbral_oscuridad_sugerido,
            tiempo_apagado_sugerido=p.tiempo_apagado_sugerido,
            patron_detectado=p.patron_detectado,
            confianza=float(p.confianza) if p.confianza else None,
        )
        for p in ml_result.scalars().all()
    ]

    return FullConfigResponse(
        casa_id=casa_id,
        casa_nombre=casa.nombre,
        zona_horaria=casa.zona_horaria,
        timestamp=datetime.now(timezone.utc).isoformat(),
        zonas=zonas,
        temporizadores=temporizadores,
        modo_nocturno=modo_nocturno,
        dispositivos=dispositivos,
        ml_profiles=ml_profiles,
    )


# ══════════════════════════════════════════════════════════════
# 2. SUBIR TELEMETRÍA (Lecturas de sensores)
# ══════════════════════════════════════════════════════════════

class SensorReading(BaseModel):
    zona_id: str
    timestamp: str  # ISO 8601
    luz_ambiente: Optional[int] = None  # 0-100 %
    movimiento: Optional[bool] = None
    temperatura: Optional[float] = None  # °C del módulo
    consumo_watts: Optional[float] = None  # consumo instantáneo
    estado_luz: Optional[str] = None  # "encendida" | "apagada"


class TelemetryBatch(BaseModel):
    lecturas: list[SensorReading]


class TelemetryResponse(BaseModel):
    recibidas: int
    procesadas: int
    errores: int


@router.post("/telemetry", response_model=TelemetryResponse)
async def upload_telemetry(
    batch: TelemetryBatch,
    casa: CasaModel = Depends(get_casa_from_device_token),
    db: AsyncSession = Depends(get_db),
):
    """
    ESP32 sube un batch de lecturas de sensores.
    Actualiza el estado en tiempo real de cada zona (config_zonas)
    y acumula consumo diario.
    """
    procesadas = 0
    errores = 0

    for lectura in batch.lecturas:
        try:
            # Actualizar config_zonas con los valores actuales del sensor
            result = await db.execute(
                select(ConfigZonaModel).where(ConfigZonaModel.zona_id == lectura.zona_id)
            )
            config = result.scalar_one_or_none()

            if config:
                if lectura.luz_ambiente is not None:
                    config.luz_ambiente_actual = lectura.luz_ambiente
                if lectura.movimiento is not None:
                    config.movimiento_detectado = lectura.movimiento
                if lectura.temperatura is not None:
                    config.temperatura_actual = lectura.temperatura
                if lectura.estado_luz is not None:
                    config.encendida = lectura.estado_luz == "encendida"

            # Acumular consumo diario
            if lectura.consumo_watts is not None and lectura.consumo_watts > 0:
                hoy = date.today()
                consumo_result = await db.execute(
                    select(ConsumoDiarioModel).where(
                        ConsumoDiarioModel.zona_id == lectura.zona_id,
                        ConsumoDiarioModel.fecha == hoy,
                    )
                )
                consumo = consumo_result.scalar_one_or_none()

                # Convertir watts instantáneos a kWh (asumiendo intervalo de 1 min)
                kwh_increment = lectura.consumo_watts / 1000 / 60

                if consumo:
                    consumo.kwh_total = float(consumo.kwh_total) + kwh_increment
                    consumo.horas_encendido = float(consumo.horas_encendido) + (1 / 60)
                else:
                    nuevo = ConsumoDiarioModel(
                        zona_id=lectura.zona_id,
                        casa_id=str(casa.id),
                        fecha=hoy,
                        kwh_total=kwh_increment,
                        horas_encendido=1 / 60,
                    )
                    db.add(nuevo)

            procesadas += 1

        except Exception as e:
            errores += 1
            print(f"[TELEMETRY] Error procesando lectura: {e}")

    await db.flush()

    return TelemetryResponse(
        recibidas=len(batch.lecturas),
        procesadas=procesadas,
        errores=errores,
    )


# ══════════════════════════════════════════════════════════════
# 3. HEARTBEAT (ESP32 reporta que está vivo)
# ══════════════════════════════════════════════════════════════

class HeartbeatRequest(BaseModel):
    dispositivos: list[dict]  # [{mac_address, estado, firmware_version}]
    uptime_seconds: Optional[int] = None
    free_memory_kb: Optional[int] = None
    wifi_rssi: Optional[int] = None


class HeartbeatResponse(BaseModel):
    ack: bool
    server_time: str
    config_updated: bool  # Si hay cambios desde la última sync


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def device_heartbeat(
    body: HeartbeatRequest,
    casa: CasaModel = Depends(get_casa_from_device_token),
    db: AsyncSession = Depends(get_db),
):
    """
    ESP32 reporta su estado y el de sus dispositivos conectados.
    El backend actualiza el estado de cada dispositivo.
    """
    now = datetime.now(timezone.utc)

    for disp_info in body.dispositivos:
        mac = disp_info.get("mac_address")
        if not mac:
            continue

        result = await db.execute(
            select(DispositivoModel).where(DispositivoModel.mac_address == mac)
        )
        disp = result.scalar_one_or_none()

        if disp:
            disp.estado = disp_info.get("estado", "online")
            disp.ultimo_heartbeat = now
            if disp_info.get("firmware_version"):
                disp.firmware_version = disp_info["firmware_version"]

    await db.flush()

    # TODO: detectar si config cambió desde último sync
    # Por ahora siempre false, el ESP32 hace poll periódico
    return HeartbeatResponse(
        ack=True,
        server_time=now.isoformat(),
        config_updated=False,
    )


# ══════════════════════════════════════════════════════════════
# 4. REPORTAR ALERTAS
# ══════════════════════════════════════════════════════════════

class DeviceAlert(BaseModel):
    tipo: str  # sensor_offline, temperatura_elevada, dispositivo_error, etc.
    zona_id: Optional[str] = None
    dispositivo_mac: Optional[str] = None
    titulo: str
    mensaje: str
    severidad: str = "warning"  # info, warning, error, success


class AlertsBatch(BaseModel):
    alertas: list[DeviceAlert]


@router.post("/alerts")
async def report_alerts(
    batch: AlertsBatch,
    casa: CasaModel = Depends(get_casa_from_device_token),
    db: AsyncSession = Depends(get_db),
):
    """ESP32 reporta alertas detectadas localmente."""
    created = 0

    for alerta in batch.alertas:
        # Buscar dispositivo_id por MAC si se proporcionó
        dispositivo_id = None
        if alerta.dispositivo_mac:
            result = await db.execute(
                select(DispositivoModel).where(DispositivoModel.mac_address == alerta.dispositivo_mac)
            )
            disp = result.scalar_one_or_none()
            if disp:
                dispositivo_id = disp.id

        nueva = AlertaModel(
            casa_id=casa.id,
            zona_id=alerta.zona_id,
            dispositivo_id=dispositivo_id,
            tipo=alerta.tipo,
            severidad=alerta.severidad,
            titulo=alerta.titulo,
            mensaje=alerta.mensaje,
        )
        db.add(nueva)
        created += 1

    await db.flush()
    return {"alertas_creadas": created}


# ══════════════════════════════════════════════════════════════
# 5. COMANDOS PENDIENTES (PWA → ESP32)
# ══════════════════════════════════════════════════════════════
# Cuando el usuario presiona "Encender" en la PWA, el backend
# ya actualiza config_zonas. El ESP32 detecta cambios comparando
# con su estado local al hacer GET /sync/config.
#
# Para comandos más inmediatos (sin esperar poll), se usa esta tabla.

class PendingCommand(BaseModel):
    id: str
    zona_id: str
    comando: str  # encender, apagar, cambiar_modo, actualizar_config
    parametros: dict
    created_at: str


@router.get("/commands", response_model=list[PendingCommand])
async def get_pending_commands(
    since: Optional[str] = Query(None, description="ISO timestamp, solo comandos después de esta fecha"),
    casa: CasaModel = Depends(get_casa_from_device_token),
    db: AsyncSession = Depends(get_db),
):
    """
    ESP32 consulta si hay comandos pendientes.
    Por ahora los comandos se derivan de cambios en config_zonas.
    En producción esto se reemplaza por DynamoDB + IoT Core shadow.
    """
    # Por ahora retornamos lista vacía.
    # Los comandos reales vienen del cambio de estado en config_zonas
    # que el ESP32 detecta al comparar con su copia local.
    return []


# ══════════════════════════════════════════════════════════════
# 6. ACTUALIZAR ESTADO DESDE ESP32
# ══════════════════════════════════════════════════════════════
# Cuando el ESP32 ejecuta un cambio (ej: el switch físico enciende
# la luz), reporta el nuevo estado al backend.

class StateUpdate(BaseModel):
    zona_id: str
    encendida: Optional[bool] = None
    modo: Optional[str] = None
    # Campos opcionales para Last-Writer-Wins (modo offline PWA).
    # Sin ellos, el handler aplica directo (compat firmware actual).
    client_id: Optional[str] = None         # UUID del comando original (PWA)
    client_timestamp: Optional[str] = None  # ISO 8601, momento en que la PWA generó el cambio


class StateUpdateBatch(BaseModel):
    updates: list[StateUpdate]


class StateUpdateResult(BaseModel):
    """Resultado por item para que la PWA reconcilie su cola offline."""
    client_id: Optional[str] = None
    zona_id: str
    status: str  # "applied" | "stale" | "unknown_zone"
    server_timestamp: str  # ISO 8601: timestamp efectivo del estado en DB


@router.post("/state", response_model=list[StateUpdateResult])
async def update_state(
    batch: StateUpdateBatch,
    casa: CasaModel = Depends(get_casa_from_device_token),
    db: AsyncSession = Depends(get_db),
):
    """
    ESP32 (real o mock) reporta cambios de estado.

    Modos de operación:
    - Compat firmware actual: items sin `client_timestamp` → se aplican directo.
    - Modo offline PWA: items con `client_timestamp` → resolución LWW contra
      `config_zonas.updated_at`. Si el timestamp del cliente es anterior al
      estado guardado, el item se descarta (status="stale").

    Devuelve un resultado por item con status applied|stale|unknown_zone
    para que la PWA reconcilie su cola offline. UPDATE se hace con SQL
    explícito para bypass del `onupdate=utcnow` del ORM y poder fijar
    `updated_at` a `max(client_timestamp, now())`.
    """
    results: list[StateUpdateResult] = []
    now = datetime.now(timezone.utc)

    for upd in batch.updates:
        # Leer updated_at actual (filtra por casa para evitar cross-tenant)
        cur_result = await db.execute(
            select(ConfigZonaModel.updated_at)
            .join(ZonaModel, ZonaModel.id == ConfigZonaModel.zona_id)
            .where(
                ConfigZonaModel.zona_id == upd.zona_id,
                ZonaModel.casa_id == casa.id,
            )
        )
        current_updated_at = cur_result.scalar_one_or_none()

        if current_updated_at is None:
            results.append(StateUpdateResult(
                client_id=upd.client_id,
                zona_id=upd.zona_id,
                status="unknown_zone",
                server_timestamp=now.isoformat(),
            ))
            continue

        # Parsear client_timestamp (si vino y es válido)
        client_ts: Optional[datetime] = None
        if upd.client_timestamp:
            try:
                client_ts = datetime.fromisoformat(upd.client_timestamp)
                if client_ts.tzinfo is None:
                    client_ts = client_ts.replace(tzinfo=timezone.utc)
            except ValueError:
                # Timestamp malformado → tratamos como sin timestamp (compat)
                client_ts = None

        # LWW: si el cliente es más viejo que lo guardado, descartar
        if client_ts is not None and client_ts < current_updated_at:
            results.append(StateUpdateResult(
                client_id=upd.client_id,
                zona_id=upd.zona_id,
                status="stale",
                server_timestamp=current_updated_at.isoformat(),
            ))
            continue

        # Calcular updated_at efectivo
        effective_ts = max(client_ts, now) if client_ts is not None else now

        values_to_set: dict = {"updated_at": effective_ts}
        if upd.encendida is not None:
            values_to_set["encendida"] = upd.encendida
        if upd.modo is not None:
            values_to_set["modo"] = upd.modo

        # UPDATE explícito (core SQL) para bypass del onupdate=utcnow del ORM
        await db.execute(
            sa_update(ConfigZonaModel)
            .where(ConfigZonaModel.zona_id == upd.zona_id)
            .values(**values_to_set)
            .execution_options(synchronize_session=False)
        )
        results.append(StateUpdateResult(
            client_id=upd.client_id,
            zona_id=upd.zona_id,
            status="applied",
            server_timestamp=effective_ts.isoformat(),
        ))

    await db.flush()
    return results
