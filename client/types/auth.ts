// Auth types for multi-house architecture

export type Rol = "propietario" | "admin" | "encargado" | "usuario"

export type PermisoZona = "lectura" | "control" | "administracion"

export interface Casa {
  id: string
  nombre: string
  direccion: string
  fecha_corte_cfe?: number
}

export interface Usuario {
  id: string
  nombre: string
  email: string
  activo: boolean
}

export interface UsuarioCasa {
  usuario_id: string
  casa_id: string
  rol: Rol
}

export interface PermisoZonaRecord {
  usuario_id: string
  zona_id: string
  permiso: PermisoZona
}

// Session state stored after login + house selection
export interface AuthSession {
  usuario_id: string
  casa_id_activa: string
  rol: Rol
  zonas_permitidas?: string[]
  nombre?: string
}

// Extended user info with houses they belong to
export interface UserWithHouses extends Usuario {
  casas: (Casa & { rol: Rol })[]
}
