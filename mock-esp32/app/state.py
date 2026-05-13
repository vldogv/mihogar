"""
Estado in-memory del mock. Refleja lo que el backend devolvió en el
último /device/sync/config exitoso.

Concurrency: usar `async with state.lock` antes de leer o mutar.
Los métodos públicos ya toman el lock por dentro.
"""
import asyncio
import hashlib
import json
from typing import Any, Optional


class InMemoryState:
    def __init__(self) -> None:
        self.casa_id: Optional[str] = None
        self.casa_nombre: Optional[str] = None
        self.last_config_sync_at: Optional[str] = None  # ISO 8601 del backend
        self.last_config_hash: Optional[str] = None
        self.zonas: list[dict[str, Any]] = []
        self.temporizadores: list[dict[str, Any]] = []
        self.dispositivos: list[dict[str, Any]] = []
        self.modo_nocturno: Optional[dict[str, Any]] = None
        self.ml_profiles: list[dict[str, Any]] = []
        self.lock = asyncio.Lock()

    async def replace_config(self, payload: dict[str, Any]) -> bool:
        """Reemplaza el estado con el payload del backend.

        Devuelve True si el contenido cambió respecto al último poll
        (compara hash excluyendo el `timestamp` para que la rotación
        del timestamp no falsee cambios).
        """
        new_hash = self._hash_payload(payload)
        async with self.lock:
            if new_hash == self.last_config_hash:
                # Actualizamos el timestamp local pero no marcamos como cambio
                self.last_config_sync_at = payload.get("timestamp")
                return False
            self.casa_id = payload.get("casa_id")
            self.casa_nombre = payload.get("casa_nombre")
            self.last_config_sync_at = payload.get("timestamp")
            self.last_config_hash = new_hash
            self.zonas = payload.get("zonas", [])
            self.temporizadores = payload.get("temporizadores", [])
            self.dispositivos = payload.get("dispositivos", [])
            self.modo_nocturno = payload.get("modo_nocturno")
            self.ml_profiles = payload.get("ml_profiles", [])
            return True

    async def get_zona(self, zona_id: str) -> Optional[dict[str, Any]]:
        async with self.lock:
            for z in self.zonas:
                if z.get("zona_id") == zona_id:
                    return dict(z)  # copia defensiva
        return None

    async def update_local_zona(
        self,
        zona_id: str,
        encendida: Optional[bool] = None,
        modo: Optional[str] = None,
    ) -> bool:
        """Actualización optimista local tras un applied del backend.

        No es la fuente de verdad — la próxima descarga de /config la
        sobrescribe. Sirve para que GET /mock/state refleje el cambio
        sin esperar al siguiente poll.
        """
        async with self.lock:
            for z in self.zonas:
                if z.get("zona_id") == zona_id:
                    if encendida is not None:
                        z["encendida"] = encendida
                    if modo is not None:
                        z["modo"] = modo
                    return True
            return False

    @staticmethod
    def _hash_payload(payload: dict[str, Any]) -> str:
        # Excluye `timestamp`: rota en cada poll sin que cambie nada real
        filtered = {k: v for k, v in payload.items() if k != "timestamp"}
        return hashlib.sha256(
            json.dumps(filtered, sort_keys=True, default=str).encode()
        ).hexdigest()
