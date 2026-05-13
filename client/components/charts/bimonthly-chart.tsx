"use client"

import { useState, useEffect } from "react"
import { Line, LineChart, ResponsiveContainer, XAxis, YAxis, Tooltip, Legend } from "recharts"
import { TrendingDown, TrendingUp } from "lucide-react"
import { useAuth } from "@/lib/auth/auth-context"
import { consumoService, type ConsumoBimestral } from "@/lib/services/consumo"

const bimestreLabels = ["Ene-Feb", "Mar-Abr", "May-Jun", "Jul-Ago", "Sep-Oct", "Nov-Dic"]

interface TooltipProps {
  active?: boolean
  payload?: Array<{ dataKey: string; value: number; stroke: string }>
  label?: string
}

function CustomTooltip({ active, payload, label }: TooltipProps) {
  if (!active || !payload || payload.length === 0) return null
  return (
    <div className="rounded-lg border border-border bg-background p-2 shadow-md">
      <p className="text-xs font-medium text-foreground mb-1">{label}</p>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="flex items-center gap-2 text-xs">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.stroke }} />
          <span className="text-muted-foreground">{entry.dataKey === "kwh" ? "Consumo" : "Costo"}:</span>
          <span className="font-medium text-foreground">
            {entry.dataKey === "costo" ? `$${entry.value.toFixed(0)}` : `${entry.value.toFixed(1)} kWh`}
          </span>
        </div>
      ))}
    </div>
  )
}

export function BimonthlyChart() {
  const { session } = useAuth()
  const casaId = session?.casa_id_activa
  const [chartData, setChartData] = useState<any[]>([])
  const [savings, setSavings] = useState<{ pct: number; amount: number; isPositive: boolean } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!casaId) return

    consumoService.getBimestral(casaId).then((datos) => {
      // Sort by year and bimestre
      const sorted = [...datos].sort((a, b) => {
        if (a.anio !== b.anio) return a.anio - b.anio
        return a.bimestre - b.bimestre
      })

      const mapped = sorted.map((d) => ({
        period: `${bimestreLabels[d.bimestre - 1] || `B${d.bimestre}`} ${d.anio}`,
        kwh: d.kwh_total,
        costo: d.costo_estimado,
        horas: d.horas_uso_dia,
      }))

      setChartData(mapped)

      // Calculate savings (last vs first)
      if (sorted.length >= 2) {
        const first = sorted[0]
        const last = sorted[sorted.length - 1]
        const diff = last.costo_estimado - first.costo_estimado
        const pct = ((last.kwh_total - first.kwh_total) / first.kwh_total) * 100
        setSavings({
          pct: Math.abs(pct),
          amount: Math.abs(diff),
          isPositive: diff < 0, // negative diff = savings
        })
      }

      setLoading(false)
    }).catch((err) => {
      console.error("Error loading bimonthly:", err)
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
        No hay datos bimestrales disponibles
      </div>
    )
  }

  return (
    <div>
      <div className="mb-3">
        <h3 className="font-semibold text-foreground text-sm">Comparativa bimestral</h3>
        <p className="text-xs text-muted-foreground">Consumo y costo por bimestre</p>
      </div>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <XAxis
              dataKey="period"
              tickLine={false}
              axisLine={false}
              tick={{ fill: "var(--muted-foreground)", fontSize: 10 }}
              angle={-20}
              textAnchor="end"
              height={40}
            />
            <YAxis
              yAxisId="left"
              tickLine={false}
              axisLine={false}
              tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
              width={35}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tickLine={false}
              axisLine={false}
              tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
              tickFormatter={(value) => `$${value}`}
              width={45}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              formatter={(value: string) => value === "kwh" ? "Consumo (kWh)" : "Costo (MXN)"}
              wrapperStyle={{ fontSize: "11px" }}
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="kwh"
              stroke="#1D9E75"
              strokeWidth={2.5}
              dot={{ fill: "#1D9E75", r: 4 }}
              activeDot={{ r: 6 }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="costo"
              stroke="#BA7517"
              strokeWidth={2.5}
              dot={{ fill: "#BA7517", r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Savings indicator */}
      {savings && (
        <div className={`mt-4 p-3 rounded-lg border ${savings.isPositive ? "bg-emerald-50 border-emerald-100" : "bg-red-50 border-red-100"}`}>
          <div className="flex items-center gap-2">
            {savings.isPositive ? (
              <TrendingDown className="h-4 w-4 text-emerald-600" />
            ) : (
              <TrendingUp className="h-4 w-4 text-red-600" />
            )}
            <p className={`text-xs font-medium ${savings.isPositive ? "text-emerald-700" : "text-red-700"}`}>
              {savings.isPositive ? "Ahorro" : "Aumento"}: {savings.pct.toFixed(0)}% vs primer bimestre (~${savings.amount.toFixed(0)} MXN/bimestre)
            </p>
          </div>
        </div>
      )}
    </div>
  )
}