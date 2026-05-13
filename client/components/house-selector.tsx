"use client"

import { useEffect } from "react"
import { Home, MapPin, Crown, Shield, Users, UserCog } from "lucide-react"
import { useAuth } from "@/lib/auth/auth-context"
import type { Rol } from "@/types/auth"
import { cn } from "@/lib/utils"

const roleLabels: Record<Rol, { label: string; icon: typeof Crown; color: string }> = {
  propietario: { label: "Propietario", icon: Crown, color: "bg-amber-50 text-amber-600" },
  admin: { label: "Admin", icon: UserCog, color: "bg-purple-50 text-purple-600" },
  encargado: { label: "Encargado", icon: Shield, color: "bg-blue-50 text-blue-600" },
  usuario: { label: "Usuario", icon: Users, color: "bg-secondary text-muted-foreground" },
}

export function HouseSelector() {
  const { user, selectHouse, isLoading } = useAuth()

  useEffect(() => {
    if (!isLoading && !user) {
      window.location.href = "/login"
    }
  }, [user, isLoading])

  const handleSelectHouse = async (casaId: string, rol: Rol) => {
    if (!user) return
    await selectHouse(casaId, rol)
    window.location.href = "/"
  }

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-secondary/30 flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Cargando...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-secondary/30 flex flex-col items-center justify-center p-4 safe-area-top safe-area-bottom">
      {/* Logo */}
      <div className="text-center mb-8">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary mx-auto mb-4">
          <Home className="h-7 w-7 text-primary-foreground" />
        </div>
        <h1 className="text-2xl font-bold text-foreground">Mi Hogar</h1>
        <p className="text-sm text-muted-foreground mt-1">Hola, {user.nombre.split(" ")[0]}</p>
      </div>

      {/* Title */}
      <h2 className="text-lg font-semibold text-foreground mb-6">Selecciona una casa</h2>

      {/* House List */}
      <div className="w-full max-w-sm space-y-3">
        {user.casas.map((casa) => {
          const roleInfo = roleLabels[casa.rol]
          return (
            <button
              key={casa.id}
              onClick={() => handleSelectHouse(casa.id, casa.rol)}
              className="w-full flex items-start gap-4 p-4 rounded-xl bg-background border border-border hover:border-primary hover:shadow-md active:bg-secondary/50 transition-all text-left"
            >
              {/* House icon */}
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 flex-shrink-0">
                <Home className="h-6 w-6 text-primary" />
              </div>

              {/* House info */}
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-foreground text-sm">{casa.nombre}</h3>
                <div className="flex items-center gap-1.5 mt-1 text-muted-foreground">
                  <MapPin className="h-3 w-3 flex-shrink-0" />
                  <p className="text-xs truncate">{casa.direccion}</p>
                </div>
                {/* Role badge */}
                <span
                  className={cn(
                    "inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full mt-2",
                    roleInfo.color,
                  )}
                >
                  <roleInfo.icon className="h-2.5 w-2.5" />
                  {roleInfo.label}
                </span>
              </div>
            </button>
          )
        })}
      </div>

      {/* Footer */}
      <p className="text-center text-xs text-muted-foreground mt-8">
        Tus permisos dependen de tu rol en cada casa
      </p>
    </div>
  )
}
