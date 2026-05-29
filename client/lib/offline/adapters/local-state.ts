import type {
  LocalState,
  LocalStateDispositivo,
  LocalStateZona,
} from "@/lib/local-hub/types"
import type {
  SnapshotData,
  SnapshotDispositivo,
  SnapshotZona,
  SnapshotZonaConfig,
  SnapshotZonaInfo,
} from "@/lib/offline/types"

function adaptZona(
  local: LocalStateZona,
  fallback: SnapshotZona | undefined,
  serverTimestamp: string,
): SnapshotZona {
  const fallbackInfo = fallback?.zona
  const fallbackConfig = fallback?.config

  const zona: SnapshotZonaInfo = {
    id: local.zona_id,
    nombre: local.nombre,
    tipo: local.tipo,
    icono: fallbackInfo?.icono ?? null,
    orden: local.orden,
  }

  const config: SnapshotZonaConfig = {
    zona_id: local.zona_id,
    encendida: local.encendida,
    modo: local.modo,
    umbral_oscuridad: local.umbral_oscuridad,
    auto_encender: local.auto_encender,
    tiempo_apagado_auto: local.tiempo_apagado_auto,
    luz_ambiente_actual: fallbackConfig?.luz_ambiente_actual ?? null,
    movimiento_detectado: fallbackConfig?.movimiento_detectado ?? false,
    temperatura_actual: fallbackConfig?.temperatura_actual ?? null,
    updated_at: serverTimestamp,
  }

  return { zona, config }
}

function adaptDispositivo(
  local: LocalStateDispositivo,
  fallback: SnapshotDispositivo | undefined,
): SnapshotDispositivo {
  return {
    id: local.id,
    zona_id: local.zona_id,
    zona_nombre: fallback?.zona_nombre ?? null,
    tipo: local.tipo,
    nombre: local.nombre,
    mac_address: local.mac_address,
    ip_local: fallback?.ip_local ?? null,
    firmware_version: fallback?.firmware_version ?? null,
    estado: fallback?.estado ?? "online",
  }
}

export function adaptLocalStateToSnapshot(
  local: LocalState,
  fallback: SnapshotData | null,
): SnapshotData {
  const fallbackZonasById = new Map<string, SnapshotZona>(
    (fallback?.zonas ?? []).map((z) => [z.zona.id, z]),
  )
  const fallbackDispositivosById = new Map<string, SnapshotDispositivo>(
    (fallback?.dispositivos ?? []).map((d) => [d.id, d]),
  )

  const zonas = local.zonas.map((z) =>
    adaptZona(z, fallbackZonasById.get(z.zona_id), local.server_timestamp),
  )

  const dispositivos = local.dispositivos.map((d) =>
    adaptDispositivo(d, fallbackDispositivosById.get(d.id)),
  )

  return {
    server_timestamp: local.server_timestamp,
    casa: {
      id: local.casa_id,
      nombre: local.casa_nombre,
      zona_horaria: fallback?.casa.zona_horaria ?? null,
    },
    zonas,
    dispositivos,
    temporizadores: fallback?.temporizadores ?? [],
    modo_nocturno: fallback?.modo_nocturno ?? null,
  }
}
