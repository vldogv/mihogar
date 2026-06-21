"""
Cliente HTTP del Pi-hub hacia el backend FastAPI principal (EC2).

Mismo patrón que mock-esp32/app/backend_client.py: httpx.AsyncClient,
reintentos con backoff exponencial en errores de red/5xx, sin reintento
en 4xx. Header X-Device-Token = CASA_ID (este es el cliente real, no el
simulador — por eso CASA_ID y no MOCK_CASA_ID).

check_health() usa GET /api/health.

get_commands(): contrato confirmado contra
server/app/interfaces/api/routes/device_sync_routes.py — devuelve
list[PendingCommand] directo (id, zona_id, comando, parametros, created_at).
HOY el endpoint es un stub que siempre regresa [] — el diseño actual no
lo necesita, ya que el ESP32 detecta cambios comparando GET /config
contra su copia local. No existe endpoint de ack; no se llama ninguno.
"""
import asyncio
import logging
from typing import Any, Optional

import httpx

from .config import Settings

logger = logging.getLogger(__name__)

_BACKOFF_BASE = 1.0
_BACKOFF_MAX = 30.0
_MAX_ATTEMPTS = 5


class BackendClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.BACKEND_URL,
            timeout=httpx.Timeout(
                connect=5.0,
                read=settings.HTTP_TIMEOUT_SECONDS,
                write=settings.HTTP_TIMEOUT_SECONDS,
                pool=5.0,
            ),
            headers={"X-Device-Token": settings.CASA_ID},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request_with_retry(
        self, method: str, path: str, *, json: Optional[Any] = None, params: Optional[dict] = None,
    ) -> Optional[httpx.Response]:
        for attempt in range(_MAX_ATTEMPTS):
            try:
                response = await self._client.request(method, path, json=json, params=params)
            except httpx.RequestError as exc:
                wait = min(_BACKOFF_BASE * (2 ** attempt), _BACKOFF_MAX)
                logger.warning(
                    "Backend %s %s falló (%s). Reintento %d/%d en %.1fs",
                    method, path, exc.__class__.__name__,
                    attempt + 1, _MAX_ATTEMPTS, wait,
                )
                await asyncio.sleep(wait)
                continue
            if 500 <= response.status_code < 600:
                wait = min(_BACKOFF_BASE * (2 ** attempt), _BACKOFF_MAX)
                logger.warning(
                    "Backend %s %s devolvió %d. Reintento %d/%d en %.1fs",
                    method, path, response.status_code,
                    attempt + 1, _MAX_ATTEMPTS, wait,
                )
                await asyncio.sleep(wait)
                continue
            return response
        logger.error(
            "Backend %s %s agotó reintentos (%d intentos)",
            method, path, _MAX_ATTEMPTS,
        )
        return None

    async def check_health(self) -> bool:
        """GET /api/health — un solo intento, sin retry."""
        try:
            response = await self._client.get("/api/health", timeout=5.0)
            return response.status_code == 200
        except httpx.RequestError:
            return False

    async def download_config(self) -> Optional[dict[str, Any]]:
        response = await self._request_with_retry("GET", "/api/device/sync/config")
        if response is None:
            return None
        if response.status_code != 200:
            logger.error(
                "download_config: status %d body=%s",
                response.status_code, response.text[:200],
            )
            return None
        return response.json()

    async def post_heartbeat(self) -> bool:
        body = {
            "dispositivos": [],
            "uptime_seconds": None,
            "free_memory_kb": None,
            "wifi_rssi": None,
        }
        response = await self._request_with_retry(
            "POST", "/api/device/sync/heartbeat", json=body,
        )
        return response is not None and response.status_code == 200

    async def post_state_batch(
        self, updates: list[dict[str, Any]]
    ) -> Optional[list[dict[str, Any]]]:
        response = await self._request_with_retry(
            "POST", "/api/device/sync/state", json={"updates": updates},
        )
        if response is None:
            return None
        if response.status_code != 200:
            logger.error(
                "post_state_batch: status %d body=%s",
                response.status_code, response.text[:200],
            )
            return None
        return response.json()

    async def post_telemetry(self, lecturas: list[dict[str, Any]]) -> bool:
        response = await self._request_with_retry(
            "POST", "/api/device/sync/telemetry", json={"lecturas": lecturas},
        )
        return response is not None and response.status_code == 200

    async def post_alerts(self, alertas: list[dict[str, Any]]) -> bool:
        response = await self._request_with_retry(
            "POST", "/api/device/sync/alerts", json={"alertas": alertas},
        )
        return response is not None and response.status_code == 200

    async def get_commands(self, since: Optional[str] = None) -> Optional[list[dict[str, Any]]]:
        """GET /api/device/sync/commands.

        Schema confirmado: lista directa de PendingCommand
        (id, zona_id, comando, parametros, created_at). HOY es un stub
        que siempre regresa [] — ver docstring del módulo.
        """
        params = {"since": since} if since else None
        response = await self._request_with_retry("GET", "/api/device/sync/commands", params=params)
        if response is None:
            return None
        if response.status_code != 200:
            logger.error(
                "get_commands: status %d body=%s",
                response.status_code, response.text[:200],
            )
            return None
        return response.json()
