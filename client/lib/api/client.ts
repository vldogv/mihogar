import { markOffline, markOnline } from "@/lib/offline/connectivity"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

const TOKEN_KEY = "mihogar_token"

export function getToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

class ApiClientError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = "ApiClientError"
    this.status = status
  }
}

class NetworkError extends Error {
  cause?: unknown
  constructor(message = "Sin conexión con el servidor", cause?: unknown) {
    super(message)
    this.name = "NetworkError"
    this.cause = cause
  }
}

export { ApiClientError, NetworkError }

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken()

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  let res: Response
  try {
    res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    })
  } catch (err) {
    markOffline()
    throw new NetworkError("Sin conexión con el servidor", err)
  }

  markOnline()

  if (!res.ok) {
    if (res.status === 401) {
      removeToken()
      if (typeof window !== "undefined") {
        window.location.href = "/login"
      }
      throw new ApiClientError("Sesión expirada", 401)
    }

    let message = "Error del servidor"
    try {
      const err = await res.json()
      message = err.detail || message
    } catch {
      message = res.statusText || message
    }

    throw new ApiClientError(message, res.status)
  }

  return res.json() as Promise<T>
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),
  post: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  put: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, { method: "PUT", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(endpoint: string) =>
    request<T>(endpoint, { method: "DELETE" }),
}
