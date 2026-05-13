"use client"

import { useState, useEffect, useCallback } from "react"
import { AppShell } from "@/components/app-shell"
import { DeviceCard } from "@/components/device-card"
import { WifiSetupModal } from "@/components/wifi-setup-modal"
import { AddDeviceWizard } from "@/components/add-device-wizard"
import { Cpu, Lightbulb, Radio, Sun, Camera, Plus, Wifi, RefreshCw, CheckCircle, AlertTriangle } from "lucide-react"
import { useAuth } from "@/lib/auth/auth-context"
import { dispositivosService, type Dispositivo } from "@/lib/services/dispositivos"
import { cn } from "@/lib/utils"
import { usePermissions } from "@/lib/hooks/use-permissions"

const deviceIcons: Record<string, any> = {
  modulo_shelly: Lightbulb,
  sensor_pir: Radio,
  sensor_crepuscular: Sun,
  camara_ip: Camera,
}

const deviceTypeLabels: Record<string, string> = {
  modulo_shelly: "Módulo Relé",
  sensor_pir: "Sensor Movimiento",
  sensor_crepuscular: "Sensor Luz",
  camara_ip: "Cámara",
}

export function DevicesView() {
  const { session } = useAuth()
  const casaId = session?.casa_id_activa
  const [devices, setDevices] = useState<Dispositivo[]>([])
  const [loading, setLoading] = useState(true)
  const [showWifiSetup, setShowWifiSetup] = useState(false)
  const [showAddDevice, setShowAddDevice] = useState(false)
  const [activeTab, setActiveTab] = useState<"all" | "shelly" | "sensors" | "camera">("all")
  const perms = usePermissions()

  const fetchDevices = useCallback(async () => {
    if (!casaId) return
    try {
      const data = await dispositivosService.getDispositivos(casaId)
      setDevices(data)
    } catch (err) {
      console.error("Error loading devices:", err)
    } finally {
      setLoading(false)
    }
  }, [casaId])

  useEffect(() => { fetchDevices() }, [fetchDevices])

  const filteredDevices = devices.filter((d) => {
    if (activeTab === "all") return true
    if (activeTab === "shelly") return d.tipo === "modulo_shelly"
    if (activeTab === "sensors") return d.tipo === "sensor_pir" || d.tipo === "sensor_crepuscular"
    if (activeTab === "camera") return d.tipo === "camara_ip"
    return true
  })

  const onlineCount = devices.filter((d) => d.estado === "online").length
  const offlineCount = devices.filter((d) => d.estado === "offline").length

  // Map to the format DeviceCard expects
  const mappedDevices = filteredDevices.map((d) => ({
    id: d.id,
    name: d.nombre,
    type: d.tipo as any,
    zone: d.zona_nombre || "",
    status: d.estado as "online" | "offline" | "updating",
    ip: d.ip_local || undefined,
    firmware: d.firmware_version || undefined,
  }))

  if (loading) {
    return (
      <AppShell title="Dispositivos" subtitle="Configura y administra los dispositivos del sistema" currentPath="/devices">
        <div className="flex items-center justify-center py-20">
          <div className="animate-pulse text-muted-foreground">Cargando dispositivos...</div>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell title="Dispositivos" subtitle="Configura y administra los dispositivos del sistema" currentPath="/devices">
      <div className="space-y-6">
        {/* Status summary */}
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-50">
            <CheckCircle className="h-4 w-4 text-emerald-600" />
            <span className="text-sm font-medium text-emerald-700">{onlineCount} en línea</span>
          </div>
          {offlineCount > 0 && (
            <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-50">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <span className="text-sm font-medium text-red-700">{offlineCount} sin conexión</span>
            </div>
          )}
        </div>

        {/* Quick actions */}
        <div className="flex flex-wrap gap-2 lg:gap-3">
          <button onClick={() => setShowWifiSetup(true)}
            className="flex items-center gap-1.5 lg:gap-2 px-3 lg:px-4 py-2 lg:py-2.5 rounded-xl bg-secondary text-secondary-foreground font-medium text-xs lg:text-sm hover:bg-secondary/80 transition-colors">
            <Wifi className="h-3.5 w-3.5 lg:h-4 lg:w-4" /> WiFi
          </button>
          {perms.canAddDevice && (
            <button
              onClick={() => setShowAddDevice(true)}
              className="flex items-center gap-1.5 lg:gap-2 px-3 lg:px-4 py-2 lg:py-2.5 rounded-xl bg-primary text-primary-foreground font-medium text-xs lg:text-sm hover:bg-primary/90 transition-colors"
            >
              <Plus className="h-3.5 w-3.5 lg:h-4 lg:w-4" />
              Agregar
            </button>
          )}
          <button onClick={fetchDevices}
            className="flex items-center gap-1.5 lg:gap-2 px-3 lg:px-4 py-2 lg:py-2.5 rounded-xl bg-secondary text-secondary-foreground font-medium text-xs lg:text-sm hover:bg-secondary/80 transition-colors">
            <RefreshCw className="h-3.5 w-3.5 lg:h-4 lg:w-4" /> Escanear
          </button>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
          {[
            { id: "all" as const, label: "Todos" },
            { id: "shelly" as const, label: "Relés" },
            { id: "sensors" as const, label: "Sensores" },
            { id: "camera" as const, label: "Cámara" },
          ].map((tab) => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={cn("px-3 lg:px-4 py-1.5 lg:py-2 rounded-xl text-xs lg:text-sm font-medium whitespace-nowrap transition-colors",
                activeTab === tab.id ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground hover:bg-secondary/80")}>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Devices grid */}
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 lg:gap-4">
          {mappedDevices.map((device) => {
            const Icon = deviceIcons[filteredDevices.find(d => d.id === device.id)?.tipo || ""] || Cpu
            const typeLabel = deviceTypeLabels[filteredDevices.find(d => d.id === device.id)?.tipo || ""] || "Dispositivo"
            return <DeviceCard key={device.id} device={device} icon={Icon} typeLabel={typeLabel} />
          })}
        </div>

        {mappedDevices.length === 0 && (
          <div className="text-center py-12">
            <Cpu className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No hay dispositivos en esta categoría</p>
          </div>
        )}
      </div>

      {showWifiSetup && <WifiSetupModal onClose={() => setShowWifiSetup(false)} />}
      {showAddDevice && <AddDeviceWizard onClose={() => setShowAddDevice(false)} />}
    </AppShell>
  )
}
