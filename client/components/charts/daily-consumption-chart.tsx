"use client"

import { useState, useEffect } from "react"
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, Legend } from "recharts"
import { useAuth } from "@/lib/auth/auth-context"
import { consumoService, type ConsumoDiario } from "@/lib/services/consumo"

const colorPalette = [
  "#1D9E75", // teal
  "#378ADD", // blue
  "#D85A30", // coral
  "#534AB7", // purple
  "#BA7517", // amber
  "#D4537E", // pink
]

interface TooltipProps {
  active?: boolean
  payload?: Array<{ dataKey: string; value: number; fill: string }>
  label?: string
}

function CustomTooltip({ active, payload, label }: TooltipProps) {
  if (!active || !payload || payload.length === 0) return null
  return (
    <div className="rounded-lg border border-border bg-background p-2 shadow-md">
      <p className="text-xs font-medium text-foreground mb-1">{label}</p>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="flex items-center gap-2 text-xs">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.fill }} />
          <span className="text-muted-foreground">{entry.dataKey}:</span>
          <span className="font-medium text-foreground">{entry.value.toFixed(2)} kWh</span>
        </div>
      ))}
    </div>
  )
}

export function DailyConsumptionChart() {
  const { session } = useAuth()
  const casaId = session?.casa_id_activa
  const [chartData, setChartData] = useState<any[]>([])
  const [zonaNames, setZonaNames] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!casaId) return
    const now = new Date()
    const desde = new Date(now)
    desde.setDate(desde.getDate() - 7)
    const desdeStr = desde.toISOString().split("T")[0]
    const hastaStr = now.toISOString().split("T")[0]

    consumoService.getDiario(casaId, desdeStr, hastaStr).then((datos) => {
      // Group by date, pivot zones as columns
      const dayNames = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
      const byDate: Record<string, Record<string, number>> = {}
      const zones = new Set<string>()

      datos.forEach((d) => {
        const name = d.zona_nombre || d.zona_id
        zones.add(name)
        if (!byDate[d.fecha]) byDate[d.fecha] = {}
        byDate[d.fecha][name] = d.kwh_total
      })

      const zonaList = Array.from(zones)
      setZonaNames(zonaList)

      const sorted = Object.entries(byDate).sort(([a], [b]) => a.localeCompare(b))
      const mapped = sorted.map(([fecha, vals]) => {
        const date = new Date(fecha + "T12:00:00")
        const row: any = { day: dayNames[date.getDay()] }
        zonaList.forEach((z) => { row[z] = vals[z] || 0 })
        return row
      })

      setChartData(mapped)
      setLoading(false)
    }).catch((err) => {
      console.error("Error loading daily consumption:", err)
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

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground text-sm">
        No hay datos disponibles
      </div>
    )
  }

  return (
    <div>
      <div className="mb-3">
        <h3 className="font-semibold text-foreground text-sm">Consumo diario por zona</h3>
        <p className="text-xs text-muted-foreground">kWh consumidos por zona</p>
      </div>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 0, right: 0, left: -10, bottom: 0 }}>
            <XAxis dataKey="day" tickLine={false} axisLine={false} tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
            <YAxis tickLine={false} axisLine={false} tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} width={30} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: "11px", whiteSpace: "normal", lineHeight: "1.6" }} />
            {zonaNames.map((zona, i) => (
              <Bar
                key={zona}
                dataKey={zona}
                stackId="a"
                fill={colorPalette[i % colorPalette.length]}
                radius={i === zonaNames.length - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}