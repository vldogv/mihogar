"""
DTOs (Data Transfer Objects) — Pydantic schemas para la API.
"""

from pydantic import BaseModel
from typing import Optional


# ── Auth ─────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginPinRequest(BaseModel):
    casa_id: str
    pin: str

class SelectCasaRequest(BaseModel):
    casa_id: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    nombre: str
    casa_id: Optional[str] = None
    requires_casa_selection: bool = False
    zonas_permitidas: list[str] = []

class CasaSimple(BaseModel):
    id: str
    nombre: str
    direccion: Optional[str] = None
    rol: str = "propietario"

class LoginOwnerResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str = "owner"
    nombre: str
    casas: list[CasaSimple]


# ── Zonas / Panel ────────────────────────────────────────────

class ZonaResponse(BaseModel):
    id: str
    nombre: str
    tipo: str
    icono: Optional[str] = None
    orden: int

class ConfigZonaResponse(BaseModel):
    zona_id: str
    encendida: bool
    modo: str
    umbral_oscuridad: int
    auto_encender: bool
    tiempo_apagado_auto: int
    luz_ambiente_actual: Optional[int] = None
    movimiento_detectado: bool
    temperatura_actual: Optional[float] = None
    # ISO 8601. Necesario para que la PWA reconcilie LWW al subir cambios offline.
    # Snapshot, panel y zona detail lo populan cuando está disponible. No-breaking:
    # campo opcional con default None.
    updated_at: Optional[str] = None

class ZonaConConfigResponse(BaseModel):
    zona: ZonaResponse
    config: Optional[ConfigZonaResponse] = None

class PanelResponse(BaseModel):
    zonas_activas: int
    zonas_total: int
    zonas: list[ZonaConConfigResponse]

class ToggleZonaRequest(BaseModel):
    encendida: bool

class CambiarModoRequest(BaseModel):
    modo: str

class ConfigZonaUpdateRequest(BaseModel):
    umbral_oscuridad: Optional[int] = None
    auto_encender: Optional[bool] = None
    tiempo_apagado_auto: Optional[int] = None


# ── Snapshot (modo offline) ──────────────────────────────────

class SnapshotCasaInfo(BaseModel):
    id: str
    nombre: str
    zona_horaria: str


class SnapshotResponse(BaseModel):
    """
    Volcado completo del estado de una casa para que la PWA lo guarde
    en IndexedDB y pueda operar offline. Lo consume la app al iniciar y
    al recuperar conexión. Cada zona incluye `config.updated_at` para
    resolución de conflictos LWW cuando se drene la cola offline.
    """
    server_timestamp: str  # ISO 8601, momento en que el backend generó el snapshot
    casa: SnapshotCasaInfo
    zonas: list["ZonaConConfigResponse"]
    temporizadores: list["TemporizadorResponse"]
    dispositivos: list["DispositivoResponse"]
    modo_nocturno: Optional["ModoNocturnoResponse"] = None


# ── Temporizadores ───────────────────────────────────────────

class TemporizadorResponse(BaseModel):
    id: str
    zona_id: str
    zona_nombre: Optional[str] = None
    tipo: str
    hora_inicio: str
    hora_fin: str
    dias: dict
    solo_si_oscuro: bool
    habilitado: bool

class TemporizadorCreateRequest(BaseModel):
    zona_id: str
    tipo: str = "horario_fijo"
    hora_inicio: str
    hora_fin: str
    lunes: bool = True
    martes: bool = True
    miercoles: bool = True
    jueves: bool = True
    viernes: bool = True
    sabado: bool = False
    domingo: bool = False
    solo_si_oscuro: bool = False

class TemporizadorUpdateRequest(BaseModel):
    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None
    lunes: Optional[bool] = None
    martes: Optional[bool] = None
    miercoles: Optional[bool] = None
    jueves: Optional[bool] = None
    viernes: Optional[bool] = None
    sabado: Optional[bool] = None
    domingo: Optional[bool] = None
    solo_si_oscuro: Optional[bool] = None
    habilitado: Optional[bool] = None


# ── Modo Nocturno ────────────────────────────────────────────

class ZonaNocturnaDTO(BaseModel):
    zona_id: str
    zona_nombre: Optional[str] = None
    zona_tipo: Optional[str] = None
    habilitada: bool

class ModoNocturnoResponse(BaseModel):
    habilitado: bool
    deteccion_inteligente: bool
    hora_inicio: str
    hora_fin: str
    zonas: list[ZonaNocturnaDTO]

class ModoNocturnoUpdateRequest(BaseModel):
    habilitado: Optional[bool] = None
    deteccion_inteligente: Optional[bool] = None
    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None
    zonas: Optional[list[ZonaNocturnaDTO]] = None


# ── Consumo ──────────────────────────────────────────────────

class ConsumoResumenResponse(BaseModel):
    consumo_hoy_kwh: float
    horas_uso_hoy: float
    bimestre_kwh: float
    bimestre_costo: float
    horas_uso_dia_promedio: float
    corte_cfe_dia: int

class ConsumoDiarioDTO(BaseModel):
    zona_id: str
    zona_nombre: Optional[str] = None
    fecha: str
    kwh_total: float
    horas_encendido: float

class HorasPicoDTO(BaseModel):
    zona_id: str
    zona_nombre: Optional[str] = None
    hora: int
    dia_semana: int
    minutos_promedio: float

class ConsumoBimestralDTO(BaseModel):
    bimestre: int
    anio: int
    kwh_total: float
    costo_estimado: float
    horas_uso_dia: float

class AlertaResponse(BaseModel):
    id: str
    tipo: str
    severidad: str
    titulo: str
    mensaje: str
    leida: bool
    created_at: Optional[str] = None


# ── Dispositivos ─────────────────────────────────────────────

class DispositivoResponse(BaseModel):
    id: str
    zona_id: str
    zona_nombre: Optional[str] = None
    tipo: str
    nombre: str
    mac_address: Optional[str] = None
    ip_local: Optional[str] = None
    firmware_version: Optional[str] = None
    estado: str

class DispositivoCreateRequest(BaseModel):
    zona_id: str
    tipo: str
    nombre: str
    mac_address: Optional[str] = None
    ip_local: Optional[str] = None


# ── Usuarios ─────────────────────────────────────────────────

class PermisoZonaDTO(BaseModel):
    zona_id: str
    zona_nombre: Optional[str] = None
    puede_controlar: bool = True
    puede_configurar: bool = False

class UsuarioResponse(BaseModel):
    id: str
    nombre: str
    email: Optional[str] = None
    rol: str
    metodo_acceso: str
    zonas_permitidas: list[str] = []
    permisos: list[PermisoZonaDTO] = []

class UsuarioCreateRequest(BaseModel):
    nombre: str
    email: Optional[str] = None
    password: Optional[str] = None
    pin: Optional[str] = None
    rol: str = "usuario"
    zonas_permitidas: list[str] = []

class UsuarioUpdateRequest(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    rol: Optional[str] = None
    zonas_permitidas: Optional[list[str]] = None

class PermisosRolResponse(BaseModel):
    administrador: list[str]
    encargado: list[str]
    usuario: list[str]


# ── WiFi / Equipos ───────────────────────────────────────────

class WifiConfigRequest(BaseModel):
    wifi_ssid: str
    wifi_password: str
    nombre_instalacion: Optional[str] = None
    zona_horaria: Optional[str] = None
    email_alertas: Optional[str] = None


# ── Genéricos ────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    success: bool = True
