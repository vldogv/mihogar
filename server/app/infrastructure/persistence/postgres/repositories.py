"""
Implementaciones de repositorios — Adaptadores de salida.
Implementan las interfaces definidas en domain/repositories usando SQLAlchemy.
"""

from typing import Optional
from sqlalchemy import select, delete, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.models import (
    Owner, Casa, UsuarioCasa, Zona, ConfigZona, PermisoZona,
    Dispositivo, Temporizador, ModoNocturno, ZonaNocturna,
    ConsumoDiario, ConsumoBimestral, HorasPico, Alerta, PerfilSagemaker,
)
from app.domain.repositories.interfaces import (
    OwnerRepository, CasaRepository, UsuarioCasaRepository, ZonaRepository,
    ConfigZonaRepository, PermisoZonaRepository, DispositivoRepository,
    TemporizadorRepository, ModoNocturnoRepository, ZonaNocturnaRepository,
    ConsumoRepository, AlertaRepository, PerfilSagemakerRepository,
)
from app.infrastructure.persistence.postgres.models import (
    OwnerModel, CasaModel, UsuarioCasaModel, ZonaModel, ConfigZonaModel,
    PermisoZonaModel, DispositivoModel, TemporizadorModel, ModoNocturnoModel,
    ZonaNocturnaModel, ConsumoDiarioModel, ConsumoBimestralModel,
    HorasPicoModel, AlertaModel, PerfilSagemakerModel,
)


# ── Helpers de mapeo Model <-> Entity ────────────────────────

def _to_str(val) -> Optional[str]:
    return str(val) if val else None


