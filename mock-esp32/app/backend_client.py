"""
Cliente HTTP hacia el backend FastAPI principal.

Usa httpx.AsyncClient (no requests — bloqueante). Reintenta con backoff
exponencial en errores de red y 5xx. NO reintenta en 4xx: si el backend
nos dice "device token inválido" (401) o "request mal formado" (422),
reintentar no lo va a arreglar.
"""
import asyncio
import logging
from typing import Any, Optional

import httpx

from .config import Settings

logger = logging.getLogger(__name__)

# Backoff exponencial: 1s, 2s, 4s, 8s, 16s (cap a 30)
_BACKOFF_BASE = 1.0
_BACKOFF_MAX = 30.0
_MAX_ATTEMPTS = 5


class BackendClient:
    """Wrapper de httpx.AsyncClient con autenticación de device token.

    Reusa el cliente entre requests (pooling). Cerrar con .aclose() en el
    shutdown del lifespan.
    """

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
            headers={"X-Device-Token": settings.MOCK_CASA_ID},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Any] = None,
    ) -> Optional[httpx.Response]:
        """Ejecuta el request con reintentos para fallas transitorias.

        Reintenta:
          - httpx.RequestError (red caída, timeout, DNS, etc.)
          - status 5xx (servidor caído o overload)
        NO reintenta:
          - status 4xx (problema del request, no se arregla reintentando)

        Devuelve None si agota los reintentos.
        """
        for attempt in range(_MAX_ATTEMPTS):
            try:
                response = await self._client.request(method, path, json=json)
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

    # ── Métodos públicos ──────────────────────────────────────

    async def download_config(self) -> Optional[dict[str, Any]]:
        """GET /api/device/sync/config — descarga toda la config de la casa."""
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
        """POST /api/device/sync/heartbeat."""
        body = {
            "dispositivos": [],  # mock no trackea dispositivos individuales en F1
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
        """POST /api/device/sync/state.

        Devuelve la lista de StateUpdateResult (uno por item con status
        applied|stale|unknown_zone), o None si falló el request.
        """
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
        """POST /api/device/sync/telemetry — dummy random opcional."""
        response = await self._request_with_retry(
            "POST", "/api/device/sync/telemetry", json={"lecturas": lecturas},
        )
        return response is not None and response.status_code == 200
