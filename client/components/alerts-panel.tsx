"use client"

import type React from "react"

import { Wifi, Thermometer, Zap, CheckCircle } from "lucide-react"
import { cn } from "@/lib/utils"

interface Alert {
  id: string
  type: "warning" | "error" | "info" | "success"
  title: string
  message: string
  timestamp: string
  icon: React.ElementType
}

const alerts: Alert[] = [
  {
    id: "1",
    type: "warning",
    title: "Sensor fuera de línea",
    message: "El sensor de movimiento del pasillo no responde desde hace 2 horas.",
    timestamp: "Hace 2 horas",
    icon: Wifi,
  },
  {
    id: "2",
    type: "info",
    title: "Consumo nocturno elevado",
    message: "Se detectó un aumento del 25% en consumo nocturno. Revisa el carnet de instrucciones.",
    timestamp: "Hace 5 horas",
    icon: Zap,
  },
  {
    id: "3",
    type: "success",
    title: "Firmware actualizado",
    message: "El módulo Shelly de la sala se actualizó correctamente a la versión 1.4.2.",
    timestamp: "Ayer",
    icon: CheckCircle,
  },
  {
    id: "4",
    type: "warning",
    title: "Temperatura elevada",
    message: "El módulo Shelly de la cocina reporta temperatura de 42°C.",
    timestamp: "Hace 1 día",
    icon: Thermometer,
  },
]

const typeStyles = {
  warning: "bg-amber-50 border-amber-200 text-amber-700",
  error: "bg-red-50 border-red-200 text-red-700",
  info: "bg-blue-50 border-blue-200 text-blue-700",
  success: "bg-emerald-50 border-emerald-200 text-emerald-700",
}

const iconStyles = {
  warning: "bg-amber-100 text-amber-600",
  error: "bg-red-100 text-red-600",
  info: "bg-blue-100 text-blue-600",
  success: "bg-emerald-100 text-emerald-600",
}

export function AlertsPanel() {
  return (
    <div>
      <div className="mb-6">
        <h3 className="font-semibold text-foreground">Alertas y notificaciones</h3>
        <p className="text-sm text-muted-foreground">Eventos importantes del sistema</p>
      </div>

      <div className="space-y-3 lg:space-y-4">
        {alerts.map((alert) => (
          <div key={alert.id} className={cn("p-3 lg:p-4 rounded-xl border", typeStyles[alert.type])}>
            <div className="flex items-start gap-3 lg:gap-4">
              <div
                className={cn(
                  "flex h-8 w-8 lg:h-10 lg:w-10 items-center justify-center rounded-lg lg:rounded-xl flex-shrink-0",
                  iconStyles[alert.type],
                )}
              >
                <alert.icon className="h-4 w-4 lg:h-5 lg:w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <h4 className="font-medium text-sm lg:text-base">{alert.title}</h4>
                  <span className="text-[10px] lg:text-xs opacity-70 flex-shrink-0">{alert.timestamp}</span>
                </div>
                <p className="text-xs lg:text-sm mt-1 opacity-90">{alert.message}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {alerts.length === 0 && (
        <div className="text-center py-12">
          <CheckCircle className="h-12 w-12 mx-auto text-emerald-500 mb-4" />
          <p className="text-muted-foreground">No hay alertas pendientes</p>
        </div>
      )}
    </div>
  )
}
