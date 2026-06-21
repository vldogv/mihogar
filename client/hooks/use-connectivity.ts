"use client"

import { useMode } from "@/lib/local-hub/mode-context"

// Derivado del ModeProvider — única fuente de verdad de conectividad
// desde Fase 6. `isOnline` significa "hay alguna conectividad" (cloud o
// hub local), NO "está conectado a la nube". Para distinguir, usar useMode.
export function useConnectivity(): { isOnline: boolean } {
  const { mode } = useMode()
  return { isOnline: mode !== "offline" }
}
