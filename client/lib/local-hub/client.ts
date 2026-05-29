import type {
  LocalCommandResponse,
  LocalHealth,
  LocalInfo,
  LocalModeRequest,
  LocalSceneResponse,
  LocalState,
  LocalToggleRequest,
} from "./types"

// Cliente HTTP del pi-hub (Fase 6). NO usa el wrapper @/lib/api/client
// porque ése apunta al cloud (Bearer token, /api prefix, markOnline emitter).
// El pi-hub es LAN sin auth y vive en un baseURL distinto.

export class LocalHubError extends Error {
  status: number
  detail: string
  constructor(message: string, status: number, detail: string) {
    super(message)
    this.name = "LocalHubError"
    this.status = status
    this.detail = detail
  }
}

export class LocalHubTimeoutError extends Error {
  constructor(message = "ack timeout") {
    super(message)
    this.name = "LocalHubTimeoutError"
  }
}

export class LocalHubNetworkError extends Error {
  cause?: unknown
  constructor(message = "Pi-hub inalcanzable", cause?: unknown) {
    super(message)
    this.name = "LocalHubNetworkError"
    this.cause = cause
  }
}

const PROBE_TIMEOUT_MS = 1500
const COMMAND_TIMEOUT_MS = 5000

async function fetchWithTimeout(
  url: string,
  init: RequestInit,
  timeoutMs: number,
): Promise<Response> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    return await fetch(url, { ...init, signal: controller.signal })
  } catch (err) {
    if ((err as { name?: string }).name === "AbortError") {
      throw new LocalHubNetworkError("Timeout contactando al pi-hub", err)
    }
    throw new LocalHubNetworkError("Pi-hub inalcanzable", err)
  } finally {
    clearTimeout(timer)
  }
}

async function parseOrThrow<T>(res: Response): Promise<T> {
  if (res.ok) return (await res.json()) as T
  if (res.status === 504) {
    throw new LocalHubTimeoutError("ack timeout")
  }
  let detail = res.statusText || "Error del pi-hub"
  try {
    const body = await res.json()
    if (body?.detail) detail = body.detail
  } catch {
    /* body no es JSON */
  }
  throw new LocalHubError(detail, res.status, detail)
}

function joinURL(baseURL: string, path: string): string {
  const base = baseURL.replace(/\/+$/, "")
  const rel = path.startsWith("/") ? path : `/${path}`
  return `${base}${rel}`
}

export const localHub = {
  health: async (baseURL: string): Promise<LocalHealth> => {
    const res = await fetchWithTimeout(
      joinURL(baseURL, "/health"),
      { method: "GET", headers: { Accept: "application/json" } },
      PROBE_TIMEOUT_MS,
    )
    return parseOrThrow<LocalHealth>(res)
  },

  info: async (baseURL: string): Promise<LocalInfo> => {
    const res = await fetchWithTimeout(
      joinURL(baseURL, "/info"),
      { method: "GET", headers: { Accept: "application/json" } },
      PROBE_TIMEOUT_MS,
    )
    return parseOrThrow<LocalInfo>(res)
  },

  state: async (baseURL: string): Promise<LocalState> => {
    const res = await fetchWithTimeout(
      joinURL(baseURL, "/state"),
      { method: "GET", headers: { Accept: "application/json" } },
      COMMAND_TIMEOUT_MS,
    )
    return parseOrThrow<LocalState>(res)
  },

  zoneToggle: async (
    baseURL: string,
    zonaId: string,
    body: LocalToggleRequest,
  ): Promise<LocalCommandResponse> => {
    const res = await fetchWithTimeout(
      joinURL(baseURL, `/zones/${zonaId}/toggle`),
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
      COMMAND_TIMEOUT_MS,
    )
    return parseOrThrow<LocalCommandResponse>(res)
  },

  zoneMode: async (
    baseURL: string,
    zonaId: string,
    body: LocalModeRequest,
  ): Promise<LocalCommandResponse> => {
    const res = await fetchWithTimeout(
      joinURL(baseURL, `/zones/${zonaId}/mode`),
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
      COMMAND_TIMEOUT_MS,
    )
    return parseOrThrow<LocalCommandResponse>(res)
  },

  sceneAllOn: async (
    baseURL: string,
    body: { client_id?: string; client_timestamp?: string },
  ): Promise<LocalSceneResponse> => {
    const res = await fetchWithTimeout(
      joinURL(baseURL, "/scene/all-on"),
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
      COMMAND_TIMEOUT_MS,
    )
    return parseOrThrow<LocalSceneResponse>(res)
  },

  sceneAllOff: async (
    baseURL: string,
    body: { client_id?: string; client_timestamp?: string },
  ): Promise<LocalSceneResponse> => {
    const res = await fetchWithTimeout(
      joinURL(baseURL, "/scene/all-off"),
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
      COMMAND_TIMEOUT_MS,
    )
    return parseOrThrow<LocalSceneResponse>(res)
  },
}
