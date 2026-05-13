import { api } from "@/lib/api/client"

export interface Temporizador {
  id: string; zona_id: string; zona_nombre: string | null; tipo: string
  hora_inicio: string; hora_fin: string
  dias: { lunes: boolean; martes: boolean; miercoles: boolean; jueves: boolean; viernes: boolean; sabado: boolean; domingo: boolean }
  solo_si_oscuro: boolean; habilitado: boolean
}
export interface TemporizadorCreate {
  zona_id: string; tipo?: string; hora_inicio: string; hora_fin: string
  lunes?: boolean; martes?: boolean; miercoles?: boolean; jueves?: boolean; viernes?: boolean; sabado?: boolean; domingo?: boolean
  solo_si_oscuro?: boolean
}
export interface ZonaNocturna { zona_id: string; zona_nombre: string | null; zona_tipo: string | null; habilitada: boolean }
export interface ModoNocturno { habilitado: boolean; deteccion_inteligente: boolean; hora_inicio: string; hora_fin: string; zonas: ZonaNocturna[] }
interface Msg { message: string; success: boolean }

export const horariosService = {
  getTemporizadores: (casaId: string) => api.get<Temporizador[]>(`/casas/${casaId}/temporizadores`),
  createTemporizador: (casaId: string, data: TemporizadorCreate) => api.post<Temporizador>(`/casas/${casaId}/temporizadores`, data),
  updateTemporizador: (id: string, data: Partial<TemporizadorCreate> & { habilitado?: boolean }) => api.put<Temporizador>(`/temporizadores/${id}`, data),
  deleteTemporizador: (id: string) => api.delete<Msg>(`/temporizadores/${id}`),
  getModoNocturno: (casaId: string) => api.get<ModoNocturno>(`/casas/${casaId}/modo-nocturno`),
  updateModoNocturno: (casaId: string, data: Partial<ModoNocturno>) => api.put<Msg>(`/casas/${casaId}/modo-nocturno`, data),
}
