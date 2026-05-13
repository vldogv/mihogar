"use client"

import { useState } from "react"
import { Home, Lightbulb, Calendar, BarChart3, Settings, Users, LogOut, ArrowLeftRight, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuth } from "@/lib/auth/auth-context"
import { usePermissions } from "@/lib/hooks/use-permissions"



interface MobileNavProps {
  currentPath: string
}

export function MobileNav({ currentPath }: MobileNavProps) {
  const { user, activeCasa, logout, changeHouse ,session} = useAuth()
  const [showMenu, setShowMenu] = useState(false)
  const perms = usePermissions()

  const navItems = [
    { name: "Inicio", href: "/", icon: Home },
    { name: "Zonas", href: "/zones", icon: Lightbulb },
    { name: "Horarios", href: "/schedules", icon: Calendar },
    { name: "Consumo", href: "/reports", icon: BarChart3 },
    { name: "Equipos", href: "/devices", icon: Settings },
    ...(perms.canSeeUsuarios ? [{ name: "Usuarios", href: "/users", icon: Users }] : []),
  ]

  return (
    <>
      {/* Bottom sheet menu */}
      {showMenu && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowMenu(false)} />
          <div className="absolute bottom-0 left-0 right-0 bg-background rounded-t-2xl border-t border-border p-6 safe-area-bottom animate-in slide-in-from-bottom duration-200">
            <div className="flex items-center justify-between mb-6">
              <div>
                <p className="font-semibold text-foreground">{user?.nombre || session?.nombre || "Usuario"}</p>
                <p className="text-sm text-muted-foreground">{activeCasa?.nombre || "Sin casa"}</p>
              </div>
              <button onClick={() => setShowMenu(false)} className="p-2 rounded-xl hover:bg-secondary">
                <X className="h-5 w-5" />
              </button>
            </div>

            {user?.casas && user.casas.length > 1 && (
              <button
                onClick={() => { setShowMenu(false); changeHouse() }}
                className="flex items-center gap-3 w-full p-3 rounded-xl hover:bg-secondary transition-colors mb-2"
              >
                <ArrowLeftRight className="h-5 w-5 text-muted-foreground" />
                <span className="text-foreground">Cambiar casa</span>
              </button>
            )}

            <button
              onClick={() => { setShowMenu(false); logout() }}
              className="flex items-center gap-3 w-full p-3 rounded-xl hover:bg-red-50 transition-colors text-red-600"
            >
              <LogOut className="h-5 w-5" />
              <span>Cerrar sesión</span>
            </button>
          </div>
        </div>
      )}

      {/* Navigation bar */}
      <nav className="fixed bottom-0 left-0 right-0 z-40 bg-background/95 backdrop-blur-lg border-t border-border lg:hidden">
        <div className="flex items-center justify-around px-1 py-2 safe-area-bottom">
          {/* Avatar / menu button */}
          <button
            onClick={() => setShowMenu(true)}
            className="flex flex-col items-center gap-1 min-w-0 flex-1 py-1 rounded-lg transition-colors text-muted-foreground active:bg-secondary"
          >
            <div className="flex items-center justify-center h-8 w-8 rounded-full bg-primary text-primary-foreground text-xs font-bold">
              {user?.nombre?.charAt(0) || "U"}
            </div>
            <span className="text-[10px] font-medium leading-tight truncate">Cuenta</span>
          </button>

          {navItems.map((item) => {
            const isActive = item.href === currentPath
            return (
              <a
                key={item.name}
                href={item.href}
                className={cn(
                  "flex flex-col items-center gap-1 min-w-0 flex-1 py-1 rounded-lg transition-colors",
                  isActive ? "text-foreground" : "text-muted-foreground active:bg-secondary",
                )}
              >
                <div
                  className={cn(
                    "flex items-center justify-center h-8 w-8 rounded-xl transition-colors",
                    isActive && "bg-primary text-primary-foreground",
                  )}
                >
                  <item.icon className="h-[18px] w-[18px]" />
                </div>
                <span className={cn("text-[10px] font-medium leading-tight truncate", isActive && "font-semibold")}>
                  {item.name}
                </span>
              </a>
            )
          })}
        </div>
      </nav>
    </>
  )
}
