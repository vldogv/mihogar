"""
Inyección de dependencias — Conecta los puertos con los adaptadores.
FastAPI Depends() resuelve estas funciones para cada request.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

from app.domain.repositories.interfaces import (
    OwnerRepository, CasaRepository, UsuarioCasaRepository, ZonaRepository,
    ConfigZonaRepository, PermisoZonaRepository, DispositivoRepository,
    TemporizadorRepository, ModoNocturnoRepository, ZonaNocturnaRepository,
    ConsumoRepository, AlertaRepository, PerfilSagemakerRepository,
)
from app.infrastructure.persistence.postgres.repositories import (
    PostgresOwnerRepository, PostgresCasaRepository, PostgresUsuarioCasaRepository,
    PostgresZonaRepository, PostgresConfigZonaRepository, PostgresPermisoZonaRepository,
    PostgresDispositivoRepository, PostgresTemporizadorRepository,
    PostgresModoNocturnoRepository, PostgresZonaNocturnaRepository,
    PostgresConsumoRepository, PostgresAlertaRepository, PostgresPerfilSagemakerRepository,
)


async def get_owner_repo(db: AsyncSession = Depends(get_db)) -> OwnerRepository:
    return PostgresOwnerRepository(db)


async def get_casa_repo(db: AsyncSession = Depends(get_db)) -> CasaRepository:
    return PostgresCasaRepository(db)


async def get_usuario_repo(db: AsyncSession = Depends(get_db)) -> UsuarioCasaRepository:
    return PostgresUsuarioCasaRepository(db)


async def get_zona_repo(db: AsyncSession = Depends(get_db)) -> ZonaRepository:
    return PostgresZonaRepository(db)


async def get_config_zona_repo(db: AsyncSession = Depends(get_db)) -> ConfigZonaRepository:
    return PostgresConfigZonaRepository(db)


async def get_permiso_repo(db: AsyncSession = Depends(get_db)) -> PermisoZonaRepository:
    return PostgresPermisoZonaRepository(db)


async def get_dispositivo_repo(db: AsyncSession = Depends(get_db)) -> DispositivoRepository:
    return PostgresDispositivoRepository(db)


async def get_temporizador_repo(db: AsyncSession = Depends(get_db)) -> TemporizadorRepository:
    return PostgresTemporizadorRepository(db)


async def get_modo_nocturno_repo(db: AsyncSession = Depends(get_db)) -> ModoNocturnoRepository:
    return PostgresModoNocturnoRepository(db)


async def get_zona_nocturna_repo(db: AsyncSession = Depends(get_db)) -> ZonaNocturnaRepository:
    return PostgresZonaNocturnaRepository(db)


async def get_consumo_repo(db: AsyncSession = Depends(get_db)) -> ConsumoRepository:
    return PostgresConsumoRepository(db)


async def get_alerta_repo(db: AsyncSession = Depends(get_db)) -> AlertaRepository:
    return PostgresAlertaRepository(db)


async def get_perfil_repo(db: AsyncSession = Depends(get_db)) -> PerfilSagemakerRepository:
    return PostgresPerfilSagemakerRepository(db)
