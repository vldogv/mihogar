"""
Modelos SQLAlchemy — Adaptador de persistencia.
Mapean las entidades del dominio a tablas PostgreSQL.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, SmallInteger, Integer, Text, ForeignKey,
    DateTime, Time, Date, Numeric, JSON, Enum as SAEnum, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.domain.entities.models import (
    RolUsuario, MetodoAcceso, ModoZona, TipoZona, TipoDispositivo,
    EstadoDispositivo, TipoTemporizador, TipoAlerta, SeveridadAlerta,
)


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return uuid.uuid4()


class OwnerModel(Base):
    __tablename__ = "owners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    nombre = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    telefono = Column(String(20))
    max_casas = Column(SmallInteger, nullable=False, default=3)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    casas = relationship("CasaModel", back_populates="owner", cascade="all, delete-orphan")


class CasaModel(Base):
    __tablename__ = "casas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("owners.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    direccion = Column(String(255))
    zona_horaria = Column(String(50), nullable=False, default="America/Mexico_City")
    wifi_ssid = Column(String(100))
    wifi_password_enc = Column(String(255))
    nombre_instalacion = Column(String(100))
    email_alertas = Column(String(255))
    corte_cfe_dia = Column(SmallInteger, default=15)
    activa = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    owner = relationship("OwnerModel", back_populates="casas")
    usuarios = relationship("UsuarioCasaModel", back_populates="casa", cascade="all, delete-orphan")
    zonas = relationship("ZonaModel", back_populates="casa", cascade="all, delete-orphan")
    dispositivos = relationship("DispositivoModel", back_populates="casa", cascade="all, delete-orphan")
    temporizadores = relationship("TemporizadorModel", back_populates="casa", cascade="all, delete-orphan")
    modo_nocturno = relationship("ModoNocturnoModel", back_populates="casa", uselist=False, cascade="all, delete-orphan")
    alertas = relationship("AlertaModel", back_populates="casa", cascade="all, delete-orphan")


class UsuarioCasaModel(Base):
    __tablename__ = "usuarios_casa"
    __table_args__ = (
        UniqueConstraint("casa_id", "email", name="uq_email_por_casa"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    casa_id = Column(UUID(as_uuid=True), ForeignKey("casas.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("owners.id"))
    nombre = Column(String(100), nullable=False)
    email = Column(String(255), index=True)
    password_hash = Column(String(255))
    pin_hash = Column(String(255))
    rol = Column(SAEnum("administrador", "encargado", "usuario", name="rol_usuario", create_type=False), nullable=False, default=RolUsuario.USUARIO)
    metodo_acceso = Column(SAEnum("email", "pin", name="metodo_acceso", create_type=False), nullable=False, default=MetodoAcceso.EMAIL)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    casa = relationship("CasaModel", back_populates="usuarios")
    permisos = relationship("PermisoZonaModel", back_populates="usuario", cascade="all, delete-orphan")


class ZonaModel(Base):
    __tablename__ = "zonas"
    __table_args__ = (
        UniqueConstraint("casa_id", "nombre", name="uq_zona_nombre_casa"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    casa_id = Column(UUID(as_uuid=True), ForeignKey("casas.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    tipo = Column(SAEnum("habitacion", "zona_de_paso", "exterior", name="tipo_zona", create_type=False), nullable=False, default=TipoZona.HABITACION)
    icono = Column(String(50))
    orden = Column(SmallInteger, nullable=False, default=0)
    activa = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    casa = relationship("CasaModel", back_populates="zonas")
    config = relationship("ConfigZonaModel", back_populates="zona", uselist=False, cascade="all, delete-orphan")
    dispositivos = relationship("DispositivoModel", back_populates="zona", cascade="all, delete-orphan")
    permisos = relationship("PermisoZonaModel", back_populates="zona", cascade="all, delete-orphan")


class ConfigZonaModel(Base):
    __tablename__ = "config_zonas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    zona_id = Column(UUID(as_uuid=True), ForeignKey("zonas.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    encendida = Column(Boolean, nullable=False, default=False)
    modo = Column(SAEnum("automatico", "manual", "temporizador", name="modo_zona", create_type=False), nullable=False, default=ModoZona.AUTOMATICO)
    umbral_oscuridad = Column(SmallInteger, nullable=False, default=40)
    auto_encender = Column(Boolean, nullable=False, default=True)
    tiempo_apagado_auto = Column(SmallInteger, nullable=False, default=60)
    luz_ambiente_actual = Column(SmallInteger)
    movimiento_detectado = Column(Boolean, default=False)
    temperatura_actual = Column(Numeric(5, 2))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    zona = relationship("ZonaModel", back_populates="config")


class PermisoZonaModel(Base):
    __tablename__ = "permisos_zona"
    __table_args__ = (
        UniqueConstraint("usuario_id", "zona_id", name="uq_permiso_usuario_zona"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios_casa.id", ondelete="CASCADE"), nullable=False, index=True)
    zona_id = Column(UUID(as_uuid=True), ForeignKey("zonas.id", ondelete="CASCADE"), nullable=False, index=True)
    puede_controlar = Column(Boolean, nullable=False, default=True)
    puede_configurar = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    usuario = relationship("UsuarioCasaModel", back_populates="permisos")
    zona = relationship("ZonaModel", back_populates="permisos")


class DispositivoModel(Base):
    __tablename__ = "dispositivos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    zona_id = Column(UUID(as_uuid=True), ForeignKey("zonas.id", ondelete="CASCADE"), nullable=False, index=True)
    casa_id = Column(UUID(as_uuid=True), ForeignKey("casas.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(SAEnum("modulo_shelly", "sensor_pir", "sensor_crepuscular", "camara_ip", name="tipo_dispositivo", create_type=False), nullable=False)
    nombre = Column(String(100), nullable=False)
    mac_address = Column(String(17), unique=True)
    ip_local = Column(String(45))
    firmware_version = Column(String(20))
    estado = Column(SAEnum("online", "offline", "error", "actualizando", name="estado_dispositivo", create_type=False), nullable=False, default=EstadoDispositivo.OFFLINE)
    ultimo_heartbeat = Column(DateTime(timezone=True))
    configuracion = Column(JSON, default={})
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    zona = relationship("ZonaModel", back_populates="dispositivos")
    casa = relationship("CasaModel", back_populates="dispositivos")


class TemporizadorModel(Base):
    __tablename__ = "temporizadores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    zona_id = Column(UUID(as_uuid=True), ForeignKey("zonas.id", ondelete="CASCADE"), nullable=False, index=True)
    casa_id = Column(UUID(as_uuid=True), ForeignKey("casas.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(SAEnum("horario_fijo", "por_sensor", name="tipo_temporizador", create_type=False), nullable=False, default=TipoTemporizador.HORARIO_FIJO)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    lunes = Column(Boolean, nullable=False, default=True)
    martes = Column(Boolean, nullable=False, default=True)
    miercoles = Column(Boolean, nullable=False, default=True)
    jueves = Column(Boolean, nullable=False, default=True)
    viernes = Column(Boolean, nullable=False, default=True)
    sabado = Column(Boolean, nullable=False, default=False)
    domingo = Column(Boolean, nullable=False, default=False)
    solo_si_oscuro = Column(Boolean, nullable=False, default=False)
    habilitado = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    zona = relationship("ZonaModel")
    casa = relationship("CasaModel", back_populates="temporizadores")


class ModoNocturnoModel(Base):
    __tablename__ = "modo_nocturno"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    casa_id = Column(UUID(as_uuid=True), ForeignKey("casas.id", ondelete="CASCADE"), nullable=False, unique=True)
    habilitado = Column(Boolean, nullable=False, default=False)
    deteccion_inteligente = Column(Boolean, nullable=False, default=True)
    hora_inicio = Column(Time, nullable=False, default="23:00")
    hora_fin = Column(Time, nullable=False, default="06:00")
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    casa = relationship("CasaModel", back_populates="modo_nocturno")
    zonas_nocturnas = relationship("ZonaNocturnaModel", back_populates="modo_nocturno", cascade="all, delete-orphan")


class ZonaNocturnaModel(Base):
    __tablename__ = "zonas_nocturnas"
    __table_args__ = (
        UniqueConstraint("modo_nocturno_id", "zona_id", name="uq_zona_nocturna"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    modo_nocturno_id = Column(UUID(as_uuid=True), ForeignKey("modo_nocturno.id", ondelete="CASCADE"), nullable=False)
    zona_id = Column(UUID(as_uuid=True), ForeignKey("zonas.id", ondelete="CASCADE"), nullable=False)
    habilitada = Column(Boolean, nullable=False, default=True)

    modo_nocturno = relationship("ModoNocturnoModel", back_populates="zonas_nocturnas")


class ConsumoDiarioModel(Base):
    __tablename__ = "consumo_diario"
    __table_args__ = (
        UniqueConstraint("zona_id", "fecha", name="uq_consumo_dia_zona"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    zona_id = Column(UUID(as_uuid=True), ForeignKey("zonas.id", ondelete="CASCADE"), nullable=False, index=True)
    casa_id = Column(UUID(as_uuid=True), ForeignKey("casas.id", ondelete="CASCADE"), nullable=False, index=True)
    fecha = Column(Date, nullable=False)
    kwh_total = Column(Numeric(8, 4), nullable=False, default=0)
    horas_encendido = Column(Numeric(6, 2), nullable=False, default=0)
    minutos_nocturno = Column(Numeric(6, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class ConsumoBimestralModel(Base):
    __tablename__ = "consumo_bimestral"
    __table_args__ = (
        UniqueConstraint("casa_id", "bimestre", "anio", name="uq_bimestre_casa"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    casa_id = Column(UUID(as_uuid=True), ForeignKey("casas.id", ondelete="CASCADE"), nullable=False, index=True)
    bimestre = Column(SmallInteger, nullable=False)
    anio = Column(SmallInteger, nullable=False)
    kwh_total = Column(Numeric(10, 4), nullable=False, default=0)
    costo_estimado = Column(Numeric(10, 2), nullable=False, default=0)
    horas_uso_dia = Column(Numeric(6, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class HorasPicoModel(Base):
    __tablename__ = "horas_pico"
    __table_args__ = (
        UniqueConstraint("zona_id", "hora", "dia_semana", "periodo_inicio", name="uq_hora_pico"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    zona_id = Column(UUID(as_uuid=True), ForeignKey("zonas.id", ondelete="CASCADE"), nullable=False)
    casa_id = Column(UUID(as_uuid=True), ForeignKey("casas.id", ondelete="CASCADE"), nullable=False, index=True)
    hora = Column(SmallInteger, nullable=False)
    dia_semana = Column(SmallInteger, nullable=False)
    minutos_promedio = Column(Numeric(6, 2), nullable=False, default=0)
    periodo_inicio = Column(Date, nullable=False)
    periodo_fin = Column(Date, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class AlertaModel(Base):
    __tablename__ = "alertas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    casa_id = Column(UUID(as_uuid=True), ForeignKey("casas.id", ondelete="CASCADE"), nullable=False, index=True)
    zona_id = Column(UUID(as_uuid=True), ForeignKey("zonas.id", ondelete="SET NULL"))
    dispositivo_id = Column(UUID(as_uuid=True), ForeignKey("dispositivos.id", ondelete="SET NULL"))
    tipo = Column(SAEnum("sensor_offline", "consumo_elevado", "firmware_actualizado", "temperatura_elevada", "dispositivo_error", "consumo_nocturno_alto", "umbral_superado", name="tipo_alerta", create_type=False), nullable=False)
    severidad = Column(SAEnum("info", "warning", "error", "success", name="severidad_alerta", create_type=False), nullable=False, default=SeveridadAlerta.INFO)
    titulo = Column(String(200), nullable=False)
    mensaje = Column(Text, nullable=False)
    leida = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    casa = relationship("CasaModel", back_populates="alertas")


class PerfilSagemakerModel(Base):
    __tablename__ = "perfiles_sagemaker"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    zona_id = Column(UUID(as_uuid=True), ForeignKey("zonas.id", ondelete="CASCADE"), nullable=False, index=True)
    casa_id = Column(UUID(as_uuid=True), ForeignKey("casas.id", ondelete="CASCADE"), nullable=False, index=True)
    umbral_oscuridad_sugerido = Column(SmallInteger)
    tiempo_apagado_sugerido = Column(SmallInteger)
    horas_uso_optimas = Column(JSON)
    patron_detectado = Column(String(100))
    modelo_version = Column(String(50))
    confianza = Column(Numeric(5, 4))
    datos_entrenamiento_desde = Column(Date)
    datos_entrenamiento_hasta = Column(Date)
    aplicado = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
