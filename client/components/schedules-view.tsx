"use client"

import { useState, useEffect, useCallback } from "react"
import { AppShell } from "@/components/app-shell"
import { TimerCard } from "@/components/timer-card"
import { NightModeSettings } from "@/components/night-mode-settings"
import { Plus, Clock, Moon, Calendar } from "lucide-react"
import { useAuth } from "@/lib/auth/auth-context"
import { horariosService, type Temporizador } from "@/lib/services/horarios"
import { panelService, type Zona } from "@/lib/services/panel"
import { cn } from "@/lib/utils"

const dayMap: Record<string, string> = {
  lunes: "L", martes: "M", miercoles: "X", jueves: "J", viernes: "V", sabado: "S", domingo: "D",
}
const dayMapReverse: Record<string, string> = {
  L: "lunes", M: "martes", X: "miercoles", J: "jueves", V: "viernes", S: "sabado", D: "domingo",
}

function tempToDays(t: Temporizador): string[] {
  return Object.entries(t.dias)
    .filter(([, v]) => v)
    .map(([k]) => dayMap[k] || k)
}

export function SchedulesView() {
  const { session } = useAuth()
  const casaId = session?.casa_id_activa
  const [timers, setTimers] = useState<Temporizador[]>([])
  const [zones, setZones] = useState<Zona[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<"timers" | "night">("timers")
  const [showAddModal, setShowAddModal] = useState(false)
  const [newTimer, setNewTimer] = useState({
    zone: "",
    startTime: "18:00",
    endTime: "23:00",
    days: ["L", "M", "X", "J", "V"] as string[],
    type: "fixed" as "fixed" | "sensor",
  })

  const fetchData = useCallback(async () => {
    if (!casaId) return
    try {
      const [t, z] = await Promise.all([
        horariosService.getTemporizadores(casaId),
        panelService.getZonas(casaId),
      ])
      setTimers(t)
      setZones(z)
    } catch (err) {
      console.error("Error loading schedules:", err)
    } finally {
      setLoading(false)
    }
  }, [casaId])

  useEffect(() => { fetchData() }, [fetchData])

  const handleToggleTimer = async (timerId: string, current: boolean) => {
    try {
      await horariosService.updateTemporizador(timerId, { habilitado: !current })
      await fetchData()
    } catch (err) { console.error(err) }
  }

  const handleDeleteTimer = async (timerId: string) => {
    try {
      await horariosService.deleteTemporizador(timerId)
      await fetchData()
    } catch (err) { console.error(err) }
  }

  const handleAddTimer = async () => {
    if (!casaId || !newTimer.zone) return
    const dias: Record<string, boolean> = {}
    for (const d of ["L", "M", "X", "J", "V", "S", "D"]) {
      const key = dayMapReverse[d]
      if (key) dias[key] = newTimer.days.includes(d)
    }
    try {
      await horariosService.createTemporizador(casaId, {
        zona_id: newTimer.zone,
        tipo: newTimer.type === "sensor" ? "por_sensor" : "horario_fijo",
        hora_inicio: newTimer.startTime,
        hora_fin: newTimer.endTime,
        ...dias,
        solo_si_oscuro: newTimer.type === "sensor",
      } as any)
      setShowAddModal(false)
      setNewTimer({ zone: "", startTime: "18:00", endTime: "23:00", days: ["L", "M", "X", "J", "V"], type: "fixed" })
      await fetchData()
    } catch (err) { console.error(err) }
  }

  const toggleDay = (day: string) => {
    setNewTimer((prev) => ({
      ...prev,
      days: prev.days.includes(day) ? prev.days.filter((d) => d !== day) : [...prev.days, day],
    }))
  }

  // Map API timers to the format TimerCard expects
  const mappedTimers = timers.map((t) => ({
    id: t.id,
    zone: t.zona_id,
    zoneName: t.zona_nombre || "",
    startTime: t.hora_inicio,
    endTime: t.hora_fin,
    days: tempToDays(t),
    isActive: t.habilitado,
    type: t.tipo === "por_sensor" ? "sensor" as const : "fixed" as const,
    sensorCondition: t.solo_si_oscuro ? "dark" as const : undefined,
  }))
  const zonasPermitidas = session?.zonas_permitidas
  const visibleTimers = (session?.rol === "usuario" && zonasPermitidas?.length)
    ? mappedTimers.filter(t => zonasPermitidas.includes(t.zone))
    : mappedTimers
  const zonasParaTimer = (session?.rol === "usuario" && session?.zonas_permitidas?.length)
  ? zones.filter(z => session.zonas_permitidas!.includes(z.id))
  : zones

  if (loading) {
    return (
      <AppShell title="Horarios y Temporizadores" subtitle="Programa el encendido automático de las luces" currentPath="/schedules">
        <div className="flex items-center justify-center py-20">
          <div className="animate-pulse text-muted-foreground">Cargando horarios...</div>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell title="Horarios y Temporizadores" subtitle="Programa el encendido automático de las luces" currentPath="/schedules">
      <div className="flex gap-2 mb-4 lg:mb-6">
        <button
          onClick={() => setActiveTab("timers")}
          className={cn(
            "flex items-center gap-1.5 lg:gap-2 px-4 lg:px-5 py-2 lg:py-2.5 rounded-xl font-medium text-xs lg:text-sm transition-colors",
            activeTab === "timers" ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground hover:bg-secondary/80",
          )}
        >
          <Clock className="h-3.5 w-3.5 lg:h-4 lg:w-4" />
          Temporizadores
        </button>
        <button
          onClick={() => setActiveTab("night")}
          className={cn(
            "flex items-center gap-1.5 lg:gap-2 px-4 lg:px-5 py-2 lg:py-2.5 rounded-xl font-medium text-xs lg:text-sm transition-colors",
            activeTab === "night" ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground hover:bg-secondary/80",
          )}
        >
          <Moon className="h-3.5 w-3.5 lg:h-4 lg:w-4" />
          Modo Noche
        </button>
      </div>

      {activeTab === "timers" ? (
        <div className="space-y-6">
          <button
            onClick={() => setShowAddModal(true)}
            className="w-full flex items-center justify-center gap-2 px-5 py-4 rounded-2xl border-2 border-dashed border-border text-muted-foreground hover:border-primary hover:text-foreground transition-colors"
          >
            <Plus className="h-5 w-5" />
            <span className="font-medium">Agregar temporizador</span>
          </button>

          <div className="space-y-4">
            {visibleTimers.map((timer) => (
              <TimerCard
                key={timer.id}
                timer={timer}
                onToggle={() => handleToggleTimer(timer.id, timer.isActive)}
                onDelete={() => handleDeleteTimer(timer.id)}
              />
            ))}
          </div>

          {visibleTimers.length === 0 && (
            <div className="text-center py-12">
              <Calendar className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No hay temporizadores configurados</p>
            </div>
          )}

          <div className="p-4 rounded-xl bg-blue-50 border border-blue-100">
            <p className="text-sm text-blue-700">
              <strong>Nota:</strong> Los temporizadores tienen prioridad sobre el modo automático. Mientras un temporizador está activo, se ignoran los sensores de movimiento y luz.
            </p>
          </div>
        </div>
      ) : (
        <NightModeSettings />
      )}

      {/* Add Timer Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-foreground/20 backdrop-blur-sm" onClick={() => setShowAddModal(false)} />
          <div className="relative bg-background rounded-2xl shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-semibold text-foreground mb-6">Nuevo Temporizador</h3>
            <div className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Zona</label>
                
                <select
                  value={newTimer.zone}
                  onChange={(e) => setNewTimer((prev) => ({ ...prev, zone: e.target.value }))}
                  className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                >
                  <option value="">Seleccionar zona</option>
                  {zonasParaTimer.map((zone) => (
                    <option key={zone.id} value={zone.id}>{zone.nombre}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Tipo de temporizador</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => setNewTimer((prev) => ({ ...prev, type: "fixed" }))}
                    className={cn("px-4 py-3 rounded-xl text-sm font-medium transition-colors",
                      newTimer.type === "fixed" ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground")}
                  >
                    Horario fijo
                  </button>
                  <button
                    onClick={() => setNewTimer((prev) => ({ ...prev, type: "sensor" }))}
                    className={cn("px-4 py-3 rounded-xl text-sm font-medium transition-colors",
                      newTimer.type === "sensor" ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground")}
                  >
                    Por sensor
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Hora inicio</label>
                  <input type="time" value={newTimer.startTime} onChange={(e) => setNewTimer((prev) => ({ ...prev, startTime: e.target.value }))}
                    className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Hora fin</label>
                  <input type="time" value={newTimer.endTime} onChange={(e) => setNewTimer((prev) => ({ ...prev, endTime: e.target.value }))}
                    className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Días</label>
                <div className="flex gap-2">
                  {["L", "M", "X", "J", "V", "S", "D"].map((day) => (
                    <button key={day} onClick={() => toggleDay(day)}
                      className={cn("w-10 h-10 rounded-xl text-sm font-medium transition-colors",
                        newTimer.days.includes(day) ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground hover:bg-secondary/80")}>
                      {day}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-8">
              <button onClick={() => setShowAddModal(false)}
                className="flex-1 px-5 py-3 rounded-xl bg-secondary text-secondary-foreground font-medium text-sm hover:bg-secondary/80 transition-colors">
                Cancelar
              </button>
              <button onClick={handleAddTimer} disabled={!newTimer.zone}
                className="flex-1 px-5 py-3 rounded-xl bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 transition-colors disabled:opacity-50">
                Agregar
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  )
}
