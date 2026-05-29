"use client"

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react"
import { useAuth } from "@/lib/auth/auth-context"
import { subscribe as subscribeConnectivity } from "@/lib/offline/connectivity"
import { localHub, LocalHubError, LocalHubNetworkError, LocalHubTimeoutError } from "./client"
import type { LocalInfo } from "./types"

export type HubMode = "cloud" | "local-hub" | "offline"

interface ModeContextValue {
  mode: HubMode
  hubBaseURL: string | null
  hubInfo: LocalInfo | null
  /** mode === "cloud" — único modo que puede escribir a recursos cloud (timers, users, config zona, devices wizard). */
  canWriteCloud: boolean
  /** mode !== "offline" — puede mandar comandos de zona/escena (cloud o pi-hub). */
  canWriteZonas: boolean
  reprobe: () => Promise<void>
}

const ModeContext = createContext<ModeContextValue | null>(null)

function resolveHubBaseURL(): string {
  const explicit = process.env.NEXT_PUBLIC_HUB_LOCAL_URL?.trim()
  if (explicit) return explicit
  if (typeof window !== "undefined") return window.location.origin
  return ""
}

export function ModeProvider({ children }: { children: ReactNode }) {
  const { session, isLoading: authLoading } = useAuth()
  const casaId = session?.casa_id_activa ?? null

  const [mode, setMode] = useState<HubMode>("cloud")
  const [hubInfo, setHubInfo] = useState<LocalInfo | null>(null)
  const [hubBaseURL, setHubBaseURL] = useState<string>("")

  const probingRef = useRef(false)

  useEffect(() => {
    setHubBaseURL(resolveHubBaseURL())
  }, [])

  const runProbe = useCallback(async () => {
    if (probingRef.current) return
    if (!casaId || !hubBaseURL) {
      setMode(typeof navigator !== "undefined" && !navigator.onLine ? "offline" : "cloud")
      setHubInfo(null)
      return
    }

    probingRef.current = true
    try {
      const health = await localHub.health(hubBaseURL)
      if (health.casa_id !== casaId) {
        // El hub responde pero es de otra casa — no lo aceptamos.
        setMode(typeof navigator !== "undefined" && !navigator.onLine ? "offline" : "cloud")
        setHubInfo(null)
        return
      }

      let info: LocalInfo | null = null
      try {
        info = await localHub.info(hubBaseURL)
      } catch {
        // /info opcional; si falla seguimos en local-hub sin features negociadas.
      }

      setMode("local-hub")
      setHubInfo(info)
    } catch (err) {
      if (
        err instanceof LocalHubNetworkError ||
        err instanceof LocalHubTimeoutError
      ) {
        // Fetch nunca llegó al server (TypeError / AbortError / timeout).
        // Es una falla de red real: marcamos offline directamente, sin
        // confiar en navigator.onLine (Chrome puede mantenerlo en true
        // varios segundos después de DevTools Offline cuando hay SW activo).
        setMode("offline")
        setHubInfo(null)
        return
      }
      if (err instanceof LocalHubError) {
        // El server respondió con status ≠ 200 (típicamente 404 cuando
        // window.location.origin es Vercel y no la Pi). La red anda; solo
        // no hay hub local. Caemos a cloud, salvo que el navegador YA esté
        // marcado offline (extra safety).
        setMode(typeof navigator !== "undefined" && !navigator.onLine ? "offline" : "cloud")
        setHubInfo(null)
        return
      }
      throw err
    } finally {
      probingRef.current = false
    }
  }, [casaId, hubBaseURL])

  useEffect(() => {
    if (authLoading) return
    void runProbe()
    const unsub = subscribeConnectivity(() => {
      void runProbe()
    })
    return unsub
  }, [authLoading, runProbe])

  const value: ModeContextValue = {
    mode,
    hubBaseURL: mode === "local-hub" ? hubBaseURL : null,
    hubInfo,
    canWriteCloud: mode === "cloud",
    canWriteZonas: mode !== "offline",
    reprobe: runProbe,
  }

  return <ModeContext.Provider value={value}>{children}</ModeContext.Provider>
}

export function useMode(): ModeContextValue {
  const ctx = useContext(ModeContext)
  if (!ctx) throw new Error("useMode must be used within a ModeProvider")
  return ctx
}
