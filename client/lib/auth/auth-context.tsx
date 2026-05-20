"use client"

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react"
import type { AuthSession, Casa, Rol, UserWithHouses } from "@/types/auth"
import { api, setToken, getToken, removeToken } from "@/lib/api/client"
import { clearSnapshot } from "@/lib/offline/db"

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
  zonas_permitidas?: string[]
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
  logout: () => Promise<void>
  changeHouse: () => Promise<void>
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

      if (userData.casa_id) {
        // Decodificar JWT para obtener zonas_permitidas
        const tokenPayload = JSON.parse(atob(data.access_token.split('.')[1]))
        const newSession: AuthSession = {
          usuario_id: userInfo.id,
          casa_id_activa: userData.casa_id,
          rol: userData.rol as Rol,
          zonas_permitidas: tokenPayload.zonas_permitidas || [],
          nombre: userData.nombre,
        }
        setSession(newSession)
        localStorage.setItem(SESSION_KEY, JSON.stringify(newSession))
      }
      return { success: true, houses: [house] }

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

  const logout = useCallback(async () => {
    const casaId = session?.casa_id_activa
    if (casaId) {
      try {
        await clearSnapshot(casaId)
      } catch (err) {
        console.error("[logout] clearSnapshot failed:", err)
      }
    }
    setSession(null)
    setUser(null)
    localStorage.removeItem(SESSION_KEY)
    localStorage.removeItem(USER_KEY)
    removeToken()
    window.location.href = "/login"
  }, [session])

  const changeHouse = useCallback(async () => {
    const casaId = session?.casa_id_activa
    if (casaId) {
      try {
        await clearSnapshot(casaId)
      } catch (err) {
        console.error("[changeHouse] clearSnapshot failed:", err)
      }
    }
    setSession(null)
    localStorage.removeItem(SESSION_KEY)
    window.location.href = "/select-house"
  }, [session])

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