def _owner_to_entity(m: OwnerModel) -> Owner:
    return Owner(
        id=_to_str(m.id), nombre=m.nombre, email=m.email,
        password_hash=m.password_hash, telefono=m.telefono,
        max_casas=m.max_casas, activo=m.activo,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _casa_to_entity(m: CasaModel) -> Casa:
    return Casa(
        id=_to_str(m.id), owner_id=_to_str(m.owner_id), nombre=m.nombre,
        direccion=m.direccion, zona_horaria=m.zona_horaria,
        wifi_ssid=m.wifi_ssid, wifi_password_enc=m.wifi_password_enc,
        nombre_instalacion=m.nombre_instalacion, email_alertas=m.email_alertas,
        corte_cfe_dia=m.corte_cfe_dia, activa=m.activa,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _usuario_to_entity(m: UsuarioCasaModel) -> UsuarioCasa:
    return UsuarioCasa(
        id=_to_str(m.id), casa_id=_to_str(m.casa_id), owner_id=_to_str(m.owner_id),
        nombre=m.nombre, email=m.email, password_hash=m.password_hash,
        pin_hash=m.pin_hash, rol=m.rol, metodo_acceso=m.metodo_acceso,
        activo=m.activo, created_at=m.created_at, updated_at=m.updated_at,
    )


def _zona_to_entity(m: ZonaModel) -> Zona:
    return Zona(
        id=_to_str(m.id), casa_id=_to_str(m.casa_id), nombre=m.nombre,
        tipo=m.tipo, icono=m.icono, orden=m.orden, activa=m.activa,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _config_to_entity(m: ConfigZonaModel) -> ConfigZona:
    return ConfigZona(
        id=_to_str(m.id), zona_id=_to_str(m.zona_id), encendida=m.encendida,
        modo=m.modo, umbral_oscuridad=m.umbral_oscuridad,
        auto_encender=m.auto_encender, tiempo_apagado_auto=m.tiempo_apagado_auto,
        luz_ambiente_actual=m.luz_ambiente_actual,
        movimiento_detectado=m.movimiento_detectado,
        temperatura_actual=float(m.temperatura_actual) if m.temperatura_actual else None,
        updated_at=m.updated_at,
    )


def _permiso_to_entity(m: PermisoZonaModel) -> PermisoZona:
    return PermisoZona(
        id=_to_str(m.id), usuario_id=_to_str(m.usuario_id),
        zona_id=_to_str(m.zona_id), puede_controlar=m.puede_controlar,
        puede_configurar=m.puede_configurar, created_at=m.created_at,
    )


def _dispositivo_to_entity(m: DispositivoModel) -> Dispositivo:
    return Dispositivo(
        id=_to_str(m.id), zona_id=_to_str(m.zona_id), casa_id=_to_str(m.casa_id),
        tipo=m.tipo, nombre=m.nombre, mac_address=m.mac_address,
        ip_local=m.ip_local, firmware_version=m.firmware_version,
        estado=m.estado, ultimo_heartbeat=m.ultimo_heartbeat,
        configuracion=m.configuracion or {}, activo=m.activo,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _temporizador_to_entity(m: TemporizadorModel) -> Temporizador:
    return Temporizador(
        id=_to_str(m.id), zona_id=_to_str(m.zona_id), casa_id=_to_str(m.casa_id),
        tipo=m.tipo, hora_inicio=m.hora_inicio, hora_fin=m.hora_fin,
        lunes=m.lunes, martes=m.martes, miercoles=m.miercoles,
        jueves=m.jueves, viernes=m.viernes, sabado=m.sabado, domingo=m.domingo,
        solo_si_oscuro=m.solo_si_oscuro, habilitado=m.habilitado,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _modo_nocturno_to_entity(m: ModoNocturnoModel) -> ModoNocturno:
    return ModoNocturno(
        id=_to_str(m.id), casa_id=_to_str(m.casa_id), habilitado=m.habilitado,
        deteccion_inteligente=m.deteccion_inteligente,
        hora_inicio=m.hora_inicio, hora_fin=m.hora_fin, updated_at=m.updated_at,
    )


def _alerta_to_entity(m: AlertaModel) -> Alerta:
    return Alerta(
        id=_to_str(m.id), casa_id=_to_str(m.casa_id),
        zona_id=_to_str(m.zona_id), dispositivo_id=_to_str(m.dispositivo_id),
        tipo=m.tipo, severidad=m.severidad, titulo=m.titulo,
        mensaje=m.mensaje, leida=m.leida, created_at=m.created_at,
    )


# ── Implementaciones ─────────────────────────────────────────

class PostgresOwnerRepository(OwnerRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, owner_id: str) -> Optional[Owner]:
        result = await self.session.execute(
            select(OwnerModel).where(OwnerModel.id == owner_id)
        )
        m = result.scalar_one_or_none()
        return _owner_to_entity(m) if m else None

    async def get_by_email(self, email: str) -> Optional[Owner]:
        result = await self.session.execute(
            select(OwnerModel).where(OwnerModel.email == email)
        )
        m = result.scalar_one_or_none()
        return _owner_to_entity(m) if m else None

    async def create(self, owner: Owner) -> Owner:
        m = OwnerModel(
            id=owner.id, nombre=owner.nombre, email=owner.email,
            password_hash=owner.password_hash, telefono=owner.telefono,
            max_casas=owner.max_casas,
        )
        self.session.add(m)
        await self.session.flush()
        return _owner_to_entity(m)

    async def update(self, owner: Owner) -> Owner:
        result = await self.session.execute(
            select(OwnerModel).where(OwnerModel.id == owner.id)
        )
        m = result.scalar_one()
        m.nombre = owner.nombre
        m.email = owner.email
        m.telefono = owner.telefono
        m.activo = owner.activo
        await self.session.flush()
        return _owner_to_entity(m)


class PostgresCasaRepository(CasaRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, casa_id: str) -> Optional[Casa]:
        result = await self.session.execute(
            select(CasaModel).where(CasaModel.id == casa_id)
        )
        m = result.scalar_one_or_none()
        return _casa_to_entity(m) if m else None

    async def get_by_owner(self, owner_id: str) -> list[Casa]:
        result = await self.session.execute(
            select(CasaModel).where(
                CasaModel.owner_id == owner_id, CasaModel.activa == True
            ).order_by(CasaModel.nombre)
        )
        return [_casa_to_entity(m) for m in result.scalars().all()]

    async def create(self, casa: Casa) -> Casa:
        m = CasaModel(
            id=casa.id, owner_id=casa.owner_id, nombre=casa.nombre,
            direccion=casa.direccion, zona_horaria=casa.zona_horaria,
            corte_cfe_dia=casa.corte_cfe_dia,
        )
        self.session.add(m)
        await self.session.flush()
        return _casa_to_entity(m)

    async def update(self, casa: Casa) -> Casa:
        result = await self.session.execute(
            select(CasaModel).where(CasaModel.id == casa.id)
        )
        m = result.scalar_one()
        m.nombre = casa.nombre
        m.direccion = casa.direccion
        m.zona_horaria = casa.zona_horaria
        m.wifi_ssid = casa.wifi_ssid
        m.wifi_password_enc = casa.wifi_password_enc
        m.nombre_instalacion = casa.nombre_instalacion
        m.email_alertas = casa.email_alertas
        m.corte_cfe_dia = casa.corte_cfe_dia
        await self.session.flush()
        return _casa_to_entity(m)

    async def count_by_owner(self, owner_id: str) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(CasaModel).where(
                CasaModel.owner_id == owner_id, CasaModel.activa == True
            )
        )
        return result.scalar()


class PostgresUsuarioCasaRepository(UsuarioCasaRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, usuario_id: str) -> Optional[UsuarioCasa]:
        result = await self.session.execute(
            select(UsuarioCasaModel).where(UsuarioCasaModel.id == usuario_id)
        )
        m = result.scalar_one_or_none()
        return _usuario_to_entity(m) if m else None

    async def get_by_email(self, email: str) -> Optional[UsuarioCasa]:
        result = await self.session.execute(
            select(UsuarioCasaModel).where(
                UsuarioCasaModel.email == email, UsuarioCasaModel.activo == True
            )
        )
        m = result.scalar_one_or_none()
        return _usuario_to_entity(m) if m else None

    async def get_by_email_and_casa(self, email: str, casa_id: str) -> Optional[UsuarioCasa]:
        result = await self.session.execute(
            select(UsuarioCasaModel).where(
                UsuarioCasaModel.email == email,
                UsuarioCasaModel.casa_id == casa_id,
                UsuarioCasaModel.activo == True,
            )
        )
        m = result.scalar_one_or_none()
        return _usuario_to_entity(m) if m else None

    async def get_by_casa(self, casa_id: str) -> list[UsuarioCasa]:
        result = await self.session.execute(
            select(UsuarioCasaModel).where(
                UsuarioCasaModel.casa_id == casa_id, UsuarioCasaModel.activo == True
            ).order_by(UsuarioCasaModel.rol, UsuarioCasaModel.nombre)
        )
        return [_usuario_to_entity(m) for m in result.scalars().all()]

    async def get_by_pin_and_casa(self, pin_hash: str, casa_id: str) -> Optional[UsuarioCasa]:
        # For PIN auth we need to check all users in the casa
        result = await self.session.execute(
            select(UsuarioCasaModel).where(
                UsuarioCasaModel.casa_id == casa_id,
                UsuarioCasaModel.metodo_acceso == "pin",
                UsuarioCasaModel.activo == True,
            )
        )
        return [_usuario_to_entity(m) for m in result.scalars().all()]

    async def create(self, usuario: UsuarioCasa) -> UsuarioCasa:
        m = UsuarioCasaModel(
            id=usuario.id, casa_id=usuario.casa_id, owner_id=usuario.owner_id,
            nombre=usuario.nombre, email=usuario.email,
            password_hash=usuario.password_hash, pin_hash=usuario.pin_hash,
            rol=usuario.rol, metodo_acceso=usuario.metodo_acceso,
        )
        self.session.add(m)
        await self.session.flush()
        return _usuario_to_entity(m)

    async def update(self, usuario: UsuarioCasa) -> UsuarioCasa:
        result = await self.session.execute(
            select(UsuarioCasaModel).where(UsuarioCasaModel.id == usuario.id)
        )
        m = result.scalar_one()
        m.nombre = usuario.nombre
        m.email = usuario.email
        m.rol = usuario.rol
        m.activo = usuario.activo
        if usuario.password_hash:
            m.password_hash = usuario.password_hash
        if usuario.pin_hash:
            m.pin_hash = usuario.pin_hash
        await self.session.flush()
        return _usuario_to_entity(m)

    async def delete(self, usuario_id: str) -> bool:
        result = await self.session.execute(
            select(UsuarioCasaModel).where(UsuarioCasaModel.id == usuario_id)
        )
        m = result.scalar_one_or_none()
        if m:
            m.activo = False
            await self.session.flush()
            return True
        return False


class PostgresZonaRepository(ZonaRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, zona_id: str) -> Optional[Zona]:
        result = await self.session.execute(
            select(ZonaModel).where(ZonaModel.id == zona_id)
        )
        m = result.scalar_one_or_none()
        return _zona_to_entity(m) if m else None

    async def get_by_casa(self, casa_id: str) -> list[Zona]:
        result = await self.session.execute(
            select(ZonaModel).where(
                ZonaModel.casa_id == casa_id, ZonaModel.activa == True
            ).order_by(ZonaModel.orden)
        )
        return [_zona_to_entity(m) for m in result.scalars().all()]

    async def create(self, zona: Zona) -> Zona:
        m = ZonaModel(
            id=zona.id, casa_id=zona.casa_id, nombre=zona.nombre,
            tipo=zona.tipo, icono=zona.icono, orden=zona.orden,
        )
        self.session.add(m)
        await self.session.flush()
        return _zona_to_entity(m)

    async def update(self, zona: Zona) -> Zona:
        result = await self.session.execute(
            select(ZonaModel).where(ZonaModel.id == zona.id)
        )
        m = result.scalar_one()
        m.nombre = zona.nombre
        m.tipo = zona.tipo
        m.icono = zona.icono
        m.orden = zona.orden
        await self.session.flush()
        return _zona_to_entity(m)


class PostgresConfigZonaRepository(ConfigZonaRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_zona(self, zona_id: str) -> Optional[ConfigZona]:
        result = await self.session.execute(
            select(ConfigZonaModel).where(ConfigZonaModel.zona_id == zona_id)
        )
        m = result.scalar_one_or_none()
        return _config_to_entity(m) if m else None

    async def get_all_by_casa(self, casa_id: str) -> list[ConfigZona]:
        result = await self.session.execute(
            select(ConfigZonaModel).join(ZonaModel).where(ZonaModel.casa_id == casa_id)
        )
        return [_config_to_entity(m) for m in result.scalars().all()]

    async def upsert(self, config: ConfigZona) -> ConfigZona:
        result = await self.session.execute(
            select(ConfigZonaModel).where(ConfigZonaModel.zona_id == config.zona_id)
        )
        m = result.scalar_one_or_none()
        if m:
            m.encendida = config.encendida
            m.modo = config.modo
            m.umbral_oscuridad = config.umbral_oscuridad
            m.auto_encender = config.auto_encender
            m.tiempo_apagado_auto = config.tiempo_apagado_auto
            m.luz_ambiente_actual = config.luz_ambiente_actual
            m.movimiento_detectado = config.movimiento_detectado
            m.temperatura_actual = config.temperatura_actual
        else:
            m = ConfigZonaModel(
                id=config.id, zona_id=config.zona_id, encendida=config.encendida,
                modo=config.modo, umbral_oscuridad=config.umbral_oscuridad,
                auto_encender=config.auto_encender,
                tiempo_apagado_auto=config.tiempo_apagado_auto,
            )
            self.session.add(m)
        await self.session.flush()
        return _config_to_entity(m)


class PostgresPermisoZonaRepository(PermisoZonaRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_usuario(self, usuario_id: str) -> list[PermisoZona]:
        result = await self.session.execute(
            select(PermisoZonaModel).where(PermisoZonaModel.usuario_id == usuario_id)
        )
        return [_permiso_to_entity(m) for m in result.scalars().all()]

    async def get_by_zona(self, zona_id: str) -> list[PermisoZona]:
        result = await self.session.execute(
            select(PermisoZonaModel).where(PermisoZonaModel.zona_id == zona_id)
        )
        return [_permiso_to_entity(m) for m in result.scalars().all()]

    async def set_permisos(self, usuario_id: str, permisos: list[PermisoZona]) -> list[PermisoZona]:
        await self.session.execute(
            delete(PermisoZonaModel).where(PermisoZonaModel.usuario_id == usuario_id)
        )
        models = []
        for p in permisos:
            m = PermisoZonaModel(
                usuario_id=usuario_id, zona_id=p.zona_id,
                puede_controlar=p.puede_controlar, puede_configurar=p.puede_configurar,
            )
            self.session.add(m)
            models.append(m)
        await self.session.flush()
        return [_permiso_to_entity(m) for m in models]

    async def delete_by_usuario(self, usuario_id: str) -> bool:
        await self.session.execute(
            delete(PermisoZonaModel).where(PermisoZonaModel.usuario_id == usuario_id)
        )
        return True


class PostgresDispositivoRepository(DispositivoRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, dispositivo_id: str) -> Optional[Dispositivo]:
        result = await self.session.execute(
            select(DispositivoModel).where(DispositivoModel.id == dispositivo_id)
        )
        m = result.scalar_one_or_none()
        return _dispositivo_to_entity(m) if m else None

    async def get_by_casa(self, casa_id: str) -> list[Dispositivo]:
        result = await self.session.execute(
            select(DispositivoModel).where(
                DispositivoModel.casa_id == casa_id, DispositivoModel.activo == True
            )
        )
        return [_dispositivo_to_entity(m) for m in result.scalars().all()]

    async def get_by_zona(self, zona_id: str) -> list[Dispositivo]:
        result = await self.session.execute(
            select(DispositivoModel).where(
                DispositivoModel.zona_id == zona_id, DispositivoModel.activo == True
            )
        )
        return [_dispositivo_to_entity(m) for m in result.scalars().all()]

    async def create(self, dispositivo: Dispositivo) -> Dispositivo:
        m = DispositivoModel(
            id=dispositivo.id, zona_id=dispositivo.zona_id, casa_id=dispositivo.casa_id,
            tipo=dispositivo.tipo, nombre=dispositivo.nombre,
            mac_address=dispositivo.mac_address, ip_local=dispositivo.ip_local,
            firmware_version=dispositivo.firmware_version,
            configuracion=dispositivo.configuracion,
        )
        self.session.add(m)
        await self.session.flush()
        return _dispositivo_to_entity(m)

    async def update(self, dispositivo: Dispositivo) -> Dispositivo:
        result = await self.session.execute(
            select(DispositivoModel).where(DispositivoModel.id == dispositivo.id)
        )
        m = result.scalar_one()
        m.nombre = dispositivo.nombre
        m.zona_id = dispositivo.zona_id
        m.tipo = dispositivo.tipo
        m.mac_address = dispositivo.mac_address
        m.ip_local = dispositivo.ip_local
        m.firmware_version = dispositivo.firmware_version
        m.estado = dispositivo.estado
        m.configuracion = dispositivo.configuracion
        await self.session.flush()
        return _dispositivo_to_entity(m)

    async def delete(self, dispositivo_id: str) -> bool:
        result = await self.session.execute(
            select(DispositivoModel).where(DispositivoModel.id == dispositivo_id)
        )
        m = result.scalar_one_or_none()
        if m:
            m.activo = False
            await self.session.flush()
            return True
        return False


class PostgresTemporizadorRepository(TemporizadorRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, temporizador_id: str) -> Optional[Temporizador]:
        result = await self.session.execute(
            select(TemporizadorModel).where(TemporizadorModel.id == temporizador_id)
        )
        m = result.scalar_one_or_none()
        return _temporizador_to_entity(m) if m else None

    async def get_by_casa(self, casa_id: str) -> list[Temporizador]:
        result = await self.session.execute(
            select(TemporizadorModel).where(TemporizadorModel.casa_id == casa_id)
        )
        return [_temporizador_to_entity(m) for m in result.scalars().all()]

    async def create(self, temporizador: Temporizador) -> Temporizador:
        m = TemporizadorModel(
            id=temporizador.id, zona_id=temporizador.zona_id, casa_id=temporizador.casa_id,
            tipo=temporizador.tipo, hora_inicio=temporizador.hora_inicio,
            hora_fin=temporizador.hora_fin,
            lunes=temporizador.lunes, martes=temporizador.martes,
            miercoles=temporizador.miercoles, jueves=temporizador.jueves,
            viernes=temporizador.viernes, sabado=temporizador.sabado,
            domingo=temporizador.domingo, solo_si_oscuro=temporizador.solo_si_oscuro,
            habilitado=temporizador.habilitado,
        )
        self.session.add(m)
        await self.session.flush()
        return _temporizador_to_entity(m)

    async def update(self, temporizador: Temporizador) -> Temporizador:
        result = await self.session.execute(
            select(TemporizadorModel).where(TemporizadorModel.id == temporizador.id)
        )
        m = result.scalar_one()
        m.hora_inicio = temporizador.hora_inicio
        m.hora_fin = temporizador.hora_fin
        m.lunes = temporizador.lunes
        m.martes = temporizador.martes
        m.miercoles = temporizador.miercoles
        m.jueves = temporizador.jueves
        m.viernes = temporizador.viernes
        m.sabado = temporizador.sabado
        m.domingo = temporizador.domingo
        m.solo_si_oscuro = temporizador.solo_si_oscuro
        m.habilitado = temporizador.habilitado
        await self.session.flush()
        return _temporizador_to_entity(m)

    async def delete(self, temporizador_id: str) -> bool:
        result = await self.session.execute(
            delete(TemporizadorModel).where(TemporizadorModel.id == temporizador_id)
        )
        return result.rowcount > 0


class PostgresModoNocturnoRepository(ModoNocturnoRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_casa(self, casa_id: str) -> Optional[ModoNocturno]:
        result = await self.session.execute(
            select(ModoNocturnoModel).where(ModoNocturnoModel.casa_id == casa_id)
        )
        m = result.scalar_one_or_none()
        return _modo_nocturno_to_entity(m) if m else None

    async def upsert(self, modo: ModoNocturno) -> ModoNocturno:
        result = await self.session.execute(
            select(ModoNocturnoModel).where(ModoNocturnoModel.casa_id == modo.casa_id)
        )
        m = result.scalar_one_or_none()
        if m:
            m.habilitado = modo.habilitado
            m.deteccion_inteligente = modo.deteccion_inteligente
            m.hora_inicio = modo.hora_inicio
            m.hora_fin = modo.hora_fin
        else:
            m = ModoNocturnoModel(
                id=modo.id, casa_id=modo.casa_id, habilitado=modo.habilitado,
                deteccion_inteligente=modo.deteccion_inteligente,
                hora_inicio=modo.hora_inicio, hora_fin=modo.hora_fin,
            )
            self.session.add(m)
        await self.session.flush()
        return _modo_nocturno_to_entity(m)


class PostgresZonaNocturnaRepository(ZonaNocturnaRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_modo(self, modo_nocturno_id: str) -> list[ZonaNocturna]:
        result = await self.session.execute(
            select(ZonaNocturnaModel).where(ZonaNocturnaModel.modo_nocturno_id == modo_nocturno_id)
        )
        return [
            ZonaNocturna(
                id=_to_str(m.id), modo_nocturno_id=_to_str(m.modo_nocturno_id),
                zona_id=_to_str(m.zona_id), habilitada=m.habilitada,
            )
            for m in result.scalars().all()
        ]

    async def set_zonas(self, modo_nocturno_id: str, zonas: list[ZonaNocturna]) -> list[ZonaNocturna]:
        await self.session.execute(
            delete(ZonaNocturnaModel).where(ZonaNocturnaModel.modo_nocturno_id == modo_nocturno_id)
        )
        models = []
        for z in zonas:
            m = ZonaNocturnaModel(
                modo_nocturno_id=modo_nocturno_id,
                zona_id=z.zona_id, habilitada=z.habilitada,
            )
            self.session.add(m)
            models.append(m)
        await self.session.flush()
        return [
            ZonaNocturna(
                id=_to_str(m.id), modo_nocturno_id=_to_str(m.modo_nocturno_id),
                zona_id=_to_str(m.zona_id), habilitada=m.habilitada,
            )
            for m in models
        ]


class PostgresConsumoRepository(ConsumoRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_diario(self, casa_id: str, fecha_inicio: str, fecha_fin: str) -> list[ConsumoDiario]:
        from datetime import date as dt_date
        f_inicio = dt_date.fromisoformat(fecha_inicio)
        f_fin = dt_date.fromisoformat(fecha_fin)
        result = await self.session.execute(
            select(ConsumoDiarioModel).where(
                ConsumoDiarioModel.casa_id == casa_id,
                ConsumoDiarioModel.fecha >= f_inicio,
                ConsumoDiarioModel.fecha <= f_fin,
            ).order_by(ConsumoDiarioModel.fecha)
        )
        return [
            ConsumoDiario(
                id=_to_str(m.id), zona_id=_to_str(m.zona_id), casa_id=_to_str(m.casa_id),
                fecha=m.fecha, kwh_total=float(m.kwh_total),
                horas_encendido=float(m.horas_encendido),
                minutos_nocturno=float(m.minutos_nocturno),
            )
            for m in result.scalars().all()
        ]

    async def get_bimestral(self, casa_id: str) -> list[ConsumoBimestral]:
        result = await self.session.execute(
            select(ConsumoBimestralModel).where(
                ConsumoBimestralModel.casa_id == casa_id
            ).order_by(ConsumoBimestralModel.anio, ConsumoBimestralModel.bimestre)
        )
        return [
            ConsumoBimestral(
                id=_to_str(m.id), casa_id=_to_str(m.casa_id),
                bimestre=m.bimestre, anio=m.anio,
                kwh_total=float(m.kwh_total), costo_estimado=float(m.costo_estimado),
                horas_uso_dia=float(m.horas_uso_dia),
            )
            for m in result.scalars().all()
        ]

    async def get_horas_pico(self, casa_id: str) -> list[HorasPico]:
        result = await self.session.execute(
            select(HorasPicoModel).where(HorasPicoModel.casa_id == casa_id)
        )
        return [
            HorasPico(
                id=_to_str(m.id), zona_id=_to_str(m.zona_id), casa_id=_to_str(m.casa_id),
                hora=m.hora, dia_semana=m.dia_semana,
                minutos_promedio=float(m.minutos_promedio),
                periodo_inicio=m.periodo_inicio, periodo_fin=m.periodo_fin,
            )
            for m in result.scalars().all()
        ]

    async def get_resumen(self, casa_id: str) -> dict:
        # Aggregate today's consumption
        from datetime import date
        today = date.today()
        result = await self.session.execute(
            select(
                func.coalesce(func.sum(ConsumoDiarioModel.kwh_total), 0),
                func.coalesce(func.sum(ConsumoDiarioModel.horas_encendido), 0),
            ).where(
                ConsumoDiarioModel.casa_id == casa_id,
                ConsumoDiarioModel.fecha == today,
            )
        )
        row = result.one()
        bim = await self.session.execute(
            select(ConsumoBimestralModel).where(
                ConsumoBimestralModel.casa_id == casa_id
            ).order_by(desc(ConsumoBimestralModel.anio), desc(ConsumoBimestralModel.bimestre)).limit(1)
        )
        bim_model = bim.scalar_one_or_none()
        return {
            "consumo_hoy_kwh": float(row[0]),
            "horas_uso_hoy": float(row[1]),
            "bimestre_kwh": float(bim_model.kwh_total) if bim_model else 0,
            "bimestre_costo": float(bim_model.costo_estimado) if bim_model else 0,
            "horas_uso_dia_promedio": float(bim_model.horas_uso_dia) if bim_model else 0,
        }


class PostgresAlertaRepository(AlertaRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_casa(self, casa_id: str, limit: int = 20) -> list[Alerta]:
        result = await self.session.execute(
            select(AlertaModel).where(AlertaModel.casa_id == casa_id)
            .order_by(desc(AlertaModel.created_at)).limit(limit)
        )
        return [_alerta_to_entity(m) for m in result.scalars().all()]

    async def create(self, alerta: Alerta) -> Alerta:
        m = AlertaModel(
            casa_id=alerta.casa_id, zona_id=alerta.zona_id,
            dispositivo_id=alerta.dispositivo_id, tipo=alerta.tipo,
            severidad=alerta.severidad, titulo=alerta.titulo, mensaje=alerta.mensaje,
        )
        self.session.add(m)
        await self.session.flush()
        return _alerta_to_entity(m)

    async def mark_as_read(self, alerta_id: str) -> bool:
        result = await self.session.execute(
            select(AlertaModel).where(AlertaModel.id == alerta_id)
        )
        m = result.scalar_one_or_none()
        if m:
            m.leida = True
            await self.session.flush()
            return True
        return False


class PostgresPerfilSagemakerRepository(PerfilSagemakerRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest_by_zona(self, zona_id: str) -> Optional[PerfilSagemaker]:
        result = await self.session.execute(
            select(PerfilSagemakerModel).where(PerfilSagemakerModel.zona_id == zona_id)
            .order_by(desc(PerfilSagemakerModel.created_at)).limit(1)
        )
        m = result.scalar_one_or_none()
        if not m:
            return None
        return PerfilSagemaker(
            id=_to_str(m.id), zona_id=_to_str(m.zona_id), casa_id=_to_str(m.casa_id),
            umbral_oscuridad_sugerido=m.umbral_oscuridad_sugerido,
            tiempo_apagado_sugerido=m.tiempo_apagado_sugerido,
            patron_detectado=m.patron_detectado,
            confianza=float(m.confianza) if m.confianza else None,
            aplicado=m.aplicado,
        )

    async def create(self, perfil: PerfilSagemaker) -> PerfilSagemaker:
        m = PerfilSagemakerModel(
            zona_id=perfil.zona_id, casa_id=perfil.casa_id,
            umbral_oscuridad_sugerido=perfil.umbral_oscuridad_sugerido,
            tiempo_apagado_sugerido=perfil.tiempo_apagado_sugerido,
            horas_uso_optimas=perfil.horas_uso_optimas,
            patron_detectado=perfil.patron_detectado,
            modelo_version=perfil.modelo_version, confianza=perfil.confianza,
        )
        self.session.add(m)
        await self.session.flush()
        return perfil
