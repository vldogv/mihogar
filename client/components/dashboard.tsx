"use client"

import { Home, Lightbulb, Calendar, BarChart3, Settings, Users, Wifi, WifiOff, Sun, Moon } from "lucide-react"
import { ZoneCard } from "@/components/zone-card"
import { QuickActions } from "@/components/quick-actions"
import { ConnectionStatus } from "@/components/connection-status"
import { MobileNav } from "@/components/mobile-nav"
import { OfflineBanner } from "@/components/offline-banner"
import { useAuth } from "@/lib/auth/auth-context"
import { useConnectivity } from "@/hooks/use-connectivity"
import { useSnapshot } from "@/lib/offline/snapshot-context"
import { panelService } from "@/lib/services/panel"
import { cn } from "@/lib/utils"


export function Dashboard() {
  const { session, activeCasa, isLoading: authLoading } = useAuth()
  const { snapshot, isHydrating, refresh } = useSnapshot()
  const { isOnline } = useConnectivity()

  const casaId = session?.casa_id_activa

  const handleToggleZone = async (zonaId: string, currentState: boolean) => {
    if (!isOnline) return
    try {
      await panelService.toggleZona(zonaId, !currentState)
      await refresh()
    } catch (err) {
      console.error("Error toggling zone:", err)
    }
  }

  const handleModeChange = async (zonaId: string, mode: "auto" | "manual" | "timer") => {
    if (!isOnline) return
    const modeMap: Record<string, string> = { auto: "automatico", manual: "manual", timer: "temporizador" }
    try {
      await panelService.cambiarModo(zonaId, modeMap[mode])
      await refresh()
    } catch (err) {
      console.error("Error changing mode:", err)
    }
  }

  const handleAllOn = async () => {
    if (!casaId) return
    if (!isOnline) return
    try {
      await panelService.encenderTodo(casaId)
      await refresh()
    } catch (err) { console.error(err) }
  }

  const handleAllOff = async () => {
    if (!casaId) return
    if (!isOnline) return
    try {
      await panelService.apagarTodo(casaId)
      await refresh()
    } catch (err) { console.error(err) }
  }

  if (authLoading || (isHydrating && !snapshot)) {
    return (
      <div className="min-h-screen bg-secondary/30 flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Cargando panel...</div>
      </div>
    )
  }

 const allZones = (snapshot?.zonas || []).map((z) => {
    const modeMap: Record<string, "auto" | "manual" | "timer"> = {
      automatico: "auto", manual: "manual", temporizador: "timer",
    }
    return {
      id: z.zona.id,
      name: z.zona.nombre,
      icon: "lightbulb",
      isOn: z.config?.encendida || false,
      mode: modeMap[z.config?.modo || "automatico"] || "auto" as const,
      movement: z.config?.movimiento_detectado || false,
      lux: z.config?.luz_ambiente_actual ?? 0,
    }
  })

  const zonasPermitidas = session?.zonas_permitidas
  const zones = (session?.rol === "usuario" && zonasPermitidas?.length)
    ? allZones.filter(z => zonasPermitidas.includes(z.id))
    : allZones

  const activeZones = zones.filter((z) => z.isOn).length

  return (
    <div className="flex min-h-screen bg-secondary/30">
      {/* Sidebar - desktop only */}
      <aside className="hidden lg:block w-72 bg-background shadow-none">
        <div className="flex h-full flex-col">
          <div className="flex items-center gap-3 px-6 py-5 border-b border-border">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary">
              <Home className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="font-semibold text-foreground">{activeCasa?.nombre || "Mi Hogar"}</h1>
              <p className="text-xs text-muted-foreground">Sistema Domótica</p>
            </div>
          </div>
          <nav className="flex-1 px-4 py-6 space-y-1">
            {[
              { name: "Inicio", href: "/", icon: Home, current: true },
              { name: "Zonas", href: "/zones", icon: Lightbulb, current: false },
              { name: "Horarios", href: "/schedules", icon: Calendar, current: false },
              { name: "Consumo", href: "/reports", icon: BarChart3, current: false },
              { name: "Dispositivos", href: "/devices", icon: Settings, current: false },
              { name: "Usuarios", href: "/users", icon: Users, current: false },
            ].map((item) => (
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
        <header className="sticky top-0 z-30 bg-background/80 backdrop-blur-lg border-b border-border">
          <OfflineBanner />
          <div className="flex items-center justify-between px-4 py-3 lg:px-8 lg:py-4">
            <div>
              <h2 className="text-lg lg:text-xl font-semibold text-foreground">Panel de Control</h2>
              <p className="text-xs lg:text-sm text-muted-foreground">
                {activeZones} de {zones.length} zonas activas
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium",
                  isOnline ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700",
                )}
              >
                {isOnline ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
                <span className="hidden sm:inline">{isOnline ? "En línea" : "Sin conexión"}</span>
              </div>
            </div>
          </div>
        </header>

        <div className="px-3 sm:px-4 py-3 sm:py-4 pb-20 lg:px-8 lg:py-8 lg:pb-8 space-y-4 sm:space-y-6">
          <QuickActions onAllOn={handleAllOn} onAllOff={handleAllOff} onAutoAll={handleAllOn} isOnline={isOnline} />

          <section>
            <h3 className="text-sm sm:text-base lg:text-lg font-semibold text-foreground mb-3 sm:mb-4">Zonas del Hogar</h3>
            <div className="grid gap-2.5 sm:gap-3 lg:gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
              {zones.map((zone) => (
                <ZoneCard
                  key={zone.id}
                  zone={zone}
                  onToggle={() => handleToggleZone(zone.id, zone.isOn)}
                  onModeChange={(mode) => handleModeChange(zone.id, mode)}
                  isOnline={isOnline}
                />
              ))}
            </div>
          </section>
        </div>
      </main>

      <MobileNav currentPath="/" />
    </div>
  )
}
