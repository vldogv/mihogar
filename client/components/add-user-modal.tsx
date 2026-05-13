"use client"

import { useState, useEffect } from "react"
import { X, UserPlus, Key } from "lucide-react"
import { cn } from "@/lib/utils"
import { Switch } from "@/components/ui/switch"
import { useAuth } from "@/lib/auth/auth-context"
import { panelService } from "@/lib/services/panel"
import { usePermissions } from "@/lib/hooks/use-permissions"


interface AddUserModalProps {
  onClose: () => void
  onAdd: (user: { name: string; email: string; password?: string; pin?: string; role: string; zones: string[] }) => void
}


export function AddUserModal({ onClose, onAdd }: AddUserModalProps) {
  const { session } = useAuth()
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [role, setRole] = useState<"encargado" | "usuario">("usuario")
  const [selectedZones, setSelectedZones] = useState<string[]>([])
  const [usePinAccess, setUsePinAccess] = useState(false)
  const [pin, setPin] = useState("")
  const [zones, setZones] = useState<{ id: string; nombre: string }[]>([])
  const perms = usePermissions()

  const roles = [
    ...(perms.canCreateRole("encargado") ? [{ id: "encargado" as const, name: "Encargado", description: "Acceso completo a esta casa" }] : []),
    { id: "usuario" as const, name: "Usuario", description: "Acceso limitado a zonas asignadas" },
  ]

  useEffect(() => {
    if (session?.casa_id_activa) {
      panelService.getZonas(session.casa_id_activa).then(setZones).catch(console.error)
    }
  }, [session])

  const toggleZone = (zoneId: string) => {
    setSelectedZones((prev) => (prev.includes(zoneId) ? prev.filter((z) => z !== zoneId) : [...prev, zoneId]))
  }

  const handleSubmit = () => {
    onAdd({
      name,
      email: usePinAccess ? "" : email,
      password: usePinAccess ? undefined : password,
      pin: usePinAccess ? pin : undefined,
      role,
      zones: role === "encargado" ? [] : selectedZones,
    })
  }

  const isValid = name &&
    (usePinAccess ? pin.length === 4 : (email && password.length >= 4)) &&
    (role === "encargado" || selectedZones.length > 0)

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4">
      <div className="absolute inset-0 bg-foreground/20 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-background rounded-t-2xl sm:rounded-2xl shadow-xl w-full sm:max-w-md p-5 sm:p-6 max-h-[90vh] overflow-y-auto safe-area-bottom">
        <button onClick={onClose} className="absolute top-4 right-4 p-2 rounded-lg hover:bg-secondary transition-colors">
          <X className="h-5 w-5 text-muted-foreground" />
        </button>

        <div className="flex items-center gap-3 mb-5 sm:mb-6">
          <div className="flex h-10 w-10 sm:h-12 sm:w-12 items-center justify-center rounded-xl bg-primary/10 flex-shrink-0">
            <UserPlus className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
          </div>
          <div>
            <h3 className="text-base sm:text-lg font-semibold text-foreground">Agregar usuario</h3>
            <p className="text-xs sm:text-sm text-muted-foreground">Invita a alguien a tu hogar</p>
          </div>
        </div>

        <div className="space-y-4 sm:space-y-5">
          <div>
            <label className="block text-xs sm:text-sm font-medium text-foreground mb-1.5">Nombre</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Nombre del usuario"
              className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20" />
          </div>

          {!usePinAccess && (
            <>
              <div>
                <label className="block text-xs sm:text-sm font-medium text-foreground mb-1.5">Email</label>
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="usuario@email.com"
                  className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20" />
              </div>
              <div>
                <label className="block text-xs sm:text-sm font-medium text-foreground mb-1.5">Contraseña</label>
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Mínimo 4 caracteres"
                  className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20" />
              </div>
            </>
          )}

          <div>
            <label className="block text-xs sm:text-sm font-medium text-foreground mb-2">Rol</label>
            <div className="space-y-2">
              {roles.map((r) => (
                <button key={r.id} onClick={() => setRole(r.id)}
                  className={cn("w-full flex items-center gap-3 p-3 sm:p-4 rounded-xl border transition-colors text-left",
                    role === r.id ? "border-primary bg-primary/5" : "border-border hover:border-primary/50")}>
                  <div className={cn("h-5 w-5 rounded-full border-2 flex items-center justify-center flex-shrink-0",
                    role === r.id ? "border-primary" : "border-muted-foreground")}>
                    {role === r.id && <div className="h-2.5 w-2.5 rounded-full bg-primary" />}
                  </div>
                  <div>
                    <p className="font-medium text-foreground text-sm">{r.name}</p>
                    <p className="text-xs sm:text-sm text-muted-foreground">{r.description}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {role === "usuario" && (
            <div>
              <label className="block text-xs sm:text-sm font-medium text-foreground mb-2">Zonas permitidas</label>
              <div className="grid grid-cols-2 gap-1.5 sm:gap-2">
                {zones.map((zone) => (
                  <button key={zone.id} onClick={() => toggleZone(zone.id)}
                    className={cn("px-3 sm:px-4 py-2 sm:py-2.5 rounded-xl text-xs sm:text-sm font-medium transition-colors",
                      selectedZones.includes(zone.id) ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground hover:bg-secondary/80")}>
                    {zone.nombre}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="p-3 sm:p-4 rounded-xl bg-secondary/50">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 sm:gap-3">
                <Key className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground flex-shrink-0" />
                <div>
                  <p className="font-medium text-foreground text-sm">Acceso con PIN</p>
                  <p className="text-[10px] sm:text-xs text-muted-foreground">Sin email (niños, adultos mayores)</p>
                </div>
              </div>
              <Switch checked={usePinAccess} onCheckedChange={setUsePinAccess} />
            </div>
            {usePinAccess && (
              <div className="mt-3 sm:mt-4">
                <label className="block text-xs sm:text-sm font-medium text-foreground mb-1.5">PIN de 4 dígitos</label>
                <input type="password" maxLength={4} value={pin} onChange={(e) => setPin(e.target.value.replace(/\D/g, ""))} placeholder="0000"
                  className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-foreground text-center text-lg tracking-widest font-mono focus:outline-none focus:ring-2 focus:ring-primary/20" />
              </div>
            )}
          </div>
        </div>

        <div className="flex gap-2 sm:gap-3 mt-5 sm:mt-6">
          <button onClick={onClose} className="flex-1 px-4 sm:px-5 py-2.5 sm:py-3 rounded-xl bg-secondary text-secondary-foreground font-medium text-xs sm:text-sm hover:bg-secondary/80 transition-colors">
            Cancelar
          </button>
          <button onClick={handleSubmit} disabled={!isValid}
            className="flex-1 px-4 sm:px-5 py-2.5 sm:py-3 rounded-xl bg-primary text-primary-foreground font-medium text-xs sm:text-sm hover:bg-primary/90 transition-colors disabled:opacity-50">
            Agregar
          </button>
        </div>
      </div>
    </div>
  )
}