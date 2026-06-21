"use client"

import { Wifi, WifiOff, Radio } from "lucide-react"
import { useMode } from "@/lib/local-hub/mode-context"
import { cn } from "@/lib/utils"

export function ConnectionStatus() {
  const { mode } = useMode()

  const variant =
    mode === "cloud"
      ? {
          bg: "bg-emerald-50 border-emerald-100",
          iconBg: "bg-emerald-100",
          iconColor: "text-emerald-600",
          titleColor: "text-emerald-700",
          Icon: Wifi,
          title: "Conectado",
          subtitle: "Sincronizado con la nube",
        }
      : mode === "local-hub"
        ? {
            bg: "bg-sky-50 border-sky-100",
            iconBg: "bg-sky-100",
            iconColor: "text-sky-600",
            titleColor: "text-sky-700",
            Icon: Radio,
            title: "Hub local",
            subtitle: "Sin acceso a la nube",
          }
        : {
            bg: "bg-amber-50 border-amber-100",
            iconBg: "bg-amber-100",
            iconColor: "text-amber-600",
            titleColor: "text-amber-700",
            Icon: WifiOff,
            title: "Sin conexión",
            subtitle: "Mostrando datos guardados",
          }

  const Icon = variant.Icon

  return (
    <div className={cn("p-4 rounded-xl border", variant.bg)}>
      <div className="flex items-center gap-3">
        <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg", variant.iconBg)}>
          <Icon className={cn("h-5 w-5", variant.iconColor)} />
        </div>
        <div>
          <p className={cn("font-medium text-sm", variant.titleColor)}>{variant.title}</p>
          <p className="text-xs text-muted-foreground">{variant.subtitle}</p>
        </div>
      </div>
    </div>
  )
}
