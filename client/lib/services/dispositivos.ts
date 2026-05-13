import { api } from "@/lib/api/client"

export interface Dispositivo { id: string; zona_id: string; zona_nombre: string | null; tipo: string; nombre: string; mac_address: string | null; ip_local: string | null; firmware_version: string | null; estado: string }
export interface DispositivoCreate { zona_id: string; tipo: string; nombre: string; mac_address?: string; ip_local?: string }
export interface WifiConfig { wifi_ssid: string; wifi_password: string; nombre_instalacion?: string; zona_horaria?: string; email_alertas?: string }
interface Msg { message: string; success: boolean }

export const dispositivosService = {
  getDispositivos: (casaId: string) => api.get<Dispositivo[]>(`/casas/${casaId}/dispositivos`),
  createDispositivo: (casaId: string, data: DispositivoCreate) => api.post<Dispositivo>(`/casas/${casaId}/dispositivos`, data),
  deleteDispositivo: (id: string) => api.delete<Msg>(`/dispositivos/${id}`),
  saveWifiConfig: (casaId: string, data: WifiConfig) => api.post<Msg>(`/casas/${casaId}/wifi-config`, data),
}
