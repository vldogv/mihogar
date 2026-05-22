"use client"

import { useState } from "react"
import { AppShell } from "@/components/app-shell"
import { ZoneDetailCard } from "@/components/zone-detail-card"
import { Slider } from "@/components/ui/slider"

const initialZones = [
  { id: "sala", name: "Sala", isOn: true, mode: "auto" as const, movement: true, lux: 35, darknessThreshold: 40 },
  {
    id: "recamara-principal",
    name: "Recámara Principal",
    isOn: false,
    mode: "manual" as const,
    movement: false,
    lux: 80,
    darknessThreshold: 50,
  },
  {
    id: "recamara-2",
    name: "Recámara 2",
    isOn: false,
    mode: "auto" as const,
    movement: false,
    lux: 75,
    darknessThreshold: 40,
  },
  { id: "cocina", name: "Cocina", isOn: true, mode: "timer" as const, movement: true, lux: 20, darknessThreshold: 30 },
  {
    id: "pasillo",
    name: "Pasillo",
    isOn: false,
    mode: "auto" as const,
    movement: false,
    lux: 45,
    darknessThreshold: 45,
  },
  { id: "bano", name: "Baño", isOn: false, mode: "auto" as const, movement: false, lux: 60, darknessThreshold: 35 },
]

export function ZonesView() {
  const [zones, setZones] = useState(initialZones)
  const [selectedZone, setSelectedZone] = useState<string | null>(null)

  const handleToggle = (zoneId: string) => {
    setZones((prev) => prev.map((z) => (z.id === zoneId ? { ...z, isOn: !z.isOn } : z)))
  }

  const handleModeChange = (zoneId: string, mode: "auto" | "manual" | "timer") => {
    setZones((prev) => prev.map((z) => (z.id === zoneId ? { ...z, mode } : z)))
  }

  const handleThresholdChange = (zoneId: string, value: number) => {
    setZones((prev) => prev.map((z) => (z.id === zoneId ? { ...z, darknessThreshold: value } : z)))
  }

  const selected = zones.find((z) => z.id === selectedZone)

  const settingsPanel = selected ? (
    <div className="rounded-2xl border border-border bg-background p-5 lg:p-6">
      <h3 className="font-semibold text-foreground mb-1">{selected.name}</h3>
      <p className="text-sm text-muted-foreground mb-5 lg:mb-6">Configuración de sensores</p>

      <div className="space-y-5 lg:space-y-6">
        <div>
          <label className="block text-sm font-medium text-foreground mb-3">
            Umbral de oscuridad: {selected.darknessThreshold}%
          </label>
          <Slider
            value={[selected.darknessThreshold]}
            onValueChange={([v]) => handleThresholdChange(selected.id, v)}
            max={100}
            step={5}
            className="w-full"
          />
          <p className="text-xs text-muted-foreground mt-2">
            La luz se enciende cuando el nivel de luz ambiente está por debajo de este valor.
          </p>
        </div>

        <div className="p-3 lg:p-4 rounded-xl bg-secondary/50">
          <p className="text-sm font-medium text-foreground mb-2">Estado actual</p>
          <div className="space-y-1.5 text-sm text-muted-foreground">
            <p>Luz ambiente: {selected.lux}%</p>
            <p>Movimiento: {selected.movement ? "Detectado" : "Sin movimiento"}</p>
            <p>
              Se encendería:{" "}
              <span className={selected.lux < selected.darknessThreshold ? "text-emerald-600 font-medium" : ""}>
                {selected.lux < selected.darknessThreshold ? "Sí" : "No"}
              </span>
            </p>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-3">Tiempo de apagado automático</label>
          <select className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20">
            <option value="1">1 minuto</option>
            <option value="3">3 minutos</option>
            <option value="5">5 minutos</option>
            <option value="10">10 minutos</option>
          </select>
        </div>
      </div>
    </div>
  ) : null

  return (
    <AppShell title="Control de Zonas" subtitle="Gestiona cada zona de tu hogar" currentPath="/zones">
      {/* Single column vertical layout - mobile first */}
      <div className="space-y-3">
        {zones.map((zone) => (
          <div key={zone.id}>
            <ZoneDetailCard
              zone={zone}
              isSelected={selectedZone === zone.id}
              onSelect={() => setSelectedZone(selectedZone === zone.id ? null : zone.id)}
              onToggle={() => handleToggle(zone.id)}
              onModeChange={(mode) => handleModeChange(zone.id, mode)}
              isOnline={true}
            />
            {/* Show settings panel directly below selected zone */}
            {selectedZone === zone.id && settingsPanel && (
              <div className="mt-3">
                {settingsPanel}
              </div>
            )}
          </div>
        ))}
      </div>
    </AppShell>
  )
}
