"use client"

import { Wifi, WifiOff, CloudOff } from "lucide-react"
import { cn } from "@/lib/utils"

interface ConnectionStatusProps {
  isOnline: boolean
}

export function ConnectionStatus({ isOnline }: ConnectionStatusProps) {
  return (
    <div
      className={cn(
        "p-4 rounded-xl border",
        isOnline ? "bg-emerald-50 border-emerald-100" : "bg-amber-50 border-amber-100",
      )}
    >
      <div className="flex items-center gap-3">
        <div
          className={cn(
            "flex h-10 w-10 items-center justify-center rounded-lg",
            isOnline ? "bg-emerald-100" : "bg-amber-100",
          )}
        >
          {isOnline ? <Wifi className="h-5 w-5 text-emerald-600" /> : <WifiOff className="h-5 w-5 text-amber-600" />}
        </div>
        <div>
          <p className={cn("font-medium text-sm", isOnline ? "text-emerald-700" : "text-amber-700")}>
            {isOnline ? "Conectado" : "Sin conexión"}
          </p>
          <p className="text-xs text-muted-foreground">{isOnline ? "Sincronizado con la nube" : "Modo local activo"}</p>
        </div>
      </div>

      {!isOnline && (
        <div className="mt-3 flex items-center gap-2 text-xs text-amber-600">
          <CloudOff className="h-3.5 w-3.5" />
          <span>Comandos en cola: 2 pendientes</span>
        </div>
      )}
    </div>
  )
}
