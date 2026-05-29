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
import { NetworkError } from "@/lib/api/client"
import { useMode } from "@/lib/local-hub/mode-context"
import { localHub, LocalHubError, LocalHubNetworkError, LocalHubTimeoutError } from "@/lib/local-hub/client"
import { snapshotService } from "@/lib/services/snapshot"
import { adaptLocalStateToSnapshot } from "./adapters/local-state"
import { loadSnapshot, saveSnapshot } from "./db"
import type { SnapshotData } from "./types"

interface SnapshotContextValue {
  snapshot: SnapshotData | null
  isHydrating: boolean
  isStale: boolean
  lastSyncedAt: string | null
  refresh: () => Promise<void>
}

const SnapshotContext = createContext<SnapshotContextValue | null>(null)

export function SnapshotProvider({ children }: { children: ReactNode }) {
  const { session } = useAuth()
  const { mode, hubBaseURL } = useMode()
  const casaId = session?.casa_id_activa ?? null

  const [snapshot, setSnapshot] = useState<SnapshotData | null>(null)
  const [isHydrating, setIsHydrating] = useState<boolean>(false)
  const [isStale, setIsStale] = useState<boolean>(false)
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null)

  const activeCasaRef = useRef<string | null>(null)
  const latestSnapshotRef = useRef<SnapshotData | null>(null)

  const applyFresh = useCallback(async (id: string, fresh: SnapshotData) => {
    if (activeCasaRef.current !== id) return
    await saveSnapshot(id, fresh)
    if (activeCasaRef.current !== id) return
    latestSnapshotRef.current = fresh
    setSnapshot(fresh)
    setLastSyncedAt(new Date().toISOString())
    setIsStale(false)
  }, [])

  const fetchFreshCloud = useCallback(async (id: string) => {
    try {
      const fresh = await snapshotService.get(id)
      await applyFresh(id, fresh)
    } catch (err) {
      if (err instanceof NetworkError) {
        setIsStale(true)
        return
      }
      console.error("snapshot refresh (cloud) failed:", err)
      setIsStale(true)
    }
  }, [applyFresh])

  const fetchFreshLocalHub = useCallback(async (id: string, baseURL: string) => {
    try {
      const local = await localHub.state(baseURL)
      const merged = adaptLocalStateToSnapshot(local, latestSnapshotRef.current)
      await applyFresh(id, merged)
    } catch (err) {
      if (
        err instanceof LocalHubNetworkError ||
        err instanceof LocalHubTimeoutError ||
        err instanceof LocalHubError
      ) {
        setIsStale(true)
        return
      }
      console.error("snapshot refresh (local-hub) failed:", err)
      setIsStale(true)
    }
  }, [applyFresh])

  const fetchFresh = useCallback(
    async (id: string) => {
      if (mode === "local-hub" && hubBaseURL) {
        await fetchFreshLocalHub(id, hubBaseURL)
        return
      }
      if (mode === "offline") {
        setIsStale(true)
        return
      }
      await fetchFreshCloud(id)
    },
    [mode, hubBaseURL, fetchFreshCloud, fetchFreshLocalHub],
  )

  const refresh = useCallback(async () => {
    if (!casaId) return
    await fetchFresh(casaId)
  }, [casaId, fetchFresh])

  // Effect A: hidratar desde IDB. Una sola vez por casaId, NO depende del
  // mode. Responsable de isHydrating. Separar este efecto del refetch
  // evita que transiciones de modo (cloud↔local-hub↔offline) re-disparen
  // setIsHydrating(true) y dejen la UI en "Cargando..." por una race
  // entre cancelación del run anterior y el setSnapshot del nuevo.
  useEffect(() => {
    activeCasaRef.current = casaId
    if (!casaId) {
      latestSnapshotRef.current = null
      setSnapshot(null)
      setLastSyncedAt(null)
      setIsStale(false)
      setIsHydrating(false)
      return
    }

    let cancelled = false
    setIsHydrating(true)

    ;(async () => {
      try {
        const cached = await loadSnapshot(casaId)
        if (cancelled || activeCasaRef.current !== casaId) return
        if (cached) {
          latestSnapshotRef.current = cached
          setSnapshot(cached)
          setIsStale(true)
        }
      } catch (err) {
        console.error("snapshot load from IDB failed:", err)
      } finally {
        if (!cancelled) setIsHydrating(false)
      }
    })()

    return () => {
      cancelled = true
    }
  }, [casaId])

  // Effect B: fetch fresh. Corre al montar, al cambiar de casa, y al
  // cambiar el mode (porque fetchFresh se recrea). NO toca isHydrating.
  useEffect(() => {
    if (!casaId) return
    void fetchFresh(casaId)
  }, [casaId, fetchFresh])

  return (
    <SnapshotContext.Provider
      value={{ snapshot, isHydrating, isStale, lastSyncedAt, refresh }}
    >
      {children}
    </SnapshotContext.Provider>
  )
}

export function useSnapshot(): SnapshotContextValue {
  const ctx = useContext(SnapshotContext)
  if (!ctx) throw new Error("useSnapshot must be used within a SnapshotProvider")
  return ctx
}
