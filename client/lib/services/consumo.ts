import { api } from "@/lib/api/client"

export interface ConsumoResumen { consumo_hoy_kwh: number; horas_uso_hoy: number; bimestre_kwh: number; bimestre_costo: number; horas_uso_dia_promedio: number; corte_cfe_dia: number }
export interface ConsumoDiario { zona_id: string; zona_nombre: string | null; fecha: string; kwh_total: number; horas_encendido: number }
export interface HorasPico { zona_id: string; zona_nombre: string | null; hora: number; dia_semana: number; minutos_promedio: number }
export interface ConsumoBimestral { bimestre: number; anio: number; kwh_total: number; costo_estimado: number; horas_uso_dia: number }
export interface Alerta { id: string; tipo: string; severidad: string; titulo: string; mensaje: string; leida: boolean; created_at: string | null }
interface Msg { message: string; success: boolean }

export const consumoService = {
  getResumen: (casaId: string) => api.get<ConsumoResumen>(`/casas/${casaId}/consumo/resumen`),
  getDiario: (casaId: string, desde: string, hasta: string) => api.get<ConsumoDiario[]>(`/casas/${casaId}/consumo/diario?desde=${desde}&hasta=${hasta}`),
  getHorasPico: (casaId: string) => api.get<HorasPico[]>(`/casas/${casaId}/consumo/horas-pico`),
  getBimestral: (casaId: string) => api.get<ConsumoBimestral[]>(`/casas/${casaId}/consumo/bimestral`),
  getAlertas: (casaId: string, limit = 20) => api.get<Alerta[]>(`/casas/${casaId}/alertas?limit=${limit}`),
  marcarAlertaLeida: (alertaId: string) => api.put<Msg>(`/alertas/${alertaId}/leer`),
}
