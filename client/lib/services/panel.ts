import { api } from "@/lib/api/client"

export interface ZonaConfig {
  zona_id: string; encendida: boolean; modo: string; umbral_oscuridad: number
  auto_encender: boolean; tiempo_apagado_auto: number
  luz_ambiente_actual: number | null; movimiento_detectado: boolean; temperatura_actual: number | null
}

export interface Zona { id: string; nombre: string; tipo: string; icono: string | null; orden: number }
export interface ZonaConConfig { zona: Zona; config: ZonaConfig | null }
export interface PanelData { zonas_activas: number; zonas_total: number; zonas: ZonaConConfig[] }
interface Msg { message: string; success: boolean }

export const panelService = {
  getPanel: (casaId: string) => api.get<PanelData>(`/casas/${casaId}/panel`),
  getZonas: (casaId: string) => api.get<Zona[]>(`/casas/${casaId}/zonas`),
  getZonaDetail: (zonaId: string) => api.get<ZonaConConfig>(`/zonas/${zonaId}`),
  toggleZona: (zonaId: string, encendida: boolean) => api.put<Msg>(`/zonas/${zonaId}/toggle`, { encendida }),
  cambiarModo: (zonaId: string, modo: string) => api.put<Msg>(`/zonas/${zonaId}/modo`, { modo }),
  updateConfigZona: (zonaId: string, config: { umbral_oscuridad?: number; auto_encender?: boolean; tiempo_apagado_auto?: number }) =>
    api.put<Msg>(`/zonas/${zonaId}/config`, config),
  encenderTodo: (casaId: string) => api.post<Msg>(`/casas/${casaId}/encender-todo`),
  apagarTodo: (casaId: string) => api.post<Msg>(`/casas/${casaId}/apagar-todo`),
}
