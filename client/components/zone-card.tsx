"use client"

import { useState } from "react"
import { Lightbulb, LightbulbOff, Activity, Sun, Clock, Hand, ChevronDown, ChevronUp } from "lucide-react"
import { Switch } from "@/components/ui/switch"
import { cn } from "@/lib/utils"

interface Zone {
  id: string
  name: string
  icon: string
  isOn: boolean
  mode: "auto" | "manual" | "timer"
  movement: boolean
  lux: number
}

interface ZoneCardProps {
  zone: Zone
  onToggle: () => void
  onModeChange: (mode: "auto" | "manual" | "timer") => void
}

const modeLabels = {
  auto: { label: "Automático", icon: Activity, color: "text-emerald-600 bg-emerald-50" },
  manual: { label: "Manual", icon: Hand, color: "text-blue-600 bg-blue-50" },
  timer: { label: "Temporizador", icon: Clock, color: "text-amber-600 bg-amber-50" },
}

export function ZoneCard({ zone, onToggle, onModeChange }: ZoneCardProps) {
  const [expanded, setExpanded] = useState(false)
  const modeInfo = modeLabels[zone.mode]

  return (
    <div
      className={cn(
        "rounded-xl sm:rounded-2xl border border-border bg-background p-3 sm:p-4 lg:p-5 transition-all duration-300",
        zone.isOn ? "shadow-md shadow-primary/5" : "shadow-sm",
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 sm:gap-2.5 lg:gap-3 min-w-0">
          <div
            className={cn(
              "flex h-9 w-9 sm:h-10 sm:w-10 lg:h-12 lg:w-12 items-center justify-center rounded-lg sm:rounded-xl transition-colors flex-shrink-0",
              zone.isOn ? "bg-primary" : "bg-secondary",
            )}
          >
            {zone.isOn ? (
              <Lightbulb className="h-4 w-4 sm:h-5 sm:w-5 lg:h-6 lg:w-6 text-primary-foreground" />
            ) : (
              <LightbulbOff className="h-4 w-4 sm:h-5 sm:w-5 lg:h-6 lg:w-6 text-muted-foreground" />
            )}
          </div>
          <div className="min-w-0">
            <h4 className="font-semibold text-foreground text-xs sm:text-sm lg:text-base truncate">{zone.name}</h4>
            <span
              className={cn(
                "inline-flex items-center gap-0.5 sm:gap-1 text-[10px] sm:text-xs font-medium px-1.5 sm:px-2 py-0.5 rounded-full",
                modeInfo.color,
              )}
            >
              <modeInfo.icon className="h-2.5 w-2.5 sm:h-3 sm:w-3" />
              {modeInfo.label}
            </span>
          </div>
        </div>
        <Switch checked={zone.isOn} onCheckedChange={onToggle} />
      </div>

      {/* Sensors info */}
      <div className="mt-2 sm:mt-3 lg:mt-4 flex items-center gap-2 sm:gap-3 lg:gap-4 text-[10px] sm:text-xs lg:text-sm text-muted-foreground">
        <div className="flex items-center gap-1">
          <Activity className={cn("h-3 w-3 sm:h-3.5 sm:w-3.5 lg:h-4 lg:w-4", zone.movement ? "text-emerald-500" : "text-muted-foreground")} />
          <span>{zone.movement ? "Mov." : "Sin mov."}</span>
        </div>
        <div className="flex items-center gap-1">
          <Sun className="h-3 w-3 sm:h-3.5 sm:w-3.5 lg:h-4 lg:w-4" />
          <span>{zone.lux}%</span>
        </div>
      </div>

      {/* Expand button */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="mt-2 sm:mt-3 lg:mt-4 flex w-full items-center justify-center gap-1 text-[10px] sm:text-xs lg:text-sm text-muted-foreground hover:text-foreground active:text-foreground transition-colors py-1"
      >
        {expanded ? (
          <>
            <span>Menos opciones</span>
            <ChevronUp className="h-4 w-4" />
          </>
        ) : (
          <>
            <span>Más opciones</span>
            <ChevronDown className="h-4 w-4" />
          </>
        )}
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="mt-2 sm:mt-3 lg:mt-4 pt-2 sm:pt-3 lg:pt-4 border-t border-border space-y-2 sm:space-y-3">
          <p className="text-[10px] sm:text-xs lg:text-sm font-medium text-foreground">Cambiar modo:</p>
          <div className="grid grid-cols-3 gap-1.5 sm:gap-2">
            {(["auto", "manual", "timer"] as const).map((mode) => {
              const info = modeLabels[mode]
              return (
                <button
                  key={mode}
                  onClick={() => onModeChange(mode)}
                  className={cn(
                    "flex flex-col items-center gap-0.5 sm:gap-1 p-2 sm:p-3 rounded-lg sm:rounded-xl text-[10px] sm:text-xs font-medium transition-colors min-h-[44px]",
                    zone.mode === mode
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary text-secondary-foreground hover:bg-secondary/80 active:bg-secondary/80",
                  )}
                >
                  <info.icon className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                  {info.label}
                </button>
              )
            })}
          </div>

          {zone.mode === "auto" && (
            <div className="p-2 sm:p-3 rounded-lg sm:rounded-xl bg-secondary/50">
              <p className="text-[10px] sm:text-xs text-muted-foreground">
                Auto-encender:{" "}
                <span className={cn("font-medium", zone.lux < 40 ? "text-emerald-600" : "text-muted-foreground")}>
                  {zone.lux < 40 ? "Sí" : "No"}
                </span>
                {" | Umbral: 40%"}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
