#!/bin/bash
# ══════════════════════════════════════════════════════════════
# Mi Hogar - Instalar archivos de conexión API en el frontend
# Ejecutar desde la raíz del proyecto: ./install-api.sh
# ══════════════════════════════════════════════════════════════

FRONT="client"

echo "🔌 Instalando conexión API en $FRONT..."

# 1. API Client
echo "  → lib/api/client.ts"
mkdir -p "$FRONT/lib/api"

cat > "$FRONT/lib/api/client.ts" << 'ENDOFFILE'
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

const TOKEN_KEY = "mihogar_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

class ApiClientError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
  }
}

export { ApiClientError };

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    if (res.status === 401) {
      removeToken();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
      throw new ApiClientError("Sesión expirada", 401);
    }

    let message = "Error del servidor";
    try {
      const err = await res.json();
      message = err.detail || message;
    } catch {
      message = res.statusText || message;
    }

    throw new ApiClientError(message, res.status);
  }

  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),
  post: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  put: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, { method: "PUT", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(endpoint: string) =>
    request<T>(endpoint, { method: "DELETE" }),
};
ENDOFFILE

# 2. Auth Context (reemplaza los mocks)
echo "  → lib/auth/auth-context.tsx (reemplazando mocks)"

cat > "$FRONT/lib/auth/auth-context.tsx" << 'ENDOFFILE'
"use client"

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react"
import type { AuthSession, Casa, Rol, UserWithHouses } from "@/types/auth"
import { api, setToken, getToken, removeToken } from "@/lib/api/client"

interface LoginOwnerResponse {
  access_token: string
  token_type: string
  rol: string
  nombre: string
  casas: { id: string; nombre: string; direccion: string | null; rol: string }[]
}

interface LoginUserResponse {
  access_token: string
  token_type: string
  rol: string
  nombre: string
  casa_id: string | null
  requires_casa_selection: boolean
}

interface SelectCasaResponse {
  access_token: string
  token_type: string
  rol: string
  nombre: string
  casa_id: string
}

