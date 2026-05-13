"use client"

import { useState } from "react"
import { X, Search, Lightbulb, Radio, Sun, Camera, ChevronRight, CheckCircle, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface AddDeviceWizardProps {
  onClose: () => void
}

interface DiscoveredDevice {
  id: string
  name: string
  type: "shelly" | "pir" | "lux" | "camera"
  ip: string
}

const deviceTypes = [
  { id: "shelly", name: "Módulo Shelly", icon: Lightbulb, description: "Relé para control de luces" },
  { id: "pir", name: "Sensor PIR", icon: Radio, description: "Sensor de movimiento" },
  { id: "lux", name: "Sensor Crepuscular", icon: Sun, description: "Sensor de luz ambiental" },
  { id: "camera", name: "Cámara IP", icon: Camera, description: "Cámara para modo nocturno" },
]

const zones = [
  { id: "sala", name: "Sala" },
  { id: "recamara-principal", name: "Recámara Principal" },
  { id: "recamara-2", name: "Recámara 2" },
  { id: "cocina", name: "Cocina" },
  { id: "pasillo", name: "Pasillo" },
  { id: "bano", name: "Baño" },
]

export function AddDeviceWizard({ onClose }: AddDeviceWizardProps) {
  const [step, setStep] = useState<"select" | "scan" | "configure" | "done">("select")
  const [selectedType, setSelectedType] = useState<string | null>(null)
  const [isScanning, setIsScanning] = useState(false)
  const [discoveredDevices, setDiscoveredDevices] = useState<DiscoveredDevice[]>([])
  const [selectedDevice, setSelectedDevice] = useState<DiscoveredDevice | null>(null)
  const [selectedZone, setSelectedZone] = useState("")
  const [isSaving, setIsSaving] = useState(false)

  const handleScan = async () => {
    setIsScanning(true)
    // Simulate scanning
    await new Promise((resolve) => setTimeout(resolve, 2000))
    setDiscoveredDevices([
      { id: "new-1", name: "Shelly 1 Gen4", type: "shelly", ip: "192.168.1.120" },
      { id: "new-2", name: "Sensor PIR WiFi", type: "pir", ip: "192.168.1.121" },
    ])
    setIsScanning(false)
    setStep("scan")
  }

  const handleConfigure = (device: DiscoveredDevice) => {
    setSelectedDevice(device)
    setStep("configure")
  }

  const handleSave = async () => {
    setIsSaving(true)
    await new Promise((resolve) => setTimeout(resolve, 1500))
    setIsSaving(false)
    setStep("done")
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4">
      <div className="absolute inset-0 bg-foreground/20 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-background rounded-t-2xl sm:rounded-2xl shadow-xl w-full sm:max-w-lg p-5 sm:p-6 max-h-[90vh] overflow-y-auto safe-area-bottom">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-lg hover:bg-secondary transition-colors"
        >
          <X className="h-5 w-5 text-muted-foreground" />
        </button>

        {step === "select" && (
          <>
            <h3 className="text-lg font-semibold text-foreground mb-2">Agregar dispositivo</h3>
            <p className="text-sm text-muted-foreground mb-6">Selecciona el tipo de dispositivo que deseas agregar</p>

            <div className="space-y-3">
              {deviceTypes.map((type) => (
                <button
                  key={type.id}
                  onClick={() => {
                    setSelectedType(type.id)
                    handleScan()
                  }}
                  className="w-full flex items-center gap-4 p-4 rounded-xl border border-border hover:border-primary hover:bg-secondary/50 transition-colors text-left"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                    <type.icon className="h-6 w-6 text-primary" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-foreground">{type.name}</p>
                    <p className="text-sm text-muted-foreground">{type.description}</p>
                  </div>
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                </button>
              ))}
            </div>
          </>
        )}

        {step === "scan" && (
          <>
            <h3 className="text-lg font-semibold text-foreground mb-2">Dispositivos encontrados</h3>
            <p className="text-sm text-muted-foreground mb-6">Selecciona el dispositivo que deseas agregar</p>

            {isScanning ? (
              <div className="text-center py-12">
                <Loader2 className="h-10 w-10 mx-auto text-primary animate-spin mb-4" />
                <p className="text-muted-foreground">Buscando dispositivos en la red...</p>
              </div>
            ) : discoveredDevices.length > 0 ? (
              <div className="space-y-3">
                {discoveredDevices.map((device) => (
                  <button
                    key={device.id}
                    onClick={() => handleConfigure(device)}
                    className="w-full flex items-center gap-4 p-4 rounded-xl border border-border hover:border-primary hover:bg-secondary/50 transition-colors text-left"
                  >
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50">
                      <Search className="h-5 w-5 text-emerald-600" />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-foreground">{device.name}</p>
                      <p className="text-sm text-muted-foreground font-mono">{device.ip}</p>
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground" />
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-muted-foreground">No se encontraron dispositivos nuevos</p>
              </div>
            )}

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setStep("select")}
                className="flex-1 px-5 py-3 rounded-xl bg-secondary text-secondary-foreground font-medium text-sm hover:bg-secondary/80 transition-colors"
              >
                Atrás
              </button>
              <button
                onClick={handleScan}
                disabled={isScanning}
                className="flex-1 flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                <Search className="h-4 w-4" />
                Escanear de nuevo
              </button>
            </div>
          </>
        )}

        {step === "configure" && selectedDevice && (
          <>
            <h3 className="text-lg font-semibold text-foreground mb-2">Configurar dispositivo</h3>
            <p className="text-sm text-muted-foreground mb-6">Asigna el dispositivo a una zona</p>

            <div className="p-4 rounded-xl bg-secondary/50 mb-6">
              <p className="font-medium text-foreground">{selectedDevice.name}</p>
              <p className="text-sm text-muted-foreground font-mono">{selectedDevice.ip}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-3">Zona</label>
              <div className="grid grid-cols-2 gap-3">
                {zones.map((zone) => (
                  <button
                    key={zone.id}
                    onClick={() => setSelectedZone(zone.id)}
                    className={cn(
                      "px-4 py-3 rounded-xl text-sm font-medium transition-colors",
                      selectedZone === zone.id
                        ? "bg-primary text-primary-foreground"
                        : "bg-secondary text-secondary-foreground hover:bg-secondary/80",
                    )}
                  >
                    {zone.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setStep("scan")}
                className="flex-1 px-5 py-3 rounded-xl bg-secondary text-secondary-foreground font-medium text-sm hover:bg-secondary/80 transition-colors"
              >
                Atrás
              </button>
              <button
                onClick={handleSave}
                disabled={!selectedZone || isSaving}
                className="flex-1 flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Guardando...
                  </>
                ) : (
                  "Guardar"
                )}
              </button>
            </div>
          </>
        )}

        {step === "done" && (
          <div className="text-center py-8">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 mx-auto mb-4">
              <CheckCircle className="h-8 w-8 text-emerald-600" />
            </div>
            <h3 className="text-xl font-semibold text-foreground">Dispositivo agregado</h3>
            <p className="text-muted-foreground mt-2">
              El dispositivo se configuró correctamente y ya está listo para usarse.
            </p>
            <button
              onClick={onClose}
              className="mt-6 px-6 py-3 rounded-xl bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors"
            >
              Finalizar
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
