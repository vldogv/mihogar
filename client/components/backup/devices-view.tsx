"use client"

import { useState } from "react"
import { AppShell } from "@/components/app-shell"
import { DeviceCard } from "@/components/device-card"
import { WifiSetupModal } from "@/components/wifi-setup-modal"
import { AddDeviceWizard } from "@/components/add-device-wizard"
import { Cpu, Lightbulb, Radio, Sun, Camera, Plus, Wifi, RefreshCw, CheckCircle, AlertTriangle } from "lucide-react"
import { cn } from "@/lib/utils"

interface Device {
  id: string
  name: string
  type: "esp32" | "shelly" | "pir" | "lux" | "camera"
  zone: string
  status: "online" | "offline" | "updating"
  ip?: string
  firmware?: string
}

const initialDevices: Device[] = [
  {
    id: "esp32-main",
    name: "ESP32-C5 Principal",
    type: "esp32",
    zone: "General",
    status: "online",
    ip: "192.168.1.100",
    firmware: "1.2.0",
  },
  {
    id: "shelly-sala",
    name: "Shelly 1 Gen4",
    type: "shelly",
    zone: "Sala",
    status: "online",
    ip: "192.168.1.101",
    firmware: "1.4.2",
  },
  {
    id: "shelly-cocina",
    name: "Shelly 1 Gen4",
    type: "shelly",
    zone: "Cocina",
    status: "online",
    ip: "192.168.1.102",
    firmware: "1.4.2",
  },
  {
    id: "shelly-recamara1",
    name: "Shelly 1 Gen4",
    type: "shelly",
    zone: "Recámara Principal",
    status: "online",
    ip: "192.168.1.103",
    firmware: "1.4.2",
  },
  {
    id: "shelly-recamara2",
    name: "Shelly 1 Gen4",
    type: "shelly",
    zone: "Recámara 2",
    status: "offline",
    ip: "192.168.1.104",
    firmware: "1.4.1",
  },
  {
    id: "shelly-pasillo",
    name: "Shelly 1 Gen4",
    type: "shelly",
    zone: "Pasillo",
    status: "online",
    ip: "192.168.1.105",
    firmware: "1.4.2",
  },
  {
    id: "shelly-bano",
    name: "Shelly 1 Gen4",
    type: "shelly",
    zone: "Baño",
    status: "online",
    ip: "192.168.1.106",
    firmware: "1.4.2",
  },
  { id: "pir-sala", name: "Sensor PIR 360°", type: "pir", zone: "Sala", status: "online" },
  { id: "pir-cocina", name: "Sensor PIR 360°", type: "pir", zone: "Cocina", status: "online" },
  { id: "pir-pasillo", name: "Sensor PIR 360°", type: "pir", zone: "Pasillo", status: "online" },
  { id: "lux-sala", name: "Sensor Crepuscular", type: "lux", zone: "Sala", status: "online" },
  { id: "lux-cocina", name: "Sensor Crepuscular", type: "lux", zone: "Cocina", status: "online" },
  { id: "camera-pasillo", name: "Cámara IP Nocturna", type: "camera", zone: "Pasillo", status: "online" },
]

const deviceIcons = {
  esp32: Cpu,
  shelly: Lightbulb,
  pir: Radio,
  lux: Sun,
  camera: Camera,
}

const deviceTypeLabels = {
  esp32: "Controlador",
  shelly: "Módulo Relé",
  pir: "Sensor Movimiento",
  lux: "Sensor Luz",
  camera: "Cámara",
}

