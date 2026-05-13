"use client"

import { useState } from "react"
import { AppShell } from "@/components/app-shell"
import { UserCard } from "@/components/user-card"
import { AddUserModal } from "@/components/add-user-modal"
import { useAuth } from "@/lib/auth/auth-context"
import { Users, UserPlus, Crown, Home, Shield } from "lucide-react"
import { cn } from "@/lib/utils"

interface User {
  id: string
  name: string
  email: string
  role: "admin" | "encargado" | "user"
  zones: string[]
  avatar?: string
  isPinEnabled?: boolean
}

const initialUsers: User[] = [
  { id: "1", name: "Admin Principal", email: "admin@mihogar.com", role: "admin", zones: ["all"] },
  {
    id: "2",
    name: "María García",
    email: "maria@mihogar.com",
    role: "encargado",
    zones: ["sala", "cocina", "recamara-principal"],
  },
  { id: "3", name: "Carlos Jr.", email: "", role: "user", zones: ["recamara-2"], isPinEnabled: true },
]

const roleLabels = {
  admin: { label: "Administrador", icon: Crown, color: "bg-amber-50 text-amber-600" },
  encargado: { label: "Encargado", icon: Shield, color: "bg-blue-50 text-blue-600" },
  user: { label: "Usuario", icon: Users, color: "bg-secondary text-muted-foreground" },
}

export function UsersView() {
  const { session, activeCasa } = useAuth()
  const [users, setUsers] = useState(initialUsers)
  const [showAddUser, setShowAddUser] = useState(false)

  const handleDeleteUser = (userId: string) => {
    setUsers((prev) => prev.filter((u) => u.id !== userId))
  }

  const handleAddUser = (user: Omit<User, "id">) => {
    setUsers((prev) => [...prev, { ...user, id: Date.now().toString() }])
    setShowAddUser(false)
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
          {Object.entries(roleLabels).map(([key, value]) => (
            <div key={key} className="flex items-center gap-2">
              <div className={cn("flex h-7 w-7 items-center justify-center rounded-lg", value.color)}>
                <value.icon className="h-3.5 w-3.5" />
              </div>
              <span className="text-xs text-muted-foreground">{value.label}</span>
            </div>
          ))}
        </div>

        {/* Add user button */}
        <button
          onClick={() => setShowAddUser(true)}
          className="w-full flex items-center justify-center gap-2 px-4 py-4 rounded-xl border-2 border-dashed border-border text-muted-foreground hover:border-primary hover:text-foreground active:bg-secondary/50 transition-colors min-h-[52px]"
        >
          <UserPlus className="h-5 w-5" />
          <span className="font-medium text-sm">Agregar usuario</span>
        </button>

        {/* Users list - vertical stack */}
        <div className="space-y-3">
          {users.map((u) => (
            <UserCard
              key={u.id}
              user={u}
              roleInfo={roleLabels[u.role]}
              onDelete={() => handleDeleteUser(u.id)}
              canDelete={u.role !== "admin"}
            />
          ))}
        </div>

        {/* Permission info - vertical cards on mobile */}
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
                  <span className={row.admin ? "text-amber-600" : "text-muted-foreground"}>
                    Admin: {row.admin ? "Si" : "-"}
                  </span>
                  <span className={row.encargado ? "text-blue-600" : "text-muted-foreground"}>
                    Encargado: {row.encargado ? "Si" : "-"}
                  </span>
                  <span className={row.user ? "text-emerald-600" : "text-muted-foreground"}>
                    Usuario: {row.user ? "Si" : "-"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {showAddUser && <AddUserModal onClose={() => setShowAddUser(false)} onAdd={handleAddUser} />}
    </AppShell>
  )
}
