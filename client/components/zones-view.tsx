"use client"

import { useState, useEffect, useCallback } from "react"
import { AppShell } from "@/components/app-shell"
import { ZoneDetailCard } from "@/components/zone-detail-card"
import { Slider } from "@/components/ui/slider"
import { useAuth } from "@/lib/auth/auth-context"
import { panelService, type PanelData } from "@/lib/services/panel"

export function ZonesView() {
  const { session } = useAuth()
  const casaId = session?.casa_id_activa
  const [panelData, setPanelData] = useState<PanelData | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedZone, setSelectedZone] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    if (!casaId) return
    try {
      const data = await panelService.getPanel(casaId)
      setPanelData(data)
    } catch (err) {
      console.error("Error loading zones:", err)
    } finally {
      setLoading(false)
    }
  }, [casaId])

  useEffect(() => { fetchData() }, [fetchData])

  const handleToggle = async (zonaId: string, currentState: boolean) => {
    try {
      await panelService.toggleZona(zonaId, !currentState)
      await fetchData()
    } catch (err) { console.error(err) }
  }

  const handleModeChange = async (zonaId: string, mode: "auto" | "manual" | "timer") => {
    const modeMap: Record<string, string> = { auto: "automatico", manual: "manual", timer: "temporizador" }
    try {
      await panelService.cambiarModo(zonaId, modeMap[mode])
      await fetchData()
    } catch (err) { console.error(err) }
  }

  const handleThresholdChange = async (zonaId: string, value: number) => {
    try {
      await panelService.updateConfigZona(zonaId, { umbral_oscuridad: value })
      await fetchData()
    } catch (err) { console.error(err) }
  }

  const handleAutoOffChange = async (zonaId: string, seconds: number) => {
    try {
      await panelService.updateConfigZona(zonaId, { tiempo_apagado_auto: seconds })
      await fetchData()
    } catch (err) { console.error(err) }
  }

  if (loading) {
    return (
      <AppShell title="Control de Zonas" subtitle="Gestiona cada zona de tu hogar" currentPath="/zones">
        <div className="flex items-center justify-center py-20">
          <div className="animate-pulse text-muted-foreground">Cargando zonas...</div>
        </div>
      </AppShell>
    )
  }

  const allZones = (panelData?.zonas || []).map((z) => {
    const modeMap: Record<string, "auto" | "manual" | "timer"> = {
      automatico: "auto", manual: "manual", temporizador: "timer",
    }
    return {
      id: z.zona.id,
      name: z.zona.nombre,
      isOn: z.config?.encendida || false,
      mode: modeMap[z.config?.modo || "automatico"] || ("auto" as const),
      movement: z.config?.movimiento_detectado || false,
      lux: z.config?.luz_ambiente_actual ?? 0,
      darknessThreshold: z.config?.umbral_oscuridad ?? 40,
      autoOff: z.config?.tiempo_apagado_auto ?? 60,
    }
  })

const zonasPermitidas = session?.zonas_permitidas
  const zones = (session?.rol === "usuario" && zonasPermitidas?.length)
    ? allZones.filter(z => zonasPermitidas.includes(z.id))
    : allZones

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
          <select
            value={selected.autoOff}
            onChange={(e) => handleAutoOffChange(selected.id, Number(e.target.value))}
            className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
          >
            <option value={60}>1 minuto</option>
            <option value={180}>3 minutos</option>
            <option value={300}>5 minutos</option>
            <option value={600}>10 minutos</option>
          </select>
        </div>
      </div>
    </div>
  ) : null

  return (
    <AppShell title="Control de Zonas" subtitle="Gestiona cada zona de tu hogar" currentPath="/zones">
      <div className="space-y-3">
        {zones.map((zone) => (
          <div key={zone.id}>
            <ZoneDetailCard
              zone={zone}
              isSelected={selectedZone === zone.id}
              onSelect={() => setSelectedZone(selectedZone === zone.id ? null : zone.id)}
              onToggle={() => handleToggle(zone.id, zone.isOn)}
              onModeChange={(mode) => handleModeChange(zone.id, mode)}
            />
            {selectedZone === zone.id && settingsPanel && <div className="mt-3">{settingsPanel}</div>}
          </div>
        ))}
      </div>
    </AppShell>
  )
}