interface AuthContextType {
  session: AuthSession | null
  user: UserWithHouses | null
  activeCasa: Casa | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<{ success: boolean; houses: (Casa & { rol: Rol })[] }>
  selectHouse: (casaId: string, rol: Rol) => void
  logout: () => void
  changeHouse: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

const SESSION_KEY = "mihogar_session"
const USER_KEY = "mihogar_user"

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(null)
  const [user, setUser] = useState<UserWithHouses | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    try {
      const storedSession = localStorage.getItem(SESSION_KEY)
      const storedUser = localStorage.getItem(USER_KEY)
      const storedToken = getToken()

      if (storedUser) setUser(JSON.parse(storedUser))
      if (storedSession && storedToken) setSession(JSON.parse(storedSession))
    } catch {
      localStorage.removeItem(SESSION_KEY)
      localStorage.removeItem(USER_KEY)
      removeToken()
    } finally {
      setIsLoading(false)
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    try {
      const data = await api.post<LoginOwnerResponse | LoginUserResponse>(
        "/auth/login",
        { email, password }
      )

      setToken(data.access_token)

      if ("casas" in data && data.casas) {
        const ownerData = data as LoginOwnerResponse
        const houses: (Casa & { rol: Rol })[] = ownerData.casas.map((c) => ({
          id: c.id,
          nombre: c.nombre,
          direccion: c.direccion || "",
          rol: "propietario" as Rol,
        }))

        const userData: UserWithHouses = {
          id: "",
          nombre: ownerData.nombre,
          email,
          activo: true,
          casas: houses,
        }

        setUser(userData)
        localStorage.setItem(USER_KEY, JSON.stringify(userData))
        return { success: true, houses }
      }

      const userData = data as LoginUserResponse
      const house: Casa & { rol: Rol } = {
        id: userData.casa_id || "",
        nombre: "",
        direccion: "",
        rol: userData.rol as Rol,
      }

      const userInfo: UserWithHouses = {
        id: "",
        nombre: userData.nombre,
        email,
        activo: true,
        casas: [house],
      }

      setUser(userInfo)
      localStorage.setItem(USER_KEY, JSON.stringify(userInfo))
      return { success: true, houses: [house] }
    } catch (err) {
      console.error("Login error:", err)
      return { success: false, houses: [] }
    }
  }, [])

  const selectHouse = useCallback(
    async (casaId: string, rol: Rol) => {
      try {
        const data = await api.post<SelectCasaResponse>("/auth/select-casa", {
          casa_id: casaId,
        })

        setToken(data.access_token)

        let currentUser = user
        if (!currentUser) {
          const storedUser = localStorage.getItem(USER_KEY)
          if (!storedUser) return
          currentUser = JSON.parse(storedUser)
        }

        const newSession: AuthSession = {
          usuario_id: currentUser!.id || data.nombre,
          casa_id_activa: casaId,
          rol: (data.rol || rol) as Rol,
        }

        setSession(newSession)
        localStorage.setItem(SESSION_KEY, JSON.stringify(newSession))
      } catch (err) {
        console.error("Select house error:", err)
        let currentUser = user
        if (!currentUser) {
          const storedUser = localStorage.getItem(USER_KEY)
          if (!storedUser) return
          currentUser = JSON.parse(storedUser)
        }

        const newSession: AuthSession = {
          usuario_id: currentUser!.id,
          casa_id_activa: casaId,
          rol,
        }

        setSession(newSession)
        localStorage.setItem(SESSION_KEY, JSON.stringify(newSession))
      }
    },
    [user]
  )

  const logout = useCallback(() => {
    setSession(null)
    setUser(null)
    localStorage.removeItem(SESSION_KEY)
    localStorage.removeItem(USER_KEY)
    removeToken()
    window.location.href = "/login"
  }, [])

  const changeHouse = useCallback(() => {
    setSession(null)
    localStorage.removeItem(SESSION_KEY)
    window.location.href = "/select-house"
  }, [])

  const activeCasa = user?.casas.find((c) => c.id === session?.casa_id_activa) || null

  return (
    <AuthContext.Provider
      value={{
        session, user, activeCasa, isLoading,
        isAuthenticated: !!session,
        login, selectHouse, logout, changeHouse,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error("useAuth must be used within an AuthProvider")
  return context
}
ENDOFFILE

# 3. Services
echo "  → lib/services/ (panel, horarios, consumo, dispositivos, usuarios)"
mkdir -p "$FRONT/lib/services"

cat > "$FRONT/lib/services/panel.ts" << 'ENDOFFILE'
import { api } from "@/lib/api/client"

export interface ZonaConfig {
  zona_id: string; encendida: boolean; modo: string; umbral_oscuridad: number
  auto_encender: boolean; tiempo_apagado_auto: number
  luz_ambiente_actual: number | null; movimiento_detectado: boolean; temperatura_actual: number | null
}

export interface Zona { id: string; nombre: string; tipo: string; icono: string | null; orden: number }
export interface ZonaConConfig { zona: Zona; config: ZonaConfig | null }
export interface PanelData { zonas_activas: number; zonas_total: number; zonas: ZonaConConfig[] }
interface Msg { message: string; success: boolean }

export const panelService = {
  getPanel: (casaId: string) => api.get<PanelData>(`/casas/${casaId}/panel`),
  getZonas: (casaId: string) => api.get<Zona[]>(`/casas/${casaId}/zonas`),
  getZonaDetail: (zonaId: string) => api.get<ZonaConConfig>(`/zonas/${zonaId}`),
  toggleZona: (zonaId: string, encendida: boolean) => api.put<Msg>(`/zonas/${zonaId}/toggle`, { encendida }),
  cambiarModo: (zonaId: string, modo: string) => api.put<Msg>(`/zonas/${zonaId}/modo`, { modo }),
  updateConfigZona: (zonaId: string, config: { umbral_oscuridad?: number; auto_encender?: boolean; tiempo_apagado_auto?: number }) =>
    api.put<Msg>(`/zonas/${zonaId}/config`, config),
  encenderTodo: (casaId: string) => api.post<Msg>(`/casas/${casaId}/encender-todo`),
  apagarTodo: (casaId: string) => api.post<Msg>(`/casas/${casaId}/apagar-todo`),
}
ENDOFFILE

cat > "$FRONT/lib/services/horarios.ts" << 'ENDOFFILE'
import { api } from "@/lib/api/client"

export interface Temporizador {
  id: string; zona_id: string; zona_nombre: string | null; tipo: string
  hora_inicio: string; hora_fin: string
  dias: { lunes: boolean; martes: boolean; miercoles: boolean; jueves: boolean; viernes: boolean; sabado: boolean; domingo: boolean }
  solo_si_oscuro: boolean; habilitado: boolean
}
export interface TemporizadorCreate {
  zona_id: string; tipo?: string; hora_inicio: string; hora_fin: string
  lunes?: boolean; martes?: boolean; miercoles?: boolean; jueves?: boolean; viernes?: boolean; sabado?: boolean; domingo?: boolean
  solo_si_oscuro?: boolean
}
export interface ZonaNocturna { zona_id: string; zona_nombre: string | null; zona_tipo: string | null; habilitada: boolean }
export interface ModoNocturno { habilitado: boolean; deteccion_inteligente: boolean; hora_inicio: string; hora_fin: string; zonas: ZonaNocturna[] }
interface Msg { message: string; success: boolean }

export const horariosService = {
  getTemporizadores: (casaId: string) => api.get<Temporizador[]>(`/casas/${casaId}/temporizadores`),
  createTemporizador: (casaId: string, data: TemporizadorCreate) => api.post<Temporizador>(`/casas/${casaId}/temporizadores`, data),
  updateTemporizador: (id: string, data: Partial<TemporizadorCreate> & { habilitado?: boolean }) => api.put<Temporizador>(`/temporizadores/${id}`, data),
  deleteTemporizador: (id: string) => api.delete<Msg>(`/temporizadores/${id}`),
  getModoNocturno: (casaId: string) => api.get<ModoNocturno>(`/casas/${casaId}/modo-nocturno`),
  updateModoNocturno: (casaId: string, data: Partial<ModoNocturno>) => api.put<Msg>(`/casas/${casaId}/modo-nocturno`, data),
}
ENDOFFILE

cat > "$FRONT/lib/services/consumo.ts" << 'ENDOFFILE'
import { api } from "@/lib/api/client"

export interface ConsumoResumen { consumo_hoy_kwh: number; horas_uso_hoy: number; bimestre_kwh: number; bimestre_costo: number; horas_uso_dia_promedio: number; corte_cfe_dia: number }
export interface ConsumoDiario { zona_id: string; zona_nombre: string | null; fecha: string; kwh_total: number; horas_encendido: number }
export interface HorasPico { zona_id: string; zona_nombre: string | null; hora: number; dia_semana: number; minutos_promedio: number }
export interface ConsumoBimestral { bimestre: number; anio: number; kwh_total: number; costo_estimado: number; horas_uso_dia: number }
export interface Alerta { id: string; tipo: string; severidad: string; titulo: string; mensaje: string; leida: boolean; created_at: string | null }
interface Msg { message: string; success: boolean }

export const consumoService = {
  getResumen: (casaId: string) => api.get<ConsumoResumen>(`/casas/${casaId}/consumo/resumen`),
  getDiario: (casaId: string, desde: string, hasta: string) => api.get<ConsumoDiario[]>(`/casas/${casaId}/consumo/diario?desde=${desde}&hasta=${hasta}`),
  getHorasPico: (casaId: string) => api.get<HorasPico[]>(`/casas/${casaId}/consumo/horas-pico`),
  getBimestral: (casaId: string) => api.get<ConsumoBimestral[]>(`/casas/${casaId}/consumo/bimestral`),
  getAlertas: (casaId: string, limit = 20) => api.get<Alerta[]>(`/casas/${casaId}/alertas?limit=${limit}`),
  marcarAlertaLeida: (alertaId: string) => api.put<Msg>(`/alertas/${alertaId}/leer`),
}
ENDOFFILE

cat > "$FRONT/lib/services/dispositivos.ts" << 'ENDOFFILE'
import { api } from "@/lib/api/client"

export interface Dispositivo { id: string; zona_id: string; zona_nombre: string | null; tipo: string; nombre: string; mac_address: string | null; ip_local: string | null; firmware_version: string | null; estado: string }
export interface DispositivoCreate { zona_id: string; tipo: string; nombre: string; mac_address?: string; ip_local?: string }
export interface WifiConfig { wifi_ssid: string; wifi_password: string; nombre_instalacion?: string; zona_horaria?: string; email_alertas?: string }
interface Msg { message: string; success: boolean }

export const dispositivosService = {
  getDispositivos: (casaId: string) => api.get<Dispositivo[]>(`/casas/${casaId}/dispositivos`),
  createDispositivo: (casaId: string, data: DispositivoCreate) => api.post<Dispositivo>(`/casas/${casaId}/dispositivos`, data),
  deleteDispositivo: (id: string) => api.delete<Msg>(`/dispositivos/${id}`),
  saveWifiConfig: (casaId: string, data: WifiConfig) => api.post<Msg>(`/casas/${casaId}/wifi-config`, data),
}
ENDOFFILE

cat > "$FRONT/lib/services/usuarios.ts" << 'ENDOFFILE'
import { api } from "@/lib/api/client"

export interface PermisoZona { zona_id: string; zona_nombre: string | null; puede_controlar: boolean; puede_configurar: boolean }
export interface Usuario { id: string; nombre: string; email: string | null; rol: string; metodo_acceso: string; zonas_permitidas: string[]; permisos: PermisoZona[] }
export interface UsuarioCreate { nombre: string; email?: string; password?: string; pin?: string; rol?: string; zonas_permitidas?: string[] }
export interface UsuarioUpdate { nombre?: string; email?: string; rol?: string; zonas_permitidas?: string[] }
export interface PermisosRol { administrador: string[]; encargado: string[]; usuario: string[] }
interface Msg { message: string; success: boolean }

export const usuariosService = {
  getUsuarios: (casaId: string) => api.get<Usuario[]>(`/casas/${casaId}/usuarios`),
  createUsuario: (casaId: string, data: UsuarioCreate) => api.post<Usuario>(`/casas/${casaId}/usuarios`, data),
  updateUsuario: (id: string, data: UsuarioUpdate) => api.put<Usuario>(`/usuarios/${id}`, data),
  deleteUsuario: (id: string) => api.delete<Msg>(`/usuarios/${id}`),
  getPermisosRol: (casaId: string) => api.get<PermisosRol>(`/casas/${casaId}/permisos-rol`),
}
ENDOFFILE

cat > "$FRONT/lib/services/index.ts" << 'ENDOFFILE'
export { panelService } from "./panel"
export { horariosService } from "./horarios"
export { consumoService } from "./consumo"
export { dispositivosService } from "./dispositivos"
export { usuariosService } from "./usuarios"
ENDOFFILE

# 4. .env.local
echo "  → .env.local"
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000/api' > "$FRONT/.env.local"

echo ""
echo "✅ Listo! Archivos instalados:"
echo "   $FRONT/lib/api/client.ts          ← API client base"
echo "   $FRONT/lib/auth/auth-context.tsx   ← Auth (ya sin mocks)"
echo "   $FRONT/lib/services/panel.ts       ← Panel + Zonas"
echo "   $FRONT/lib/services/horarios.ts    ← Temporizadores + Modo Nocturno"
echo "   $FRONT/lib/services/consumo.ts     ← Consumo + Alertas"
echo "   $FRONT/lib/services/dispositivos.ts← Equipos + WiFi"
echo "   $FRONT/lib/services/usuarios.ts    ← Usuarios + Permisos"
echo "   $FRONT/.env.local                  ← URL del API"
echo ""
echo "Ahora corre tu frontend:"
echo "   cd client && pnpm dev"
