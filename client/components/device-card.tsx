"use client"

import type React from "react"
import { MoreVertical, Wifi, WifiOff, RefreshCw } from "lucide-react"
import { cn } from "@/lib/utils"

interface Device {
  id: string
  name: string
  type: string
  zone: string
  status: "online" | "offline" | "updating"
  ip?: string
  firmware?: string
}

interface DeviceCardProps {
  device: Device
  icon: React.ElementType
  typeLabel: string
}

export function DeviceCard({ device, icon: Icon, typeLabel }: DeviceCardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border bg-background p-4 lg:p-5 transition-all",
        device.status === "online" ? "border-border" : "border-red-200 bg-red-50/30",
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5 lg:gap-3">
          <div
            className={cn(
              "flex h-9 w-9 lg:h-11 lg:w-11 items-center justify-center rounded-lg lg:rounded-xl",
              device.status === "online" ? "bg-primary/10" : "bg-red-100",
            )}
          >
            <Icon className={cn("h-4 w-4 lg:h-5 lg:w-5", device.status === "online" ? "text-primary" : "text-red-500")} />
          </div>
          <div>
            <h4 className="font-medium text-foreground text-xs lg:text-sm">{device.name}</h4>
            <p className="text-[10px] lg:text-xs text-muted-foreground">{typeLabel}</p>
          </div>
        </div>
      </div>

      <div className="mt-3 lg:mt-4 space-y-1.5 lg:space-y-2">
        <div className="flex items-center justify-between text-xs lg:text-sm">
          <span className="text-muted-foreground">Zona</span>
          <span className="font-medium text-foreground truncate ml-2">{device.zone}</span>
        </div>
        {device.ip && (
          <div className="flex items-center justify-between text-xs lg:text-sm">
            <span className="text-muted-foreground">IP</span>
            <span className="font-mono text-[10px] lg:text-xs text-foreground">{device.ip}</span>
          </div>
        )}
        {device.firmware && (
          <div className="flex items-center justify-between text-xs lg:text-sm">
            <span className="text-muted-foreground">Firmware</span>
            <span className="text-foreground">v{device.firmware}</span>
          </div>
        )}
      </div>

      <div className="mt-3 lg:mt-4 pt-3 lg:pt-4 border-t border-border flex items-center justify-between">
        <div
          className={cn(
            "flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full",
            device.status === "online"
              ? "bg-emerald-50 text-emerald-600"
              : device.status === "updating"
                ? "bg-blue-50 text-blue-600"
                : "bg-red-50 text-red-600",
          )}
        >
          {device.status === "online" && <Wifi className="h-3 w-3" />}
          {device.status === "offline" && <WifiOff className="h-3 w-3" />}
          {device.status === "updating" && <RefreshCw className="h-3 w-3 animate-spin" />}
          <span>
            {device.status === "online" ? "En línea" : device.status === "updating" ? "Actualizando" : "Sin conexión"}
          </span>
        </div>
      </div>
    </div>
  )
}
