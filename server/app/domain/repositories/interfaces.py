"""
Puertos de salida (interfaces de repositorios).
El dominio define QUÉ necesita, la infraestructura define CÓMO.
"""

from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.models import (
    Owner, Casa, UsuarioCasa, Zona, ConfigZona, PermisoZona,
    Dispositivo, Temporizador, ModoNocturno, ZonaNocturna,
    ConsumoDiario, ConsumoBimestral, HorasPico, Alerta, PerfilSagemaker,
)


class OwnerRepository(ABC):
    @abstractmethod
    async def get_by_id(self, owner_id: str) -> Optional[Owner]: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Owner]: ...

    @abstractmethod
    async def create(self, owner: Owner) -> Owner: ...

    @abstractmethod
    async def update(self, owner: Owner) -> Owner: ...


class CasaRepository(ABC):
    @abstractmethod
    async def get_by_id(self, casa_id: str) -> Optional[Casa]: ...

    @abstractmethod
    async def get_by_owner(self, owner_id: str) -> list[Casa]: ...

    @abstractmethod
    async def create(self, casa: Casa) -> Casa: ...

    @abstractmethod
    async def update(self, casa: Casa) -> Casa: ...

    @abstractmethod
    async def count_by_owner(self, owner_id: str) -> int: ...


class UsuarioCasaRepository(ABC):
    @abstractmethod
    async def get_by_id(self, usuario_id: str) -> Optional[UsuarioCasa]: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[UsuarioCasa]: ...

    @abstractmethod
    async def get_by_email_and_casa(self, email: str, casa_id: str) -> Optional[UsuarioCasa]: ...

    @abstractmethod
    async def get_by_casa(self, casa_id: str) -> list[UsuarioCasa]: ...

    @abstractmethod
    async def get_by_pin_and_casa(self, pin_hash: str, casa_id: str) -> Optional[UsuarioCasa]: ...

    @abstractmethod
    async def create(self, usuario: UsuarioCasa) -> UsuarioCasa: ...

    @abstractmethod
    async def update(self, usuario: UsuarioCasa) -> UsuarioCasa: ...

    @abstractmethod
    async def delete(self, usuario_id: str) -> bool: ...


class ZonaRepository(ABC):
    @abstractmethod
    async def get_by_id(self, zona_id: str) -> Optional[Zona]: ...

    @abstractmethod
    async def get_by_casa(self, casa_id: str) -> list[Zona]: ...

    @abstractmethod
    async def create(self, zona: Zona) -> Zona: ...

    @abstractmethod
    async def update(self, zona: Zona) -> Zona: ...


class ConfigZonaRepository(ABC):
    @abstractmethod
    async def get_by_zona(self, zona_id: str) -> Optional[ConfigZona]: ...

    @abstractmethod
    async def get_all_by_casa(self, casa_id: str) -> list[ConfigZona]: ...

    @abstractmethod
    async def upsert(self, config: ConfigZona) -> ConfigZona: ...


class PermisoZonaRepository(ABC):
    @abstractmethod
    async def get_by_usuario(self, usuario_id: str) -> list[PermisoZona]: ...

    @abstractmethod
    async def get_by_zona(self, zona_id: str) -> list[PermisoZona]: ...

    @abstractmethod
    async def set_permisos(self, usuario_id: str, permisos: list[PermisoZona]) -> list[PermisoZona]: ...

    @abstractmethod
    async def delete_by_usuario(self, usuario_id: str) -> bool: ...


class DispositivoRepository(ABC):
    @abstractmethod
    async def get_by_id(self, dispositivo_id: str) -> Optional[Dispositivo]: ...

    @abstractmethod
    async def get_by_casa(self, casa_id: str) -> list[Dispositivo]: ...

    @abstractmethod
    async def get_by_zona(self, zona_id: str) -> list[Dispositivo]: ...

    @abstractmethod
    async def create(self, dispositivo: Dispositivo) -> Dispositivo: ...

    @abstractmethod
    async def update(self, dispositivo: Dispositivo) -> Dispositivo: ...

    @abstractmethod
    async def delete(self, dispositivo_id: str) -> bool: ...


class TemporizadorRepository(ABC):
    @abstractmethod
    async def get_by_id(self, temporizador_id: str) -> Optional[Temporizador]: ...

    @abstractmethod
    async def get_by_casa(self, casa_id: str) -> list[Temporizador]: ...

    @abstractmethod
    async def create(self, temporizador: Temporizador) -> Temporizador: ...

    @abstractmethod
    async def update(self, temporizador: Temporizador) -> Temporizador: ...

    @abstractmethod
    async def delete(self, temporizador_id: str) -> bool: ...


class ModoNocturnoRepository(ABC):
    @abstractmethod
    async def get_by_casa(self, casa_id: str) -> Optional[ModoNocturno]: ...

    @abstractmethod
    async def upsert(self, modo: ModoNocturno) -> ModoNocturno: ...


class ZonaNocturnaRepository(ABC):
    @abstractmethod
    async def get_by_modo(self, modo_nocturno_id: str) -> list[ZonaNocturna]: ...

    @abstractmethod
    async def set_zonas(self, modo_nocturno_id: str, zonas: list[ZonaNocturna]) -> list[ZonaNocturna]: ...


class ConsumoRepository(ABC):
    @abstractmethod
    async def get_diario(self, casa_id: str, fecha_inicio: str, fecha_fin: str) -> list[ConsumoDiario]: ...

    @abstractmethod
    async def get_bimestral(self, casa_id: str) -> list[ConsumoBimestral]: ...

    @abstractmethod
    async def get_horas_pico(self, casa_id: str) -> list[HorasPico]: ...

    @abstractmethod
    async def get_resumen(self, casa_id: str) -> dict: ...


class AlertaRepository(ABC):
    @abstractmethod
    async def get_by_casa(self, casa_id: str, limit: int = 20) -> list[Alerta]: ...

    @abstractmethod
    async def create(self, alerta: Alerta) -> Alerta: ...

    @abstractmethod
    async def mark_as_read(self, alerta_id: str) -> bool: ...


class PerfilSagemakerRepository(ABC):
    @abstractmethod
    async def get_latest_by_zona(self, zona_id: str) -> Optional[PerfilSagemaker]: ...

    @abstractmethod
    async def create(self, perfil: PerfilSagemaker) -> PerfilSagemaker: ...
