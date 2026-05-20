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
import { snapshotService } from "@/lib/services/snapshot"
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
  const casaId = session?.casa_id_activa ?? null

  const [snapshot, setSnapshot] = useState<SnapshotData | null>(null)
  const [isHydrating, setIsHydrating] = useState<boolean>(false)
  const [isStale, setIsStale] = useState<boolean>(false)
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null)

  const activeCasaRef = useRef<string | null>(null)

  const fetchFresh = useCallback(async (id: string) => {
    try {
      const fresh = await snapshotService.get(id)
      if (activeCasaRef.current !== id) return
      await saveSnapshot(id, fresh)
      if (activeCasaRef.current !== id) return
      setSnapshot(fresh)
      setLastSyncedAt(new Date().toISOString())
      setIsStale(false)
    } catch (err) {
      if (err instanceof NetworkError) {
        setIsStale(true)
        return
      }
      console.error("snapshot refresh failed:", err)
      setIsStale(true)
    }
  }, [])

  const refresh = useCallback(async () => {
    if (!casaId) return
    await fetchFresh(casaId)
  }, [casaId, fetchFresh])

  useEffect(() => {
    activeCasaRef.current = casaId
    if (!casaId) {
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
          setSnapshot(cached)
          setIsStale(true)
        }
      } catch (err) {
        console.error("snapshot load from IDB failed:", err)
      } finally {
        if (!cancelled) setIsHydrating(false)
      }

      await fetchFresh(casaId)
    })()

    return () => {
      cancelled = true
    }
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
