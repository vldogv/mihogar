"use client"

import { useState } from "react"
import { AppShell } from "@/components/app-shell"
import { DailyConsumptionChart } from "@/components/charts/daily-consumption-chart"
import { HeatmapChart } from "@/components/charts/heatmap-chart"
import { BimonthlyChart } from "@/components/charts/bimonthly-chart"
import { ConsumptionSummary } from "@/components/consumption-summary"
import { AlertsPanel } from "@/components/alerts-panel"
import { BarChart3, Grid3x3, TrendingUp, Bell, Calendar } from "lucide-react"
import { cn } from "@/lib/utils"

type ViewType = "daily" | "heatmap" | "bimonthly" | "alerts"

export function ReportsView() {
  const [activeView, setActiveView] = useState<ViewType>("daily")
  const [cutoffDate, setCutoffDate] = useState("15")

  const views = [
    { id: "daily" as const, label: "Consumo Diario", icon: BarChart3 },
    { id: "heatmap" as const, label: "Horas Pico", icon: Grid3x3 },
    { id: "bimonthly" as const, label: "Bimestral", icon: TrendingUp },
    { id: "alerts" as const, label: "Alertas", icon: Bell },
  ]

  return (
    <AppShell title="Consumo y Reportes" subtitle="Monitorea el uso de energía" currentPath="/reports">
      <div className="space-y-5">
        {/* Summary cards */}
        <ConsumptionSummary />

        {/* CFE Cutoff date - compact inline */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">Corte CFE</span>
          </div>
          <select
            value={cutoffDate}
            onChange={(e) => setCutoffDate(e.target.value)}
            className="px-3 py-1.5 rounded-lg border border-border bg-background text-xs focus:outline-none focus:ring-2 focus:ring-primary/20"
          >
            {Array.from({ length: 28 }, (_, i) => i + 1).map((day) => (
              <option key={day} value={day}>
                Día {day}
              </option>
            ))}
          </select>
        </div>

        {/* View tabs - full width, proper spacing */}
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

        {/* Chart section - no container card, direct render */}
        <section>
          {activeView === "daily" && <DailyConsumptionChart />}
          {activeView === "heatmap" && <HeatmapChart />}
          {activeView === "bimonthly" && <BimonthlyChart />}
          {activeView === "alerts" && <AlertsPanel />}
        </section>

        {/* Divider */}
        <div className="border-t border-border" />

        {/* Usage summary - clean list without card wrapper */}
        <section>
          <h3 className="font-semibold text-foreground mb-3 text-sm">Uso promedio por día</h3>
          <div className="space-y-0">
            {[
              { zone: "Sala", hours: 4.2, kwh: 0.42, night: "15%" },
              { zone: "Cocina", hours: 3.5, kwh: 0.35, night: "10%" },
              { zone: "Recámara Principal", hours: 1.8, kwh: 0.18, night: "85%" },
              { zone: "Recámara 2", hours: 2.1, kwh: 0.21, night: "80%" },
              { zone: "Pasillo", hours: 0.8, kwh: 0.08, night: "60%" },
              { zone: "Baño", hours: 0.5, kwh: 0.05, night: "40%" },
            ].map((row) => (
              <div key={row.zone} className="flex items-center justify-between py-3 border-b border-border/50 last:border-0">
                <div>
                  <p className="text-sm font-medium text-foreground">{row.zone}</p>
                  <p className="text-xs text-muted-foreground">{row.hours}h/día</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-foreground">{row.kwh} kWh</p>
                  <p className="text-xs text-muted-foreground">{row.night} nocturno</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  )
}
