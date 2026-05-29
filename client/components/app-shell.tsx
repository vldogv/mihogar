"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Home, Lightbulb, Calendar, BarChart3, Settings, Users, Menu, X, Wifi, WifiOff, Radio, LogOut, RefreshCw } from "lucide-react"
import { ConnectionStatus } from "@/components/connection-status"
import { MobileNav } from "@/components/mobile-nav"
import { OfflineBanner } from "@/components/offline-banner"
import { useAuth } from "@/lib/auth/auth-context"
import { useMode } from "@/lib/local-hub/mode-context"
import { cn } from "@/lib/utils"
import { usePermissions } from "@/lib/hooks/use-permissions"

interface AppShellProps {
  children: React.ReactNode
  title: string
  subtitle?: string
  currentPath: string
}

export function AppShell({ children, title, subtitle, currentPath }: AppShellProps) {
  const { session, user, activeCasa, isLoading, logout, changeHouse } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { mode } = useMode()
  const perms = usePermissions()

  const navigation = [
    { name: "Inicio", href: "/", icon: Home },
    { name: "Zonas", href: "/zones", icon: Lightbulb },
    { name: "Horarios", href: "/schedules", icon: Calendar },
    { name: "Consumo", href: "/reports", icon: BarChart3 },
    { name: "Dispositivos", href: "/devices", icon: Settings },
    ...(perms.canSeeUsuarios ? [{ name: "Usuarios", href: "/users", icon: Users }] : []),
  ]

  useEffect(() => {
    if (!isLoading && !session) {
      window.location.href = "/login"
    }
  }, [session, isLoading])

  if (isLoading || !session) {
    return (
      <div className="min-h-screen bg-secondary/30 flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Cargando...</div>
      </div>
    )
  }

  const hasMultipleHouses = user && user.casas.length > 1

  return (
    <div className="flex min-h-screen bg-secondary/30">
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 bg-foreground/20 backdrop-blur-sm lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}
      <aside className={cn("fixed inset-y-0 left-0 z-50 w-72 bg-background shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:shadow-none", sidebarOpen ? "translate-x-0" : "-translate-x-full")}>
        <div className="flex h-full flex-col">
          <div className="flex items-center justify-between px-6 py-5 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary">
                <Home className="h-5 w-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="font-semibold text-foreground truncate max-w-[140px]">{activeCasa?.nombre || "Mi Hogar"}</h1>
                <p className="text-xs text-muted-foreground capitalize">{session.rol}</p>
              </div>
            </div>
            <button onClick={() => setSidebarOpen(false)} className="lg:hidden p-2 rounded-lg hover:bg-secondary">
              <X className="h-5 w-5 text-muted-foreground" />
            </button>
          </div>
          <nav className="flex-1 px-4 py-6 space-y-1">
            {navigation.map((item) => (
              <a key={item.name} href={item.href} className={cn("flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors", item.href === currentPath ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-secondary hover:text-foreground")}>
                <item.icon className="h-5 w-5" />
                {item.name}
              </a>
            ))}
          </nav>
          <div className="px-4 pb-6 space-y-3">
            <ConnectionStatus />
            {hasMultipleHouses && (
              <button onClick={changeHouse} className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors">
                <RefreshCw className="h-4 w-4" />
                Cambiar casa
              </button>
            )}
            <button onClick={logout} className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium text-muted-foreground hover:bg-red-50 hover:text-red-600 transition-colors">
              <LogOut className="h-4 w-4" />
              Cerrar sesión
            </button>
          </div>
        </div>
      </aside>
      <main className="flex-1 min-w-0 overflow-x-hidden lg:pl-0">
        <header className="sticky top-0 z-30 bg-background/80 backdrop-blur-lg border-b border-border">
          <OfflineBanner />
          <div className="flex items-center justify-between px-4 py-3 lg:px-8 lg:py-4">
            <div className="flex items-center gap-3 lg:gap-4">
              <button onClick={() => setSidebarOpen(true)} className="hidden lg:hidden p-2 rounded-lg hover:bg-secondary">
                <Menu className="h-5 w-5 text-foreground" />
              </button>
              <div>
                <h2 className="text-lg lg:text-xl font-semibold text-foreground">{title}</h2>
                {subtitle && <p className="text-xs lg:text-sm text-muted-foreground">{subtitle}</p>}
              </div>
            </div>
            <div className="flex items-center gap-2 lg:gap-3">
              <div className={cn(
                "flex items-center gap-1.5 lg:gap-2 px-3 lg:px-4 py-1.5 lg:py-2 rounded-xl text-xs lg:text-sm font-medium",
                mode === "cloud" && "bg-emerald-50 text-emerald-700",
                mode === "local-hub" && "bg-sky-50 text-sky-700",
                mode === "offline" && "bg-amber-50 text-amber-700",
              )}>
                {mode === "cloud" && <Wifi className="h-3.5 w-3.5 lg:h-4 lg:w-4" />}
                {mode === "local-hub" && <Radio className="h-3.5 w-3.5 lg:h-4 lg:w-4" />}
                {mode === "offline" && <WifiOff className="h-3.5 w-3.5 lg:h-4 lg:w-4" />}
                <span className="hidden sm:inline">
                  {mode === "cloud" ? "En línea" : mode === "local-hub" ? "Hub local" : "Sin conexión"}
                </span>
              </div>
            </div>
          </div>
        </header>
        <div className="px-4 py-4 pb-20 lg:px-8 lg:py-8 lg:pb-8 overflow-x-hidden">{children}</div>
      </main>
      <MobileNav currentPath={currentPath} />
    </div>
  )
}