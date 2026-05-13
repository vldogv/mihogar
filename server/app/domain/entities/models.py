"""
Domain entities - Núcleo del negocio.
Estas clases NO dependen de SQLAlchemy ni de ningún framework.
Son objetos puros de Python que representan los conceptos del dominio.
"""

from dataclasses import dataclass, field
from datetime import datetime, time, date
from typing import Optional
from enum import Enum
import uuid


# ── Enums del dominio ──────────────────────────────────────

class RolUsuario(str, Enum):
    ADMINISTRADOR = "administrador"
    ENCARGADO = "encargado"
    USUARIO = "usuario"


class MetodoAcceso(str, Enum):
    EMAIL = "email"
    PIN = "pin"


class ModoZona(str, Enum):
    AUTOMATICO = "automatico"
    MANUAL = "manual"
    TEMPORIZADOR = "temporizador"


class TipoZona(str, Enum):
    HABITACION = "habitacion"
    ZONA_DE_PASO = "zona_de_paso"
    EXTERIOR = "exterior"


class TipoDispositivo(str, Enum):
    MODULO_SHELLY = "modulo_shelly"
    SENSOR_PIR = "sensor_pir"
    SENSOR_CREPUSCULAR = "sensor_crepuscular"
    CAMARA_IP = "camara_ip"


class EstadoDispositivo(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    ACTUALIZANDO = "actualizando"


class TipoTemporizador(str, Enum):
    HORARIO_FIJO = "horario_fijo"
    POR_SENSOR = "por_sensor"


class TipoAlerta(str, Enum):
    SENSOR_OFFLINE = "sensor_offline"
    CONSUMO_ELEVADO = "consumo_elevado"
    FIRMWARE_ACTUALIZADO = "firmware_actualizado"
    TEMPERATURA_ELEVADA = "temperatura_elevada"
    DISPOSITIVO_ERROR = "dispositivo_error"
    CONSUMO_NOCTURNO_ALTO = "consumo_nocturno_alto"
    UMBRAL_SUPERADO = "umbral_superado"


class SeveridadAlerta(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


# ── Entidades ──────────────────────────────────────────────

@dataclass
class Owner:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nombre: str = ""
    email: str = ""
    password_hash: str = ""
    telefono: Optional[str] = None
    max_casas: int = 3
    activo: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Casa:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str = ""
    nombre: str = ""
    direccion: Optional[str] = None
    zona_horaria: str = "America/Mexico_City"
    wifi_ssid: Optional[str] = None
    wifi_password_enc: Optional[str] = None
    nombre_instalacion: Optional[str] = None
    email_alertas: Optional[str] = None
    corte_cfe_dia: int = 15
    activa: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class UsuarioCasa:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    casa_id: str = ""
    owner_id: Optional[str] = None
    nombre: str = ""
    email: Optional[str] = None
    password_hash: Optional[str] = None
    pin_hash: Optional[str] = None
    rol: RolUsuario = RolUsuario.USUARIO
    metodo_acceso: MetodoAcceso = MetodoAcceso.EMAIL
    activo: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Zona:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    casa_id: str = ""
    nombre: str = ""
    tipo: TipoZona = TipoZona.HABITACION
    icono: Optional[str] = None
    orden: int = 0
    activa: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ConfigZona:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    zona_id: str = ""
    encendida: bool = False
    modo: ModoZona = ModoZona.AUTOMATICO
    umbral_oscuridad: int = 40
    auto_encender: bool = True
    tiempo_apagado_auto: int = 60
    luz_ambiente_actual: Optional[int] = None
    movimiento_detectado: bool = False
    temperatura_actual: Optional[float] = None
    updated_at: Optional[datetime] = None


@dataclass
class PermisoZona:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    usuario_id: str = ""
    zona_id: str = ""
    puede_controlar: bool = True
    puede_configurar: bool = False
    created_at: Optional[datetime] = None


@dataclass
class Dispositivo:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    zona_id: str = ""
    casa_id: str = ""
    tipo: TipoDispositivo = TipoDispositivo.MODULO_SHELLY
    nombre: str = ""
    mac_address: Optional[str] = None
    ip_local: Optional[str] = None
    firmware_version: Optional[str] = None
    estado: EstadoDispositivo = EstadoDispositivo.OFFLINE
    ultimo_heartbeat: Optional[datetime] = None
    configuracion: dict = field(default_factory=dict)
    activo: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Temporizador:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    zona_id: str = ""
    casa_id: str = ""
    tipo: TipoTemporizador = TipoTemporizador.HORARIO_FIJO
    hora_inicio: Optional[time] = None
    hora_fin: Optional[time] = None
    lunes: bool = True
    martes: bool = True
    miercoles: bool = True
    jueves: bool = True
    viernes: bool = True
    sabado: bool = False
    domingo: bool = False
    solo_si_oscuro: bool = False
    habilitado: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ModoNocturno:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    casa_id: str = ""
    habilitado: bool = False
    deteccion_inteligente: bool = True
    hora_inicio: Optional[time] = None
    hora_fin: Optional[time] = None
    updated_at: Optional[datetime] = None


@dataclass
class ZonaNocturna:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    modo_nocturno_id: str = ""
    zona_id: str = ""
    habilitada: bool = True


@dataclass
class ConsumoDiario:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    zona_id: str = ""
    casa_id: str = ""
    fecha: Optional[date] = None
    kwh_total: float = 0.0
    horas_encendido: float = 0.0
    minutos_nocturno: float = 0.0
    created_at: Optional[datetime] = None


@dataclass
class ConsumoBimestral:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    casa_id: str = ""
    bimestre: int = 1
    anio: int = 2026
    kwh_total: float = 0.0
    costo_estimado: float = 0.0
    horas_uso_dia: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class HorasPico:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    zona_id: str = ""
    casa_id: str = ""
    hora: int = 0
    dia_semana: int = 0
    minutos_promedio: float = 0.0
    periodo_inicio: Optional[date] = None
    periodo_fin: Optional[date] = None
    updated_at: Optional[datetime] = None


@dataclass
class Alerta:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    casa_id: str = ""
    zona_id: Optional[str] = None
    dispositivo_id: Optional[str] = None
    tipo: TipoAlerta = TipoAlerta.SENSOR_OFFLINE
    severidad: SeveridadAlerta = SeveridadAlerta.INFO
    titulo: str = ""
    mensaje: str = ""
    leida: bool = False
    created_at: Optional[datetime] = None


@dataclass
class PerfilSagemaker:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    zona_id: str = ""
    casa_id: str = ""
    umbral_oscuridad_sugerido: Optional[int] = None
    tiempo_apagado_sugerido: Optional[int] = None
    horas_uso_optimas: Optional[dict] = None
    patron_detectado: Optional[str] = None
    modelo_version: Optional[str] = None
    confianza: Optional[float] = None
    datos_entrenamiento_desde: Optional[date] = None
    datos_entrenamiento_hasta: Optional[date] = None
    aplicado: bool = False
    created_at: Optional[datetime] = None
