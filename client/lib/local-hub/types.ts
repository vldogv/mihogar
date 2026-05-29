// Tipos del contrato HTTP local PWA ↔ Pi-hub (Fase 6).
// Espejo de docs/contrato-api-local-esp32.md. Mantener sincronizado.

export type LocalCommandStatus = "applied" | "stale" | "unknown_zone"

export interface LocalHealth {
  status: "ok"
  casa_id: string
}

export interface LocalInfo {
  device_id: string
  casa_id: string
  firmware_version: string
  capabilities: string[]
}

export interface LocalStateZona {
  zona_id: string
  nombre: string
  tipo: string
  orden: number
  encendida: boolean
  modo: string
  umbral_oscuridad: number
  auto_encender: boolean
  tiempo_apagado_auto: number
}

export interface LocalStateDispositivo {
  id: string
  zona_id: string
  tipo: string
  nombre: string
  mac_address: string | null
}

export interface LocalState {
  casa_id: string
  casa_nombre: string
  server_timestamp: string
  zonas: LocalStateZona[]
  dispositivos: LocalStateDispositivo[]
}

export interface LocalCommandRequest {
  client_id?: string
  client_timestamp?: string
}

export interface LocalToggleRequest extends LocalCommandRequest {
  encendida: boolean
}

export interface LocalModeRequest extends LocalCommandRequest {
  modo: string
}

export interface LocalCommandResponse {
  client_id?: string
  zona_id: string
  status: LocalCommandStatus
  server_timestamp: string
}

export interface LocalSceneResponse {
  client_id?: string
  status: LocalCommandStatus
  server_timestamp: string
  zonas_afectadas: string[]
}
