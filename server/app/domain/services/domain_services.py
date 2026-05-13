"""
Servicios de dominio - Reglas de negocio puras.
No dependen de frameworks ni de infraestructura.
"""

from app.domain.entities.models import (
    RolUsuario, UsuarioCasa, ConfigZona, ModoZona,
)


class ZonaDomainService:
    """Reglas de negocio para zonas."""

    @staticmethod
    def deberia_encender(config: ConfigZona) -> bool:
        if config.modo == ModoZona.MANUAL:
            return config.encendida

        if config.modo == ModoZona.AUTOMATICO:
            if not config.auto_encender:
                return False
            luz_baja = (
                config.luz_ambiente_actual is not None
                and config.luz_ambiente_actual < config.umbral_oscuridad
            )
            return luz_baja and config.movimiento_detectado

        return config.encendida

    @staticmethod
    def puede_usuario_controlar_zona(
        usuario: UsuarioCasa, zona_id: str, permisos_zona_ids: list[str]
    ) -> bool:
        if usuario.rol in (RolUsuario.ADMINISTRADOR, RolUsuario.ENCARGADO):
            return True
        return zona_id in permisos_zona_ids

    @staticmethod
    def puede_usuario_configurar_zona(
        usuario: UsuarioCasa, zona_id: str, permisos_config_ids: list[str]
    ) -> bool:
        if usuario.rol == RolUsuario.ADMINISTRADOR:
            return True
        if usuario.rol == RolUsuario.ENCARGADO:
            return True
        return zona_id in permisos_config_ids


class PermisosService:
    """Tabla de permisos por rol."""

    PERMISOS = {
        RolUsuario.ADMINISTRADOR: {
            "controlar_luces", "configurar_temporizadores", "ver_consumo",
            "configurar_sensores", "gestionar_usuarios", "gestionar_dispositivos",
            "config_wifi", "ver_alertas",
        },
        RolUsuario.ENCARGADO: {
            "controlar_luces", "configurar_temporizadores", "ver_consumo",
            "configurar_sensores", "ver_alertas",
        },
        RolUsuario.USUARIO: {
            "controlar_luces",
        },
    }

    @classmethod
    def tiene_permiso(cls, rol: RolUsuario, permiso: str) -> bool:
        return permiso in cls.PERMISOS.get(rol, set())

    @classmethod
    def get_permisos(cls, rol: RolUsuario) -> set[str]:
        return cls.PERMISOS.get(rol, set())