export function DevicesView() {
  const [devices] = useState(initialDevices)
  const [showWifiSetup, setShowWifiSetup] = useState(false)
  const [showAddDevice, setShowAddDevice] = useState(false)
  const [activeTab, setActiveTab] = useState<"all" | "shelly" | "sensors" | "camera">("all")

  const filteredDevices = devices.filter((device) => {
    if (activeTab === "all") return true
    if (activeTab === "shelly") return device.type === "shelly" || device.type === "esp32"
    if (activeTab === "sensors") return device.type === "pir" || device.type === "lux"
    if (activeTab === "camera") return device.type === "camera"
    return true
  })

  const onlineCount = devices.filter((d) => d.status === "online").length
  const offlineCount = devices.filter((d) => d.status === "offline").length

  return (
    <AppShell
      title="Dispositivos"
      subtitle="Configura y administra los dispositivos del sistema"
      currentPath="/devices"
    >
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
          <button
            onClick={() => setShowWifiSetup(true)}
            className="flex items-center gap-1.5 lg:gap-2 px-3 lg:px-4 py-2 lg:py-2.5 rounded-xl bg-secondary text-secondary-foreground font-medium text-xs lg:text-sm hover:bg-secondary/80 transition-colors"
          >
            <Wifi className="h-3.5 w-3.5 lg:h-4 lg:w-4" />
            WiFi
          </button>
          <button
            onClick={() => setShowAddDevice(true)}
            className="flex items-center gap-1.5 lg:gap-2 px-3 lg:px-4 py-2 lg:py-2.5 rounded-xl bg-primary text-primary-foreground font-medium text-xs lg:text-sm hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-3.5 w-3.5 lg:h-4 lg:w-4" />
            Agregar
          </button>
          <button className="flex items-center gap-1.5 lg:gap-2 px-3 lg:px-4 py-2 lg:py-2.5 rounded-xl bg-secondary text-secondary-foreground font-medium text-xs lg:text-sm hover:bg-secondary/80 transition-colors">
            <RefreshCw className="h-3.5 w-3.5 lg:h-4 lg:w-4" />
            Escanear
          </button>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-2 overflow-x-auto pb-1 -mx-4 px-4 lg:mx-0 lg:px-0 lg:flex-wrap scrollbar-none">
          {[
            { id: "all" as const, label: "Todos" },
            { id: "shelly" as const, label: "Relés" },
            { id: "sensors" as const, label: "Sensores" },
            { id: "camera" as const, label: "Cámara" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "px-3 lg:px-4 py-1.5 lg:py-2 rounded-xl text-xs lg:text-sm font-medium whitespace-nowrap transition-colors",
                activeTab === tab.id
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80",
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Devices grid */}
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 lg:gap-4">
          {filteredDevices.map((device) => {
            const Icon = deviceIcons[device.type]
            return <DeviceCard key={device.id} device={device} icon={Icon} typeLabel={deviceTypeLabels[device.type]} />
          })}
        </div>

        {/* ESP32 info card */}
        <div className="rounded-2xl border border-border bg-background p-4 lg:p-6">
          <div className="flex flex-col sm:flex-row items-start gap-3 lg:gap-4">
            <div className="flex h-10 w-10 lg:h-12 lg:w-12 items-center justify-center rounded-xl bg-primary/10 flex-shrink-0">
              <Cpu className="h-5 w-5 lg:h-6 lg:w-6 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-foreground text-sm lg:text-base">Controlador ESP32-C5</h3>
              <p className="text-xs lg:text-sm text-muted-foreground mt-1">
                Este dispositivo coordina todos los sensores y módulos Shelly de tu hogar. Opera como servidor local
                incluso sin conexión a internet.
              </p>
              <div className="grid grid-cols-2 gap-2 lg:grid-cols-4 lg:gap-4 mt-3 lg:mt-4">
                <div className="p-3 rounded-xl bg-secondary/50">
                  <p className="text-xs text-muted-foreground">IP Local</p>
                  <p className="text-sm font-medium text-foreground">192.168.1.100</p>
                </div>
                <div className="p-3 rounded-xl bg-secondary/50">
                  <p className="text-xs text-muted-foreground">Firmware</p>
                  <p className="text-sm font-medium text-foreground">v1.2.0</p>
                </div>
                <div className="p-3 rounded-xl bg-secondary/50">
                  <p className="text-xs text-muted-foreground">Zona horaria</p>
                  <p className="text-sm font-medium text-foreground">America/Mexico_City</p>
                </div>
                <div className="p-3 rounded-xl bg-secondary/50">
                  <p className="text-xs text-muted-foreground">Última sync</p>
                  <p className="text-sm font-medium text-foreground">Hace 5 min</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {showWifiSetup && <WifiSetupModal onClose={() => setShowWifiSetup(false)} />}
      {showAddDevice && <AddDeviceWizard onClose={() => setShowAddDevice(false)} />}
    </AppShell>
  )
}
