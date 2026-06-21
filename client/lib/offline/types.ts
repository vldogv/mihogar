export interface SnapshotZonaInfo {
  id: string
  nombre: string
  tipo: string
  icono: string | null
  orden: number
}

export interface SnapshotZonaConfig {
  zona_id: string
  encendida: boolean
  modo: string
  umbral_oscuridad: number
  auto_encender: boolean
  tiempo_apagado_auto: number
  luz_ambiente_actual: number | null
  movimiento_detectado: boolean
  temperatura_actual: number | null
  updated_at: string | null
}

export interface SnapshotZona {
  zona: SnapshotZonaInfo
  config: SnapshotZonaConfig | null
}

export interface SnapshotTemporizador {
  id: string
  zona_id: string
  zona_nombre: string | null
  tipo: string
  hora_inicio: string
  hora_fin: string
  dias: Record<string, boolean>
  solo_si_oscuro: boolean
  habilitado: boolean
}

export interface SnapshotDispositivo {
  id: string
  zona_id: string
  zona_nombre: string | null
  tipo: string
  nombre: string
  mac_address: string | null
  ip_local: string | null
  firmware_version: string | null
  estado: string
}

export interface SnapshotZonaNocturna {
  zona_id: string
  zona_nombre: string | null
  zona_tipo: string | null
  habilitada: boolean
}

export interface SnapshotModoNocturno {
  habilitado: boolean
  deteccion_inteligente: boolean
  hora_inicio: string
  hora_fin: string
  zonas: SnapshotZonaNocturna[]
}

export interface SnapshotCasaInfo {
  id: string
  nombre: string
  zona_horaria: string | null
}

export interface SnapshotData {
  server_timestamp: string
  casa: SnapshotCasaInfo
  zonas: SnapshotZona[]
  temporizadores: SnapshotTemporizador[]
  dispositivos: SnapshotDispositivo[]
  modo_nocturno: SnapshotModoNocturno | null
}

export interface SnapshotMeta {
  casaId: string
  server_timestamp: string
  last_synced_at: string
}
