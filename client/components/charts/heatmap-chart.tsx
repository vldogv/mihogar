"use client"

import { useState, useEffect } from "react"
import { cn } from "@/lib/utils"
import { useAuth } from "@/lib/auth/auth-context"
import { consumoService, type HorasPico } from "@/lib/services/consumo"

const hours = Array.from({ length: 24 }, (_, i) => i)

// Colors: green (low) → yellow (medium) → orange (high) → red (very high)
const getColor = (value: number, max: number) => {
  if (max === 0) return "bg-emerald-50"
  const pct = value / max
  if (pct > 0.8) return "bg-red-400"       // muy alto - alerta
  if (pct > 0.6) return "bg-orange-300"     // alto - cuidado
  if (pct > 0.4) return "bg-amber-200"      // medio
  if (pct > 0.2) return "bg-emerald-200"    // bajo - bien
  return "bg-emerald-50"                     // muy bajo - excelente
}

export function HeatmapChart() {
  const { session } = useAuth()
  const casaId = session?.casa_id_activa
  const [heatmapData, setHeatmapData] = useState<Record<string, number[]>>({})
  const [zones, setZones] = useState<string[]>([])
  const [maxValue, setMaxValue] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!casaId) return

    consumoService.getHorasPico(casaId).then((datos) => {
      // Group by zone, create 24-hour array
      const byZone: Record<string, number[]> = {}
      let max = 0

      datos.forEach((d) => {
        const name = d.zona_nombre || d.zona_id
        if (!byZone[name]) byZone[name] = new Array(24).fill(0)
        byZone[name][d.hora] = d.minutos_promedio
        if (d.minutos_promedio > max) max = d.minutos_promedio
      })

      setHeatmapData(byZone)
      setZones(Object.keys(byZone))
      setMaxValue(max)
      setLoading(false)
    }).catch((err) => {
      console.error("Error loading heatmap:", err)
      setLoading(false)
    })
  }, [casaId])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground text-sm">
        Cargando datos...
      </div>
    )
  }

  if (zones.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground text-sm">
        No hay datos disponibles
      </div>
    )
  }

  return (
    <div>
      <div className="mb-3">
        <h3 className="font-semibold text-foreground text-sm">Horas pico por habitación</h3>
        <p className="text-xs text-muted-foreground">Minutos de luz encendida por hora</p>
      </div>
      <div className="overflow-x-auto scrollbar-none">
        <div className="min-w-[480px]">
          {/* Header */}
          <div className="flex">
            <div className="w-20 flex-shrink-0" />
            <div className="flex-1 flex">
              {hours.map((hour) => (
                <div key={hour} className="flex-1 text-center text-[9px] text-muted-foreground py-1">
                  {hour.toString().padStart(2, "0")}
                </div>
              ))}
            </div>
          </div>

          {/* Rows */}
          {zones.map((zone) => (
            <div key={zone} className="flex items-center">
              <div className="w-20 flex-shrink-0 text-[10px] font-medium text-foreground py-0.5 pr-2 truncate">{zone}</div>
              <div className="flex-1 flex gap-px">
                {(heatmapData[zone] || []).map((value, i) => (
                  <div
                    key={i}
                    className={cn("flex-1 h-6 rounded-sm transition-colors", getColor(value, maxValue))}
                    title={`${zone} a las ${i}:00 — ${Math.round(value)} min`}
                  />
                ))}
              </div>
            </div>
          ))}

          {/* Legend */}
          <div className="flex items-center gap-3 mt-4 justify-center">
            <span className="text-[10px] text-muted-foreground">Bajo consumo</span>
            <div className="flex gap-0.5">
              <div className="w-5 h-3 rounded bg-emerald-50" />
              <div className="w-5 h-3 rounded bg-emerald-200" />
              <div className="w-5 h-3 rounded bg-amber-200" />
              <div className="w-5 h-3 rounded bg-orange-300" />
              <div className="w-5 h-3 rounded bg-red-400" />
            </div>
            <span className="text-[10px] text-muted-foreground">Alto consumo</span>
          </div>
        </div>
      </div>
    </div>
  )
}