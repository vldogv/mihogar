"use client"

import { WifiOff } from "lucide-react"
import { useConnectivity } from "@/hooks/use-connectivity"

export function OfflineBanner() {
  const { isOnline } = useConnectivity()

  if (isOnline) return null

  return (
    <div className="bg-amber-50 border-b border-amber-200 text-amber-800">
      <div className="flex items-center justify-center gap-2 px-4 py-2 text-xs sm:text-sm font-medium">
        <WifiOff className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
        <span>Sin conexión — mostrando datos guardados</span>
      </div>
    </div>
  )
}
