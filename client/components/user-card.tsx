"use client"
import type React from "react"
import { useState } from "react"
import { MoreVertical, Trash2, Key, Mail, Shield, MapPin, Lock, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { usePermissions } from "@/lib/hooks/use-permissions"

interface User {
  id: string
  name: string
  email: string
  role: "admin" | "encargado" | "user" | "administrador" | "usuario"
  zones: string[]
  isPinEnabled?: boolean
}

interface RoleInfo {
  label: string
  icon: React.ElementType
  color: string
}

interface UserCardProps {
  user: User
  roleInfo: RoleInfo
  onDelete: () => void
  canDelete: boolean
  onEditZones?: (userId: string) => void
  onEditRole?: (userId: string) => void
  onEditPassword?: (userId: string) => void
}



export function UserCard({ user, roleInfo, onDelete, canDelete, onEditZones, onEditRole, onEditPassword }: UserCardProps) {
  const [showMenu, setShowMenu] = useState(false)
  const perms = usePermissions()

  const getInitials = (name: string) => {
    return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
  }

  const isTargetUsuario = ["user", "usuario"].includes(user.role)
  const isTargetAdmin = ["admin", "administrador"].includes(user.role)

  // Determinar qué opciones mostrar
  const canEditThisUser = perms.isAdmin || (perms.isEncargado && isTargetUsuario)
  const showEditRole = perms.isAdmin && !isTargetAdmin
  const showEditPassword = perms.isAdmin && !isTargetAdmin
  const showEditZones = canEditThisUser && isTargetUsuario
  const hasAnyAction = canDelete || showEditRole || showEditPassword || showEditZones

  
  return (
    <div className="rounded-xl border border-border bg-background p-3 sm:p-4">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground font-semibold text-sm flex-shrink-0">
          {getInitials(user.name)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h4 className="font-semibold text-foreground text-sm truncate">{user.name}</h4>
            <span className={cn("inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full", roleInfo.color)}>
              <roleInfo.icon className="h-2.5 w-2.5" />
              {roleInfo.label}
            </span>
          </div>
          <div className="mt-1.5 space-y-0.5">
            {user.email && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Mail className="h-3 w-3 flex-shrink-0" />
                <span className="truncate">{user.email}</span>
              </div>
            )}
            {user.isPinEnabled && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Key className="h-3 w-3 flex-shrink-0" />
                <span>PIN habilitado</span>
              </div>
            )}
          </div>
          <div className="mt-2 flex flex-wrap gap-1">
            {user.zones.map((zone) => (
              <span key={zone} className="px-1.5 py-0.5 rounded-md bg-secondary text-[10px] font-medium text-secondary-foreground">
                {zone}
              </span>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-1 relative">
          {canDelete && (
            <button onClick={onDelete} className="p-2 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors">
              <Trash2 className="h-4 w-4" />
            </button>
          )}
          {hasAnyAction && (
            <button onClick={() => setShowMenu(!showMenu)} className="p-2 rounded-lg hover:bg-secondary transition-colors">
              <MoreVertical className="h-4 w-4 text-muted-foreground" />
            </button>
          )}

          {/* Dropdown menu */}
          {showMenu && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowMenu(false)} />
              <div className="absolute right-0 top-10 z-50 w-48 bg-background rounded-xl border border-border shadow-lg py-1">
                {showEditZones && (
                  <button
                    onClick={() => { setShowMenu(false); onEditZones?.(user.id) }}
                    className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-foreground hover:bg-secondary transition-colors"
                  >
                    <MapPin className="h-4 w-4 text-muted-foreground" />
                    Editar zonas
                  </button>
                )}
                {showEditRole && (
                  <button
                    onClick={() => { setShowMenu(false); onEditRole?.(user.id) }}
                    className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-foreground hover:bg-secondary transition-colors"
                  >
                    <Shield className="h-4 w-4 text-muted-foreground" />
                    Cambiar rol
                  </button>
                )}
                {showEditPassword && (
                  <button
                    onClick={() => { setShowMenu(false); onEditPassword?.(user.id) }}
                    className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-foreground hover:bg-secondary transition-colors"
                  >
                    <Lock className="h-4 w-4 text-muted-foreground" />
                    Cambiar contraseña
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}