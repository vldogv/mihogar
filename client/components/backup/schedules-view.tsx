"use client"

import { useState } from "react"
import { AppShell } from "@/components/app-shell"
import { TimerCard } from "@/components/timer-card"
import { NightModeSettings } from "@/components/night-mode-settings"
import { Plus, Clock, Moon, Calendar } from "lucide-react"
import { cn } from "@/lib/utils"

interface Timer {
  id: string
  zone: string
  zoneName: string
  startTime: string
  endTime: string
  days: string[]
  isActive: boolean
  type: "fixed" | "sensor"
  sensorCondition?: "dark" | "light"
}

const initialTimers: Timer[] = [
  {
    id: "1",
    zone: "sala",
    zoneName: "Sala",
    startTime: "18:00",
    endTime: "23:00",
    days: ["L", "M", "X", "J", "V"],
    isActive: true,
    type: "sensor",
    sensorCondition: "dark",
  },
  {
    id: "2",
    zone: "cocina",
    zoneName: "Cocina",
    startTime: "06:00",
    endTime: "08:00",
    days: ["L", "M", "X", "J", "V", "S", "D"],
    isActive: true,
    type: "fixed",
  },
  {
    id: "3",
    zone: "recamara-principal",
    zoneName: "Recámara Principal",
    startTime: "22:00",
    endTime: "06:00",
    days: ["L", "M", "X", "J", "V", "S", "D"],
    isActive: false,
    type: "fixed",
  },
]

const zones = [
  { id: "sala", name: "Sala" },
  { id: "recamara-principal", name: "Recámara Principal" },
  { id: "recamara-2", name: "Recámara 2" },
  { id: "cocina", name: "Cocina" },
  { id: "pasillo", name: "Pasillo" },
  { id: "bano", name: "Baño" },
]

