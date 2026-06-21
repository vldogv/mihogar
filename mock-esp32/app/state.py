"""
Estado in-memory del mock. Refleja lo que el backend devolvió en el
último /device/sync/config exitoso, o el seed inicial si se cargó por
MOCK_SEED_FILE.

Concurrency: usar `async with state.lock` antes de leer o mutar.
Los métodos públicos ya toman el lock por dentro.
"""
import asyncio
import hashlib
import json
from datetime import datetime, timezone
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
        # Info del "device" — leída del seed si está, expuesta vía MQTT info topic.
        self.info: Optional[dict[str, Any]] = None
        self.lock = asyncio.Lock()

    async def replace_config(self, payload: dict[str, Any]) -> bool:
        """Reemplaza el estado con el payload del backend (o seed).

        Devuelve True si el contenido cambió respecto al último poll
        (compara hash excluyendo el `timestamp` para que la rotación
        del timestamp no falsee cambios).

        Si el payload trae `info`, también la guarda (caso seed file).
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
            # info solo viene del seed (el backend principal no la manda)
            if "info" in payload:
                self.info = payload["info"]
            return True

    async def try_apply_command(
        self,
        zona_id: str,
        *,
        encendida: Optional[bool] = None,
        modo: Optional[str] = None,
        client_timestamp: Optional[str] = None,
    ) -> tuple[str, Optional[str]]:
        """Aplica una operación a una zona con LWW.

        Devuelve `(status, server_timestamp)`:
          - ("applied", ts)       — el cambio se aplicó y se actualizó updated_at
          - ("stale", ts)         — client_timestamp <= updated_at de la zona, descartado
          - ("unknown_zone", ts)  — la zona no está en el estado local

        `ts` siempre es el momento del ESP32 (now). No es null nunca.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        async with self.lock:
            zona = next((z for z in self.zonas if z.get("zona_id") == zona_id), None)
            if zona is None:
                return "unknown_zone", now_iso

            prev_updated_at = zona.get("updated_at")
            if (
                client_timestamp is not None
                and prev_updated_at is not None
                and client_timestamp <= prev_updated_at
            ):
                return "stale", now_iso

            if encendida is not None:
                zona["encendida"] = encendida
            if modo is not None:
                zona["modo"] = modo
            # Si vino client_timestamp lo guardamos como updated_at (espejo del
            # comportamiento del backend). Si no vino, usamos now.
            zona["updated_at"] = client_timestamp or now_iso
            return "applied", now_iso

    async def apply_scene_all(self, encendida: bool, client_timestamp: Optional[str]) -> tuple[str, list[str]]:
        """Aplica encender/apagar a todas las zonas. Devuelve (server_ts, zonas_afectadas).

        Atómico bajo el lock. Cada zona que pasaba el LWW gate cuenta como afectada.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        afectadas: list[str] = []
        async with self.lock:
            for zona in self.zonas:
                prev_updated_at = zona.get("updated_at")
                if (
                    client_timestamp is not None
                    and prev_updated_at is not None
                    and client_timestamp <= prev_updated_at
                ):
                    continue
                zona["encendida"] = encendida
                zona["updated_at"] = client_timestamp or now_iso
                afectadas.append(zona["zona_id"])
        return now_iso, afectadas

    def state_payload(self) -> dict[str, Any]:
        """Snapshot del state-publicable en MQTT (shape espejo de GET /state).

        IMPORTANTE: NO toma el lock — el caller es responsable. Usado por el
        mqtt_loop dentro del mismo lock que aplicó el cambio.
        """
        return {
            "casa_id": self.casa_id,
            "casa_nombre": self.casa_nombre,
            "server_timestamp": datetime.now(timezone.utc).isoformat(),
            "zonas": list(self.zonas),
            "dispositivos": list(self.dispositivos),
        }

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
