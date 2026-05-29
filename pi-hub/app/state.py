"""
Cache del último state/info recibido del ESP32 vía MQTT.

El hub NO es la fuente de verdad — solo cachea lo que el ESP32 publicó
retained. Si todavía no recibió nada, las lecturas devuelven None y los
endpoints HTTP responden 503.
"""
import asyncio
from typing import Any, Optional


class LastKnownState:
    def __init__(self) -> None:
        self._state: Optional[dict[str, Any]] = None
        self._info: Optional[dict[str, Any]] = None
        self._esp32_online: Optional[bool] = None
        self._lock = asyncio.Lock()

    async def set_state(self, payload: dict[str, Any]) -> None:
        async with self._lock:
            self._state = payload

    async def get_state(self) -> Optional[dict[str, Any]]:
        async with self._lock:
            return None if self._state is None else dict(self._state)

    async def set_info(self, payload: dict[str, Any]) -> None:
        async with self._lock:
            self._info = payload

    async def get_info(self) -> Optional[dict[str, Any]]:
        async with self._lock:
            return None if self._info is None else dict(self._info)

    async def set_esp32_online(self, online: bool) -> None:
        async with self._lock:
            self._esp32_online = online

    async def get_esp32_online(self) -> Optional[bool]:
        async with self._lock:
            return self._esp32_online