export function SchedulesView() {
  const [timers, setTimers] = useState(initialTimers)
  const [activeTab, setActiveTab] = useState<"timers" | "night">("timers")
  const [showAddModal, setShowAddModal] = useState(false)
  const [newTimer, setNewTimer] = useState<Partial<Timer>>({
    zone: "",
    startTime: "18:00",
    endTime: "23:00",
    days: ["L", "M", "X", "J", "V"],
    type: "fixed",
  })

  const handleToggleTimer = (timerId: string) => {
    setTimers((prev) => prev.map((t) => (t.id === timerId ? { ...t, isActive: !t.isActive } : t)))
  }

  const handleDeleteTimer = (timerId: string) => {
    setTimers((prev) => prev.filter((t) => t.id !== timerId))
  }

  const handleAddTimer = () => {
    if (!newTimer.zone) return
    const zone = zones.find((z) => z.id === newTimer.zone)
    const timer: Timer = {
      id: Date.now().toString(),
      zone: newTimer.zone,
      zoneName: zone?.name || "",
      startTime: newTimer.startTime || "18:00",
      endTime: newTimer.endTime || "23:00",
      days: newTimer.days || [],
      isActive: true,
      type: newTimer.type || "fixed",
      sensorCondition: newTimer.type === "sensor" ? "dark" : undefined,
    }
    setTimers((prev) => [...prev, timer])
    setShowAddModal(false)
    setNewTimer({
      zone: "",
      startTime: "18:00",
      endTime: "23:00",
      days: ["L", "M", "X", "J", "V"],
      type: "fixed",
    })
  }

  const toggleDay = (day: string) => {
    setNewTimer((prev) => ({
      ...prev,
      days: prev.days?.includes(day) ? prev.days.filter((d) => d !== day) : [...(prev.days || []), day],
    }))
  }

  return (
    <AppShell
      title="Horarios y Temporizadores"
      subtitle="Programa el encendido automático de las luces"
      currentPath="/schedules"
    >
      {/* Tabs */}
      <div className="flex gap-2 mb-4 lg:mb-6">
        <button
          onClick={() => setActiveTab("timers")}
          className={cn(
            "flex items-center gap-1.5 lg:gap-2 px-4 lg:px-5 py-2 lg:py-2.5 rounded-xl font-medium text-xs lg:text-sm transition-colors",
            activeTab === "timers"
              ? "bg-primary text-primary-foreground"
              : "bg-secondary text-secondary-foreground hover:bg-secondary/80",
          )}
        >
          <Clock className="h-3.5 w-3.5 lg:h-4 lg:w-4" />
          Temporizadores
        </button>
        <button
          onClick={() => setActiveTab("night")}
          className={cn(
            "flex items-center gap-1.5 lg:gap-2 px-4 lg:px-5 py-2 lg:py-2.5 rounded-xl font-medium text-xs lg:text-sm transition-colors",
            activeTab === "night"
              ? "bg-primary text-primary-foreground"
              : "bg-secondary text-secondary-foreground hover:bg-secondary/80",
          )}
        >
          <Moon className="h-3.5 w-3.5 lg:h-4 lg:w-4" />
          Modo Noche
        </button>
      </div>

      {activeTab === "timers" ? (
        <div className="space-y-6">
          {/* Add timer button */}
          <button
            onClick={() => setShowAddModal(true)}
            className="w-full flex items-center justify-center gap-2 px-5 py-4 rounded-2xl border-2 border-dashed border-border text-muted-foreground hover:border-primary hover:text-foreground transition-colors"
          >
            <Plus className="h-5 w-5" />
            <span className="font-medium">Agregar temporizador</span>
          </button>

          {/* Timers list */}
          <div className="space-y-4">
            {timers.map((timer) => (
              <TimerCard
                key={timer.id}
                timer={timer}
                onToggle={() => handleToggleTimer(timer.id)}
                onDelete={() => handleDeleteTimer(timer.id)}
                isOnline={true}
              />
            ))}
          </div>

          {timers.length === 0 && (
            <div className="text-center py-12">
              <Calendar className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No hay temporizadores configurados</p>
            </div>
          )}

          <div className="p-4 rounded-xl bg-blue-50 border border-blue-100">
            <p className="text-sm text-blue-700">
              <strong>Nota:</strong> Los temporizadores tienen prioridad sobre el modo automático. Mientras un
              temporizador está activo, se ignoran los sensores de movimiento y luz.
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
              {/* Zone selector */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Zona</label>
                <select
                  value={newTimer.zone}
                  onChange={(e) => setNewTimer((prev) => ({ ...prev, zone: e.target.value }))}
                  className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                >
                  <option value="">Seleccionar zona</option>
                  {zones.map((zone) => (
                    <option key={zone.id} value={zone.id}>
                      {zone.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Timer type */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Tipo de temporizador</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => setNewTimer((prev) => ({ ...prev, type: "fixed" }))}
                    className={cn(
                      "px-4 py-3 rounded-xl text-sm font-medium transition-colors",
                      newTimer.type === "fixed"
                        ? "bg-primary text-primary-foreground"
                        : "bg-secondary text-secondary-foreground",
                    )}
                  >
                    Horario fijo
                  </button>
                  <button
                    onClick={() => setNewTimer((prev) => ({ ...prev, type: "sensor" }))}
                    className={cn(
                      "px-4 py-3 rounded-xl text-sm font-medium transition-colors",
                      newTimer.type === "sensor"
                        ? "bg-primary text-primary-foreground"
                        : "bg-secondary text-secondary-foreground",
                    )}
                  >
                    Por sensor
                  </button>
                </div>
              </div>

              {newTimer.type === "sensor" && (
                <div className="p-3 rounded-xl bg-amber-50 border border-amber-100">
                  <p className="text-xs text-amber-700">
                    El temporizador solo encenderá la luz si está oscuro (sensor crepuscular por debajo del umbral
                    configurado en la zona).
                  </p>
                </div>
              )}

              {/* Time inputs */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Hora inicio</label>
                  <input
                    type="time"
                    value={newTimer.startTime}
                    onChange={(e) => setNewTimer((prev) => ({ ...prev, startTime: e.target.value }))}
                    className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Hora fin</label>
                  <input
                    type="time"
                    value={newTimer.endTime}
                    onChange={(e) => setNewTimer((prev) => ({ ...prev, endTime: e.target.value }))}
                    className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>
              </div>

              {/* Days selector */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Días</label>
                <div className="flex gap-2">
                  {["L", "M", "X", "J", "V", "S", "D"].map((day) => (
                    <button
                      key={day}
                      onClick={() => toggleDay(day)}
                      className={cn(
                        "w-10 h-10 rounded-xl text-sm font-medium transition-colors",
                        newTimer.days?.includes(day)
                          ? "bg-primary text-primary-foreground"
                          : "bg-secondary text-secondary-foreground hover:bg-secondary/80",
                      )}
                    >
                      {day}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 mt-8">
              <button
                onClick={() => setShowAddModal(false)}
                className="flex-1 px-5 py-3 rounded-xl bg-secondary text-secondary-foreground font-medium text-sm hover:bg-secondary/80 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleAddTimer}
                disabled={!newTimer.zone}
                className="flex-1 px-5 py-3 rounded-xl bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                Agregar
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  )
}
