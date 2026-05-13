import { api } from "@/lib/api/client"

export interface PermisoZona { zona_id: string; zona_nombre: string | null; puede_controlar: boolean; puede_configurar: boolean }
export interface Usuario { id: string; nombre: string; email: string | null; rol: string; metodo_acceso: string; zonas_permitidas: string[]; permisos: PermisoZona[] }
export interface UsuarioCreate { nombre: string; email?: string; password?: string; pin?: string; rol?: string; zonas_permitidas?: string[] }
export interface UsuarioUpdate { nombre?: string; email?: string; rol?: string; zonas_permitidas?: string[] }
export interface PermisosRol { administrador: string[]; encargado: string[]; usuario: string[] }
interface Msg { message: string; success: boolean }

export const usuariosService = {
  getUsuarios: (casaId: string) => api.get<Usuario[]>(`/casas/${casaId}/usuarios`),
  createUsuario: (casaId: string, data: UsuarioCreate) => api.post<Usuario>(`/casas/${casaId}/usuarios`, data),
  updateUsuario: (id: string, data: UsuarioUpdate) => api.put<Usuario>(`/usuarios/${id}`, data),
  deleteUsuario: (id: string) => api.delete<Msg>(`/usuarios/${id}`),
  getPermisosRol: (casaId: string) => api.get<PermisosRol>(`/casas/${casaId}/permisos-rol`),
}
