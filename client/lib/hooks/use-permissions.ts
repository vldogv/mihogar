"use client"

import { useAuth } from "@/lib/auth/auth-context"

export function usePermissions() {
  const { session } = useAuth()
  const rol = session?.rol || "usuario"

  const isAdmin = ["administrador", "owner", "propietario"].includes(rol)
  const isEncargado = rol === "encargado"
  const isUsuario = rol === "usuario"

  return {
    rol,
    isAdmin,
    isEncargado,
    isUsuario,

    // Navegación: todos ven todo excepto Usuarios
    canSeeUsuarios: isAdmin || isEncargado,
    canSeeDispositivos: true,
    canSeeConsumo: true,
    canSeeHorarios: true,

    // Gestión de usuarios
    canAddUser: isAdmin || isEncargado,
    canDeleteUser: isAdmin,
    canEditUserRole: isAdmin,
    canEditUserPassword: isAdmin,
    canAssignZones: isAdmin || isEncargado,
    canCreateRole: (targetRol: string) => {
      if (isAdmin) return true
      if (isEncargado) return targetRol === "usuario"
      return false
    },

    // Dispositivos
    canAddDevice: isAdmin,
    canRemoveDevice: isAdmin,
    canConfigWifi: isAdmin,

    // Zonas
    canToggleZone: true,
    canChangeModo: isAdmin || isEncargado,
    canEditZoneConfig: isAdmin || isEncargado,

    // Temporizadores
    canAddTimer: isAdmin || isEncargado,
    canDeleteTimer: isAdmin || isEncargado,

    // Modo nocturno y config
    canEditNightMode: isAdmin || isEncargado,
    canEditCorteCFE: isAdmin || isEncargado,
  }
}