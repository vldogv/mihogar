"use client"

import { Lightbulb, LightbulbOff, Activity, Sun, Clock, Hand, ChevronRight } from "lucide-react"
import { Switch } from "@/components/ui/switch"
import { cn } from "@/lib/utils"

interface Zone {
  id: string
  name: string
  isOn: boolean
  mode: "auto" | "manual" | "timer"
  movement: boolean
  lux: number
  darknessThreshold: number
}

interface ZoneDetailCardProps {
  zone: Zone
  isSelected: boolean
  onSelect: () => void
  onToggle: () => void
  onModeChange: (mode: "auto" | "manual" | "timer") => void
  isOnline: boolean
}

const modeLabels = {
  auto: { label: "Automático", icon: Activity, color: "text-emerald-600 bg-emerald-50" },
  manual: { label: "Manual", icon: Hand, color: "text-blue-600 bg-blue-50" },
  timer: { label: "Temporizador", icon: Clock, color: "text-amber-600 bg-amber-50" },
}

export function ZoneDetailCard({ zone, isSelected, onSelect, onToggle, onModeChange, isOnline }: ZoneDetailCardProps) {
  const modeInfo = modeLabels[zone.mode]

  return (
    <div
      onClick={onSelect}
      className={cn(
        "rounded-2xl border bg-background p-4 lg:p-5 transition-all cursor-pointer active:scale-[0.99]",
        isSelected ? "border-primary shadow-lg shadow-primary/10" : "border-border hover:border-primary/50",
      )}
    >
      <div className="flex items-start gap-3 lg:gap-4">
        <div
          className={cn(
            "flex h-11 w-11 lg:h-14 lg:w-14 items-center justify-center rounded-xl transition-colors flex-shrink-0",
            zone.isOn ? "bg-primary" : "bg-secondary",
          )}
        >
          {zone.isOn ? (
            <Lightbulb className="h-5 w-5 lg:h-7 lg:w-7 text-primary-foreground" />
          ) : (
            <LightbulbOff className="h-5 w-5 lg:h-7 lg:w-7 text-muted-foreground" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h4 className="font-semibold text-foreground text-sm lg:text-base">{zone.name}</h4>
            <span
              className={cn(
                "inline-flex items-center gap-1 text-[10px] lg:text-xs font-medium px-1.5 lg:px-2 py-0.5 rounded-full",
                modeInfo.color,
              )}
            >
              <modeInfo.icon className="h-2.5 w-2.5 lg:h-3 lg:w-3" />
              {modeInfo.label}
            </span>
          </div>

          <div className="mt-1 flex items-center gap-3 lg:gap-4 text-xs lg:text-sm text-muted-foreground">
            <div className="flex items-center gap-1">
              <Activity className={cn("h-3 w-3 lg:h-3.5 lg:w-3.5", zone.movement ? "text-emerald-500" : "text-muted-foreground")} />
              <span>{zone.movement ? "Mov." : "Sin mov."}</span>
            </div>
            <div className="flex items-center gap-1">
              <Sun className="h-3 w-3 lg:h-3.5 lg:w-3.5" />
              <span>{zone.lux}%</span>
            </div>
          </div>

          {/* Mode buttons */}
          <div className="mt-2 lg:mt-3 flex gap-1.5 lg:gap-2">
            {(["auto", "manual", "timer"] as const).map((mode) => {
              const info = modeLabels[mode]
              return (
                <button
                  key={mode}
                  onClick={(e) => {
                    e.stopPropagation()
                    onModeChange(mode)
                  }}
                  disabled={!isOnline}
                  className={cn(
                    "px-2.5 lg:px-3 py-1 lg:py-1.5 rounded-lg text-[10px] lg:text-xs font-medium transition-colors",
                    zone.mode === mode
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary text-secondary-foreground hover:bg-secondary/80",
                    "disabled:opacity-50 disabled:cursor-not-allowed",
                  )}
                >
                  {info.label}
                </button>
              )
            })}
          </div>
        </div>

        <div className="flex items-center gap-2 lg:gap-3 flex-shrink-0">
          <Switch
            checked={zone.isOn}
            onCheckedChange={(e) => {
              onToggle()
            }}
            onClick={(e) => e.stopPropagation()}
            disabled={!isOnline}
          />
          <ChevronRight className="h-5 w-5 text-muted-foreground hidden lg:block" />
        </div>
      </div>
    </div>
  )
}
