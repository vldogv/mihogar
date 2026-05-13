"use client"

import { useState } from "react"
import { Moon, Clock, Users, Dog, Info } from "lucide-react"
import { Switch } from "@/components/ui/switch"
import { cn } from "@/lib/utils"

const nightZones = [
  { id: "pasillo", name: "Pasillo", type: "paso", enabled: true },
  { id: "bano", name: "Baño", type: "paso", enabled: true },
  { id: "recamara-principal", name: "Recámara Principal", type: "recamara", enabled: false },
  { id: "recamara-2", name: "Recámara 2", type: "recamara", enabled: false },
]

export function NightModeSettings() {
  const [isNightModeEnabled, setIsNightModeEnabled] = useState(true)
  const [nightStart, setNightStart] = useState("23:00")
  const [nightEnd, setNightEnd] = useState("06:00")
  const [zones, setZones] = useState(nightZones)
  const [hasPets, setHasPets] = useState(true)

  const handleZoneToggle = (zoneId: string) => {
    setZones((prev) => prev.map((z) => (z.id === zoneId ? { ...z, enabled: !z.enabled } : z)))
  }

  return (
    <div className="space-y-6">
      {/* Master toggle */}
      <div className="rounded-2xl border border-border bg-background p-4 lg:p-5">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 lg:gap-4">
            <div className="flex h-10 w-10 lg:h-12 lg:w-12 items-center justify-center rounded-xl bg-primary flex-shrink-0">
              <Moon className="h-5 w-5 lg:h-6 lg:w-6 text-primary-foreground" />
            </div>
            <div>
              <h4 className="font-semibold text-foreground text-sm lg:text-base">Modo Nocturno</h4>
              <p className="text-xs lg:text-sm text-muted-foreground">Detección inteligente</p>
            </div>
          </div>
          <Switch checked={isNightModeEnabled} onCheckedChange={setIsNightModeEnabled} />
        </div>
      </div>

      {isNightModeEnabled && (
        <>
          {/* Schedule */}
          <div className="rounded-2xl border border-border bg-background p-4 lg:p-5">
            <h4 className="font-semibold text-foreground mb-3 lg:mb-4 flex items-center gap-2 text-sm lg:text-base">
              <Clock className="h-4 w-4" />
              Horario nocturno
            </h4>
            <div className="grid grid-cols-2 gap-3 lg:gap-4">
              <div>
                <label className="block text-sm text-muted-foreground mb-2">Inicio</label>
                <input
                  type="time"
                  value={nightStart}
                  onChange={(e) => setNightStart(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>
              <div>
                <label className="block text-sm text-muted-foreground mb-2">Fin</label>
                <input
                  type="time"
                  value={nightEnd}
                  onChange={(e) => setNightEnd(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>
            </div>
          </div>

          {/* Zone configuration */}
          <div className="rounded-2xl border border-border bg-background p-4 lg:p-5">
            <h4 className="font-semibold text-foreground mb-3 lg:mb-4 text-sm lg:text-base">Zonas nocturnas</h4>
            <div className="space-y-3">
              {zones.map((zone) => (
                <div
                  key={zone.id}
                  className={cn(
                    "flex items-center justify-between p-3 lg:p-4 rounded-xl transition-colors",
                    zone.enabled ? "bg-secondary" : "bg-secondary/30",
                  )}
                >
                  <div>
                    <p className="font-medium text-foreground">{zone.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {zone.type === "paso" ? "Zona de paso" : "Recámara"}
                    </p>
                  </div>
                  <Switch checked={zone.enabled} onCheckedChange={() => handleZoneToggle(zone.id)} />
                </div>
              ))}
            </div>
          </div>

          {/* Pets setting */}
          <div className="rounded-2xl border border-border bg-background p-4 lg:p-5">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3 lg:gap-4">
                <div className="flex h-9 w-9 lg:h-10 lg:w-10 items-center justify-center rounded-xl bg-amber-50 flex-shrink-0">
                  <Dog className="h-4 w-4 lg:h-5 lg:w-5 text-amber-600" />
                </div>
                <div>
                  <h4 className="font-medium text-foreground text-sm lg:text-base">Detección de mascotas</h4>
                  <p className="text-xs lg:text-sm text-muted-foreground">Ignorar movimiento nocturno</p>
                </div>
              </div>
              <Switch checked={hasPets} onCheckedChange={setHasPets} />
            </div>
          </div>

          {/* Family members */}
          <div className="rounded-2xl border border-border bg-background p-4 lg:p-5">
            <h4 className="font-semibold text-foreground mb-3 lg:mb-4 flex items-center gap-2 text-sm lg:text-base">
              <Users className="h-4 w-4" />
              Miembros del hogar
            </h4>
            <p className="text-xs lg:text-sm text-muted-foreground mb-3 lg:mb-4">
              El sistema aprenderá los patrones nocturnos de cada miembro.
            </p>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 lg:p-4 rounded-xl bg-secondary">
                <div className="flex items-center gap-2.5 lg:gap-3">
                  <div className="h-9 w-9 lg:h-10 lg:w-10 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-medium text-sm">
                    A
                  </div>
                  <div>
                    <p className="font-medium text-foreground text-sm">Admin</p>
                    <p className="text-[10px] lg:text-xs text-muted-foreground">Adulto</p>
                  </div>
                </div>
                <span className="text-[10px] lg:text-xs text-emerald-600 font-medium">Aprendiendo...</span>
              </div>
            </div>
          </div>

          {/* Info card */}
          <div className="p-4 rounded-xl bg-blue-50 border border-blue-100 flex gap-3">
            <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-700">
              <p className="font-medium mb-1">Cómo funciona el modo nocturno</p>
              <p>
                El sistema utiliza cámaras y sensores para distinguir entre humanos y mascotas. Cuando detecta
                movimiento humano en zonas de paso (pasillos, baños), enciende las luces automáticamente. Los patrones
                se aprenden con el tiempo para optimizar el comportamiento.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
