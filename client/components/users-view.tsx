"use client"

import { useState, useEffect, useCallback } from "react"
import { AppShell } from "@/components/app-shell"
import { UserCard } from "@/components/user-card"
import { AddUserModal } from "@/components/add-user-modal"
import { useAuth } from "@/lib/auth/auth-context"
import { usuariosService, type Usuario } from "@/lib/services/usuarios"
import { Users, UserPlus, Crown, Home, Shield } from "lucide-react"
import { cn } from "@/lib/utils"
import { usePermissions } from "@/lib/hooks/use-permissions"
import { panelService } from "@/lib/services/panel"

const roleLabels: Record<string, { label: string; icon: typeof Crown; color: string }> = {
  administrador: { label: "Administrador", icon: Crown, color: "bg-amber-50 text-amber-600" },
  encargado: { label: "Encargado", icon: Shield, color: "bg-blue-50 text-blue-600" },
  usuario: { label: "Usuario", icon: Users, color: "bg-secondary text-muted-foreground" },
  // Aliases
  admin: { label: "Administrador", icon: Crown, color: "bg-amber-50 text-amber-600" },
  user: { label: "Usuario", icon: Users, color: "bg-secondary text-muted-foreground" },
}

export function UsersView() {
  const { session, activeCasa } = useAuth()
  const casaId = session?.casa_id_activa
  const [users, setUsers] = useState<Usuario[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddUser, setShowAddUser] = useState(false)
  const perms = usePermissions()

  const fetchUsers = useCallback(async () => {
    if (!casaId) return
    try {
      const data = await usuariosService.getUsuarios(casaId)
      setUsers(data)
    } catch (err) {
      console.error("Error loading users:", err)
    } finally {
      setLoading(false)
    }
  }, [casaId])

  useEffect(() => { fetchUsers() }, [fetchUsers])

  const handleDeleteUser = async (userId: string) => {
    try {
      await usuariosService.deleteUsuario(userId)
      await fetchUsers()
    } catch (err) { console.error(err) }
  }

const [editingUser, setEditingUser] = useState<string | null>(null)
  const [editMode, setEditMode] = useState<"zones" | "role" | "password" | null>(null)
  const [editZones, setEditZones] = useState<string[]>([])
  const [editRole, setEditRole] = useState("")
  const [editPassword, setEditPassword] = useState("")
  const [allZones, setAllZones] = useState<{ id: string; nombre: string }[]>([])

  // Cargar zonas para el editor
  useEffect(() => {
    if (casaId) {
      panelService.getZonas(casaId).then(setAllZones).catch(console.error)
    }
  }, [casaId])

  const handleEditZones = (userId: string) => {
    const user = users.find(u => u.id === userId)
    if (!user) return
    setEditingUser(userId)
    setEditMode("zones")
    // Pre-cargar zonas actuales (necesitamos los IDs, no nombres)
    setEditZones([])
  }

  const handleEditRole = (userId: string) => {
    const user = users.find(u => u.id === userId)
    if (!user) return
    setEditingUser(userId)
    setEditMode("role")
    setEditRole(user.rol)
  }

  const handleEditPassword = (userId: string) => {
    setEditingUser(userId)
    setEditMode("password")
    setEditPassword("")
  }

  const handleSaveEdit = async () => {
    if (!editingUser) return
    try {
      if (editMode === "zones") {
        await usuariosService.updateUsuario(editingUser, { zonas_permitidas: editZones })
      } else if (editMode === "role") {
        await usuariosService.updateUsuario(editingUser, { rol: editRole })
      } else if (editMode === "password") {
        const { api } = await import("@/lib/api/client")
        await api.put(`/usuarios/${editingUser}/password`, { password: editPassword })
      }
      setEditingUser(null)
      setEditMode(null)
      await fetchUsers()
    } catch (err) { console.error(err) }
  }

  const handleAddUser = async (user: { name: string; email: string; password?: string; pin?: string; role: string; zones: string[] }) => {
    if (!casaId) return
    try {
      await usuariosService.createUsuario(casaId, {
        nombre: user.name,
        email: user.email || undefined,
        password: user.password || undefined,
        pin: user.pin || undefined,
        rol: user.role,
        zonas_permitidas: user.zones,
      })
      setShowAddUser(false)
      await fetchUsers()
    } catch (err) { console.error(err) }
  }

  // Map API users to the format UserCard expects
  const mappedUsers = users.map((u) => ({
    id: u.id,
    name: u.nombre,
    email: u.email || "",
    role: u.rol as "admin" | "encargado" | "user",
    zones: u.zonas_permitidas,
    isPinEnabled: u.metodo_acceso === "pin",
  }))

  if (loading) {
    return (
      <AppShell title="Usuarios y Permisos" subtitle="Administra el acceso a tu hogar" currentPath="/users">
        <div className="flex items-center justify-center py-20">
          <div className="animate-pulse text-muted-foreground">Cargando usuarios...</div>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell title="Usuarios y Permisos" subtitle="Administra el acceso a tu hogar" currentPath="/users">
      <div className="space-y-4">
        {/* House info */}
        <div className="rounded-xl border border-border bg-background p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 flex-shrink-0">
              <Home className="h-5 w-5 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-foreground text-sm">{activeCasa?.nombre || "Mi Hogar"}</h3>
              <p className="text-xs text-muted-foreground">{users.length} usuarios registrados</p>
            </div>
          </div>
        </div>

        {/* Role legend */}
        <div className="flex flex-wrap gap-3">
          {["administrador", "encargado", "usuario"].map((key) => {
            const value = roleLabels[key]
            if (!value) return null
            return (
              <div key={key} className="flex items-center gap-2">
                <div className={cn("flex h-7 w-7 items-center justify-center rounded-lg", value.color)}>
                  <value.icon className="h-3.5 w-3.5" />
                </div>
                <span className="text-xs text-muted-foreground">{value.label}</span>
              </div>
            )
          })}
        </div>

        {/* Add user button */}
       {perms.canAddUser && (
          <button
            onClick={() => setShowAddUser(true)}
            className="w-full flex items-center justify-center gap-2 px-4 py-4 rounded-xl border-2 border-dashed border-border text-muted-foreground hover:border-primary hover:text-foreground active:bg-secondary/50 transition-colors min-h-[52px]"
          >
            <UserPlus className="h-5 w-5" />
            <span className="font-medium text-sm">Agregar usuario</span>
          </button>
        )}

        {/* Users list */}
        <div className="space-y-3">
          {mappedUsers.map((u) => (
            <UserCard
              key={u.id}
              user={u}
              roleInfo={roleLabels[u.role] || roleLabels["usuario"]}
              onDelete={() => handleDeleteUser(u.id)}
              canDelete={perms.canDeleteUser && u.role !== "administrador"}
              onEditZones={handleEditZones}
              onEditRole={handleEditRole}
              onEditPassword={handleEditPassword}
            />
          ))}
        </div>

        {/*   PERMISOS INFO
        
        <div className="rounded-xl border border-border bg-background p-4">
          <h3 className="font-semibold text-foreground mb-4 text-sm">Permisos por rol</h3>
          <div className="space-y-3">
            {[
              { name: "Controlar luces", admin: true, encargado: true, user: true },
              { name: "Configurar temporizadores", admin: true, encargado: true, user: false },
              { name: "Ver reportes de consumo", admin: true, encargado: true, user: false },
              { name: "Agregar dispositivos", admin: true, encargado: false, user: false },
              { name: "Gestionar usuarios", admin: true, encargado: false, user: false },
              { name: "Configurar modo nocturno", admin: true, encargado: true, user: false },
            ].map((row) => (
              <div key={row.name} className="py-3 border-b border-border/50 last:border-0">
                <p className="text-sm font-medium text-foreground mb-2">{row.name}</p>
                <div className="flex gap-4 text-xs">
                  <span className={row.admin ? "text-amber-600" : "text-muted-foreground"}>Admin: {row.admin ? "Si" : "-"}</span>
                  <span className={row.encargado ? "text-blue-600" : "text-muted-foreground"}>Encargado: {row.encargado ? "Si" : "-"}</span>
                  <span className={row.user ? "text-emerald-600" : "text-muted-foreground"}>Usuario: {row.user ? "Si" : "-"}</span>
                </div>
              </div>
            ))}
          </div>
        </div>*/}
      
      </div>

      {showAddUser && <AddUserModal onClose={() => setShowAddUser(false)} onAdd={handleAddUser as any} />}

      {editingUser && editMode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-foreground/20 backdrop-blur-sm" onClick={() => { setEditingUser(null); setEditMode(null) }} />
          <div className="relative bg-background rounded-2xl shadow-xl w-full max-w-sm p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">
              {editMode === "zones" ? "Editar zonas" : editMode === "role" ? "Cambiar rol" : "Cambiar contraseña"}
            </h3>

            {editMode === "zones" && (
              <div className="grid grid-cols-2 gap-2">
                {allZones.map((zone) => (
                  <button key={zone.id}
                    onClick={() => setEditZones(prev => prev.includes(zone.id) ? prev.filter(z => z !== zone.id) : [...prev, zone.id])}
                    className={cn("px-3 py-2 rounded-xl text-sm font-medium transition-colors",
                      editZones.includes(zone.id) ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground")}>
                    {zone.nombre}
                  </button>
                ))}
              </div>
            )}

            {editMode === "role" && (
              <div className="space-y-2">
                {["encargado", "usuario"].map((r) => (
                  <button key={r} onClick={() => setEditRole(r)}
                    className={cn("w-full p-3 rounded-xl border text-sm text-left transition-colors",
                      editRole === r ? "border-primary bg-primary/5 font-medium" : "border-border")}>
                    {r === "encargado" ? "Encargado" : "Usuario"}
                  </button>
                ))}
              </div>
            )}

            {editMode === "password" && (
              <input type="password" value={editPassword} onChange={(e) => setEditPassword(e.target.value)}
                placeholder="Nueva contraseña" className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20" />
            )}

            <div className="flex gap-3 mt-6">
              <button onClick={() => { setEditingUser(null); setEditMode(null) }}
                className="flex-1 px-4 py-2.5 rounded-xl bg-secondary text-secondary-foreground font-medium text-sm">
                Cancelar
              </button>
              <button onClick={handleSaveEdit}
                className="flex-1 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground font-medium text-sm">
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}

    </AppShell>
  )
}
