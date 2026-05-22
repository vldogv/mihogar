"use client"

import { useState } from "react"
import { Home, Lightbulb, Calendar, BarChart3, Settings, Users, Menu, X, Wifi, WifiOff, Sun, Moon } from "lucide-react"
import { ZoneCard } from "@/components/zone-card"
import { QuickActions } from "@/components/quick-actions"
import { ConnectionStatus } from "@/components/connection-status"
import { MobileNav } from "@/components/mobile-nav"
import { cn } from "@/lib/utils"

const zones = [
  { id: "sala", name: "Sala", icon: "sofa", isOn: true, mode: "auto" as const, movement: true, lux: 35 },
  {
    id: "recamara-principal",
    name: "Recámara Principal",
    icon: "bed",
    isOn: false,
    mode: "manual" as const,
    movement: false,
    lux: 80,
  },
  { id: "recamara-2", name: "Recámara 2", icon: "bed", isOn: false, mode: "auto" as const, movement: false, lux: 75 },
  { id: "cocina", name: "Cocina", icon: "utensils", isOn: true, mode: "timer" as const, movement: true, lux: 20 },
  {
    id: "pasillo",
    name: "Pasillo",
    icon: "move-horizontal",
    isOn: false,
    mode: "auto" as const,
    movement: false,
    lux: 45,
  },
  { id: "bano", name: "Baño", icon: "bath", isOn: false, mode: "auto" as const, movement: false, lux: 60 },
]

const navigation = [
  { name: "Inicio", href: "/", icon: Home, current: true },
  { name: "Zonas", href: "/zones", icon: Lightbulb, current: false },
  { name: "Horarios", href: "/schedules", icon: Calendar, current: false },
  { name: "Consumo", href: "/reports", icon: BarChart3, current: false },
  { name: "Dispositivos", href: "/devices", icon: Settings, current: false },
  { name: "Usuarios", href: "/users", icon: Users, current: false },
]

export function Dashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [isOnline, setIsOnline] = useState(true)
  const [nightMode, setNightMode] = useState(false)
  const [zonesState, setZonesState] = useState(zones)

  const handleToggleZone = (zoneId: string) => {
    setZonesState((prev) => prev.map((zone) => (zone.id === zoneId ? { ...zone, isOn: !zone.isOn } : zone)))
  }

  const handleModeChange = (zoneId: string, mode: "auto" | "manual" | "timer") => {
    setZonesState((prev) => prev.map((zone) => (zone.id === zoneId ? { ...zone, mode } : zone)))
  }

  const activeZones = zonesState.filter((z) => z.isOn).length

  return (
    <div className="flex min-h-screen bg-secondary/30">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-foreground/20 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar - desktop only */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-72 bg-background shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:shadow-none",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-full flex-col">
          <div className="flex items-center justify-between px-6 py-5 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary">
                <Home className="h-5 w-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="font-semibold text-foreground">Mi Hogar</h1>
                <p className="text-xs text-muted-foreground">Sistema Domótica</p>
              </div>
            </div>
            <button onClick={() => setSidebarOpen(false)} className="lg:hidden p-2 rounded-lg hover:bg-secondary">
              <X className="h-5 w-5 text-muted-foreground" />
            </button>
          </div>

          <nav className="flex-1 px-4 py-6 space-y-1">
            {navigation.map((item) => (
              <a
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors",
                  item.current
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                )}
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </a>
            ))}
          </nav>

          <div className="px-4 pb-6">
            <ConnectionStatus />
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 lg:pl-0">
        {/* Header */}
        <header className="sticky top-0 z-30 bg-background/80 backdrop-blur-lg border-b border-border">
          <div className="flex items-center justify-between px-4 py-3 lg:px-8 lg:py-4">
            <div className="flex items-center gap-3 lg:gap-4">
              <button onClick={() => setSidebarOpen(true)} className="hidden lg:hidden p-2 rounded-lg hover:bg-secondary">
                <Menu className="h-5 w-5 text-foreground" />
              </button>
              <div>
                <h2 className="text-lg lg:text-xl font-semibold text-foreground">Panel de Control</h2>
                <p className="text-xs lg:text-sm text-muted-foreground">
                  {activeZones} de {zonesState.length} zonas activas
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 lg:gap-3">
              <button
                onClick={() => setNightMode(!nightMode)}
                className={cn(
                  "flex items-center gap-1.5 lg:gap-2 px-3 lg:px-4 py-1.5 lg:py-2 rounded-xl text-xs lg:text-sm font-medium transition-colors",
                  nightMode
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-secondary-foreground hover:bg-secondary/80",
                )}
              >
                {nightMode ? <Moon className="h-3.5 w-3.5 lg:h-4 lg:w-4" /> : <Sun className="h-3.5 w-3.5 lg:h-4 lg:w-4" />}
                <span className="hidden sm:inline">{nightMode ? "Modo Noche" : "Modo Día"}</span>
              </button>

              <button
                onClick={() => setIsOnline(!isOnline)}
                className={cn(
                  "flex items-center gap-1.5 lg:gap-2 px-3 lg:px-4 py-1.5 lg:py-2 rounded-xl text-xs lg:text-sm font-medium transition-colors",
                  isOnline ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700",
                )}
              >
                {isOnline ? <Wifi className="h-3.5 w-3.5 lg:h-4 lg:w-4" /> : <WifiOff className="h-3.5 w-3.5 lg:h-4 lg:w-4" />}
                <span className="hidden sm:inline">{isOnline ? "En línea" : "Sin conexión"}</span>
              </button>
            </div>
          </div>
        </header>

        {/* Content - bottom padding for mobile nav */}
        <div className="px-3 sm:px-4 py-3 sm:py-4 pb-20 lg:px-8 lg:py-8 lg:pb-8 space-y-4 sm:space-y-6 lg:space-y-8">
          {/* Quick Actions */}
          <QuickActions
            onAllOn={() => setZonesState((prev) => prev.map((z) => ({ ...z, isOn: true })))}
            onAllOff={() => setZonesState((prev) => prev.map((z) => ({ ...z, isOn: false })))}
            onAutoAll={() => setZonesState((prev) => prev.map((z) => ({ ...z, mode: "auto" as const })))}
            isOnline={true}
          />

          {/* Zones Grid */}
          <section>
            <h3 className="text-sm sm:text-base lg:text-lg font-semibold text-foreground mb-3 sm:mb-4">Zonas del Hogar</h3>
            <div className="grid gap-2.5 sm:gap-3 lg:gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
              {zonesState.map((zone) => (
                <ZoneCard
                  key={zone.id}
                  zone={zone}
                  onToggle={() => handleToggleZone(zone.id)}
                  onModeChange={(mode) => handleModeChange(zone.id, mode)}
                  isOnline={true}
                />
              ))}
            </div>
          </section>
        </div>
      </main>

      {/* Mobile bottom navigation */}
      <MobileNav currentPath="/" />
    </div>
  )
}
