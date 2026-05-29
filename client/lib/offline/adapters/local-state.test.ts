import { describe, expect, it } from "vitest"
import { adaptLocalStateToSnapshot } from "./local-state"
import type { LocalState } from "@/lib/local-hub/types"
import type { SnapshotData } from "@/lib/offline/types"

const baseLocal: LocalState = {
  casa_id: "casa-1",
  casa_nombre: "Casa Aldo",
  server_timestamp: "2026-05-26T12:00:00+00:00",
  zonas: [
    {
      zona_id: "zona-1",
      nombre: "Sala",
      tipo: "sala",
      orden: 1,
      encendida: true,
      modo: "automatico",
      umbral_oscuridad: 40,
      auto_encender: true,
      tiempo_apagado_auto: 60,
    },
  ],
  dispositivos: [
    {
      id: "disp-1",
      zona_id: "zona-1",
      tipo: "modulo_shelly",
      nombre: "Lámpara sala",
      mac_address: "AA:BB:CC:DD:EE:FF",
    },
  ],
}

const baseFallback: SnapshotData = {
  server_timestamp: "2026-05-26T10:00:00+00:00",
  casa: { id: "casa-1", nombre: "Casa Aldo (cache)", zona_horaria: "America/Mexico_City" },
  zonas: [
    {
      zona: { id: "zona-1", nombre: "Sala cache", tipo: "sala", icono: "lightbulb", orden: 1 },
      config: {
        zona_id: "zona-1",
        encendida: false,
        modo: "manual",
        umbral_oscuridad: 30,
        auto_encender: false,
        tiempo_apagado_auto: 120,
        luz_ambiente_actual: 55,
        movimiento_detectado: true,
        temperatura_actual: 22.5,
        updated_at: "2026-05-26T09:00:00+00:00",
      },
    },
  ],
  dispositivos: [
    {
      id: "disp-1",
      zona_id: "zona-1",
      zona_nombre: "Sala",
      tipo: "modulo_shelly",
      nombre: "Lámpara sala",
      mac_address: "AA:BB:CC:DD:EE:FF",
      ip_local: "192.168.1.42",
      firmware_version: "1.2.3",
      estado: "online",
    },
  ],
  temporizadores: [
    {
      id: "timer-1",
      zona_id: "zona-1",
      zona_nombre: "Sala",
      tipo: "horario_fijo",
      hora_inicio: "18:00",
      hora_fin: "23:00",
      dias: { lunes: true, martes: true, miercoles: true, jueves: true, viernes: true, sabado: false, domingo: false },
      solo_si_oscuro: false,
      habilitado: true,
    },
  ],
  modo_nocturno: {
    habilitado: true,
    deteccion_inteligente: false,
    hora_inicio: "22:00",
    hora_fin: "07:00",
    zonas: [],
  },
}

describe("adaptLocalStateToSnapshot", () => {
  it("merges fallback into local for live + cloud-only data", () => {
    const result = adaptLocalStateToSnapshot(baseLocal, baseFallback)

    // Live data prevalece sobre fallback en la zona.
    expect(result.zonas[0].config?.encendida).toBe(true)
    expect(result.zonas[0].config?.modo).toBe("automatico")
    expect(result.zonas[0].config?.umbral_oscuridad).toBe(40)
    // Sensores (no llegan vía pi-hub) salen del fallback.
    expect(result.zonas[0].config?.luz_ambiente_actual).toBe(55)
    expect(result.zonas[0].config?.movimiento_detectado).toBe(true)
    expect(result.zonas[0].config?.temperatura_actual).toBe(22.5)
    // Icono no viene en /state — sale del fallback.
    expect(result.zonas[0].zona.icono).toBe("lightbulb")
    // Dispositivo: ip_local, firmware, zona_nombre del fallback.
    expect(result.dispositivos[0].ip_local).toBe("192.168.1.42")
    expect(result.dispositivos[0].firmware_version).toBe("1.2.3")
    expect(result.dispositivos[0].zona_nombre).toBe("Sala")
    // Cloud-only: temporizadores y modo_nocturno conservados.
    expect(result.temporizadores).toHaveLength(1)
    expect(result.modo_nocturno?.habilitado).toBe(true)
    // Casa: nombre del pi-hub, zona_horaria del fallback.
    expect(result.casa.nombre).toBe("Casa Aldo")
    expect(result.casa.zona_horaria).toBe("America/Mexico_City")
    // server_timestamp viene de /state.
    expect(result.server_timestamp).toBe("2026-05-26T12:00:00+00:00")
  })

  it("returns null/false defaults when no fallback (first boot in local mode)", () => {
    const result = adaptLocalStateToSnapshot(baseLocal, null)

    expect(result.zonas[0].zona.icono).toBeNull()
    expect(result.zonas[0].config?.luz_ambiente_actual).toBeNull()
    expect(result.zonas[0].config?.movimiento_detectado).toBe(false)
    expect(result.zonas[0].config?.temperatura_actual).toBeNull()
    expect(result.dispositivos[0].ip_local).toBeNull()
    expect(result.dispositivos[0].firmware_version).toBeNull()
    expect(result.dispositivos[0].zona_nombre).toBeNull()
    expect(result.dispositivos[0].estado).toBe("online")
    expect(result.temporizadores).toEqual([])
    expect(result.modo_nocturno).toBeNull()
    // Sin cache → zona_horaria queda null. No adivinamos TZ.
    expect(result.casa.zona_horaria).toBeNull()
  })

  it("ignores fallback zones the pi-hub does not report (pi-hub is authoritative for live state)", () => {
    const fallbackWithExtra: SnapshotData = {
      ...baseFallback,
      zonas: [
        ...baseFallback.zonas,
        {
          zona: { id: "zona-fantasma", nombre: "Fantasma", tipo: "habitacion", icono: null, orden: 99 },
          config: null,
        },
      ],
    }
    const result = adaptLocalStateToSnapshot(baseLocal, fallbackWithExtra)
    expect(result.zonas).toHaveLength(1)
    expect(result.zonas[0].zona.id).toBe("zona-1")
  })

  it("adds zones present in pi-hub but missing in fallback (sensors null)", () => {
    const localWithNew: LocalState = {
      ...baseLocal,
      zonas: [
        ...baseLocal.zonas,
        {
          zona_id: "zona-nueva",
          nombre: "Estudio",
          tipo: "habitacion",
          orden: 2,
          encendida: false,
          modo: "manual",
          umbral_oscuridad: 50,
          auto_encender: false,
          tiempo_apagado_auto: 90,
        },
      ],
    }
    const result = adaptLocalStateToSnapshot(localWithNew, baseFallback)
    expect(result.zonas).toHaveLength(2)
    const nueva = result.zonas.find((z) => z.zona.id === "zona-nueva")
    expect(nueva?.zona.icono).toBeNull()
    expect(nueva?.config?.luz_ambiente_actual).toBeNull()
    expect(nueva?.config?.movimiento_detectado).toBe(false)
  })
})
