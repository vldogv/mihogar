"use client"

import { useState, useEffect, useCallback } from "react"
import { AppShell } from "@/components/app-shell"
import { DailyConsumptionChart } from "@/components/charts/daily-consumption-chart"
import { HeatmapChart } from "@/components/charts/heatmap-chart"
import { BimonthlyChart } from "@/components/charts/bimonthly-chart"
import { AlertsPanel } from "@/components/alerts-panel"
import { BarChart3, Grid3x3, TrendingUp, Bell, Calendar, Zap, Clock, DollarSign, TrendingDown } from "lucide-react"
import { useAuth } from "@/lib/auth/auth-context"
import { consumoService, type ConsumoResumen } from "@/lib/services/consumo"
import { cn } from "@/lib/utils"
import { usePermissions } from "@/lib/hooks/use-permissions"

type ViewType = "daily" | "heatmap" | "bimonthly" | "alerts"

export function ReportsView() {
  const { session } = useAuth()
  const casaId = session?.casa_id_activa
  const [activeView, setActiveView] = useState<ViewType>("daily")
  const [resumen, setResumen] = useState<ConsumoResumen | null>(null)
  const [loading, setLoading] = useState(true)
  const perms = usePermissions()

  const fetchResumen = useCallback(async () => {
    if (!casaId) return
    try {
      const data = await consumoService.getResumen(casaId)
      setResumen(data)
    } catch (err) {
      console.error("Error loading consumption:", err)
    } finally {
      setLoading(false)
    }
  }, [casaId])

  useEffect(() => { fetchResumen() }, [fetchResumen])

  const views = [
    { id: "daily" as const, label: "Consumo Diario", icon: BarChart3 },
    { id: "heatmap" as const, label: "Horas Pico", icon: Grid3x3 },
    { id: "bimonthly" as const, label: "Bimestral", icon: TrendingUp },
    { id: "alerts" as const, label: "Alertas", icon: Bell },
  ]

  return (
    <AppShell title="Consumo y Reportes" subtitle="Monitorea el uso de energía" currentPath="/reports">
      <div className="space-y-5">
        {/* Summary cards - from API */}
        {resumen && (
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-border bg-background p-4">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="h-5 w-5 text-blue-500" />
              </div>
              <p className="text-xl font-bold text-foreground">{resumen.consumo_hoy_kwh.toFixed(2)} <span className="text-sm font-normal text-muted-foreground">kWh</span></p>
              <p className="text-xs text-muted-foreground">Consumo hoy</p>
            </div>
            <div className="rounded-xl border border-border bg-background p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingDown className="h-5 w-5 text-emerald-500" />
              </div>
              <p className="text-xl font-bold text-foreground">{resumen.bimestre_kwh.toFixed(1)} <span className="text-sm font-normal text-muted-foreground">kWh</span></p>
              <p className="text-xs text-muted-foreground">Este bimestre</p>
            </div>
            <div className="rounded-xl border border-border bg-background p-4">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="h-5 w-5 text-blue-500" />
              </div>
              <p className="text-xl font-bold text-foreground">{resumen.horas_uso_dia_promedio.toFixed(1)} <span className="text-sm font-normal text-muted-foreground">hrs/día</span></p>
              <p className="text-xs text-muted-foreground">Horas de uso</p>
            </div>
            <div className="rounded-xl border border-border bg-background p-4">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="h-5 w-5 text-amber-500" />
              </div>
              <p className="text-xl font-bold text-foreground">${resumen.bimestre_costo.toFixed(0)} <span className="text-sm font-normal text-muted-foreground">MXN</span></p>
              <p className="text-xs text-muted-foreground">Costo estimado</p>
            </div>
          </div>
        )}

        {loading && (
          <div className="grid grid-cols-2 gap-3">
            {[1,2,3,4].map((i) => (
              <div key={i} className="rounded-xl border border-border bg-background p-4 animate-pulse">
                <div className="h-5 w-5 bg-secondary rounded mb-2" />
                <div className="h-6 w-20 bg-secondary rounded mb-1" />
                <div className="h-3 w-16 bg-secondary rounded" />
              </div>
            ))}
          </div>
        )}

        {/* CFE Cutoff */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">Corte CFE</span>
          </div>
          {perms.isAdmin ? (
            <select
              value={resumen?.corte_cfe_dia || 15}
              onChange={async (e) => {
                if (!casaId) return
                try {
                  await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api'}/casas/${casaId}/config`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("mihogar_token")}` },
                    body: JSON.stringify({ corte_cfe_dia: Number(e.target.value) }),
                  })
                  fetchResumen()
                } catch (err) { console.error(err) }
              }}
              className="px-3 py-1.5 rounded-lg border border-border bg-background text-xs focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              {Array.from({ length: 31 }, (_, i) => i + 1).map((day) => (
                <option key={day} value={day}>Día {day}</option>
              ))}
            </select>
          ) : (
            <span className="text-xs font-medium text-foreground">Día {resumen?.corte_cfe_dia || 15}</span>
          )}
        </div>
        
        {/* View tabs */}
        <div className="flex gap-2 overflow-x-auto scrollbar-none">
          {views.map((view) => (
            <button
              key={view.id}
              onClick={() => setActiveView(view.id)}
              className={cn(
                "flex items-center gap-1.5 px-4 py-2.5 rounded-xl font-medium text-xs transition-colors whitespace-nowrap min-h-[44px]",
                activeView === view.id
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground active:bg-secondary/80",
              )}
            >
              <view.icon className="h-4 w-4" />
              {view.label}
            </button>
          ))}
        </div>

        {/* Charts - these still use their own mock data for now, but the summary is real */}
        <section>
          {activeView === "daily" && <DailyConsumptionChart />}
          {activeView === "heatmap" && <HeatmapChart />}
          {activeView === "bimonthly" && <BimonthlyChart />}
          {activeView === "alerts" && <AlertsPanel />}
        </section>
      </div>
    </AppShell>
  )
}
