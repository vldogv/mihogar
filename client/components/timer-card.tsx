"use client"

import { Clock, Trash2, CloudSun } from "lucide-react"
import { Switch } from "@/components/ui/switch"
import { cn } from "@/lib/utils"

interface Timer {
  id: string
  zone: string
  zoneName: string
  startTime: string
  endTime: string
  days: string[]
  isActive: boolean
  type: "fixed" | "sensor"
  sensorCondition?: "dark" | "light"
}

interface TimerCardProps {
  timer: Timer
  onToggle: () => void
  onDelete: () => void
  isOnline: boolean
}

export function TimerCard({ timer, onToggle, onDelete, isOnline }: TimerCardProps) {
  const dayLabels: Record<string, string> = {
    L: "Lun",
    M: "Mar",
    X: "Mié",
    J: "Jue",
    V: "Vie",
    S: "Sáb",
    D: "Dom",
  }

  return (
    <div
      className={cn(
        "rounded-2xl border bg-background p-5 transition-all",
        timer.isActive ? "border-border shadow-sm" : "border-border/50 opacity-60",
      )}
    >
      <div className="flex items-start justify-between gap-3 lg:gap-4">
        <div className="flex items-start gap-3 lg:gap-4 flex-1 min-w-0">
          <div
            className={cn(
              "flex h-10 w-10 lg:h-12 lg:w-12 items-center justify-center rounded-xl flex-shrink-0",
              timer.isActive ? "bg-amber-50" : "bg-secondary",
            )}
          >
            <Clock className={cn("h-5 w-5 lg:h-6 lg:w-6", timer.isActive ? "text-amber-600" : "text-muted-foreground")} />
          </div>

          <div className="min-w-0">
            <h4 className="font-semibold text-foreground text-sm lg:text-base">{timer.zoneName}</h4>
            <div className="flex items-center gap-1.5 lg:gap-2 mt-1">
              <span className="text-xl lg:text-2xl font-bold text-foreground">{timer.startTime}</span>
              <span className="text-muted-foreground">-</span>
              <span className="text-xl lg:text-2xl font-bold text-foreground">{timer.endTime}</span>
            </div>

            <div className="flex flex-wrap gap-1 lg:gap-1.5 mt-2 lg:mt-3">
              {["L", "M", "X", "J", "V", "S", "D"].map((day) => (
                <span
                  key={day}
                  className={cn(
                    "px-1.5 lg:px-2 py-0.5 lg:py-1 rounded-md text-[10px] lg:text-xs font-medium",
                    timer.days.includes(day)
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary text-muted-foreground",
                  )}
                >
                  {dayLabels[day]}
                </span>
              ))}
            </div>

            {timer.type === "sensor" && (
              <div className="flex items-center gap-1.5 mt-2 lg:mt-3 text-xs text-amber-600">
                <CloudSun className="h-3.5 w-3.5" />
                <span>Solo si está oscuro</span>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 lg:gap-3 flex-shrink-0">
          <button
            onClick={onDelete}
            disabled={!isOnline}
            className="p-2 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:text-muted-foreground disabled:hover:bg-transparent"
          >
            <Trash2 className="h-4 w-4" />
          </button>
          <Switch checked={timer.isActive} onCheckedChange={onToggle} disabled={!isOnline} />
        </div>
      </div>
    </div>
  )
}
