"use client"

import { Zap, TrendingDown, Clock, DollarSign } from "lucide-react"

const summaryData = [
  {
    label: "Consumo hoy",
    value: "1.29",
    unit: "kWh",
    icon: Zap,
    color: "bg-amber-50 text-amber-600",
  },
  {
    label: "Este bimestre",
    value: "42.5",
    unit: "kWh",
    icon: TrendingDown,
    color: "bg-emerald-50 text-emerald-600",
    change: "-12%",
  },
  {
    label: "Horas de uso",
    value: "12.9",
    unit: "hrs/día",
    icon: Clock,
    color: "bg-blue-50 text-blue-600",
  },
  {
    label: "Costo estimado",
    value: "$156",
    unit: "MXN",
    icon: DollarSign,
    color: "bg-primary/10 text-primary",
  },
]

export function ConsumptionSummary() {
  if (!summaryData || summaryData.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-background p-4 text-center text-muted-foreground text-sm">
        No hay datos disponibles
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 gap-3">
      {summaryData.map((item) => (
        <div key={item.label} className="rounded-xl border border-border bg-background p-3">
          <div className="flex items-center justify-between mb-2">
            <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${item.color}`}>
              <item.icon className="h-4 w-4" />
            </div>
            {item.change && (
              <span className="text-[10px] font-medium text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-full">
                {item.change}
              </span>
            )}
          </div>
          <p className="text-lg font-bold text-foreground leading-tight">
            {item.value}
            <span className="text-xs font-normal text-muted-foreground ml-0.5">{item.unit}</span>
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">{item.label}</p>
        </div>
      ))}
    </div>
  )
}
