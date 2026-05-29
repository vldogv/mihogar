import { panelService } from "@/lib/services/panel"
import { localHub } from "@/lib/local-hub/client"
import type { HubMode } from "@/lib/local-hub/mode-context"
import type { LocalCommandStatus } from "@/lib/local-hub/types"

// Capa que rutea comandos de zona/escena al cloud (panelService) o al pi-hub
// según el `mode` activo. Las views llaman a este service en vez de a
// panelService directo, para no quedarse acopladas al transporte.

export class HomeControlStaleError extends Error {
  constructor(message = "El cambio fue ignorado: hay un estado más nuevo") {
    super(message)
    this.name = "HomeControlStaleError"
  }
}

export class HomeControlUnknownZoneError extends Error {
  zonaId: string
  constructor(zonaId: string) {
    super(`La zona ${zonaId} no existe en el hub local`)
    this.name = "HomeControlUnknownZoneError"
    this.zonaId = zonaId
  }
}

interface CommandContext {
  mode: HubMode
  hubBaseURL: string | null
}

function ensureLocalApplied(
  status: LocalCommandStatus,
  zonaId: string,
): void {
  if (status === "applied") return
  if (status === "stale") throw new HomeControlStaleError()
  if (status === "unknown_zone") throw new HomeControlUnknownZoneError(zonaId)
}

function nowIso(): string {
  return new Date().toISOString()
}

function newClientId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export const homeControl = {
  toggleZona: async (
    ctx: CommandContext,
    zonaId: string,
    encendida: boolean,
  ): Promise<void> => {
    if (ctx.mode === "local-hub" && ctx.hubBaseURL) {
      const res = await localHub.zoneToggle(ctx.hubBaseURL, zonaId, {
        encendida,
        client_id: newClientId(),
        client_timestamp: nowIso(),
      })
      ensureLocalApplied(res.status, zonaId)
      return
    }
    await panelService.toggleZona(zonaId, encendida)
  },

  cambiarModo: async (
    ctx: CommandContext,
    zonaId: string,
    modo: string,
  ): Promise<void> => {
    if (ctx.mode === "local-hub" && ctx.hubBaseURL) {
      const res = await localHub.zoneMode(ctx.hubBaseURL, zonaId, {
        modo,
        client_id: newClientId(),
        client_timestamp: nowIso(),
      })
      ensureLocalApplied(res.status, zonaId)
      return
    }
    await panelService.cambiarModo(zonaId, modo)
  },

  encenderTodo: async (
    ctx: CommandContext,
    casaId: string,
  ): Promise<void> => {
    if (ctx.mode === "local-hub" && ctx.hubBaseURL) {
      const res = await localHub.sceneAllOn(ctx.hubBaseURL, {
        client_id: newClientId(),
        client_timestamp: nowIso(),
      })
      ensureLocalApplied(res.status, "*")
      return
    }
    await panelService.encenderTodo(casaId)
  },

  apagarTodo: async (
    ctx: CommandContext,
    casaId: string,
  ): Promise<void> => {
    if (ctx.mode === "local-hub" && ctx.hubBaseURL) {
      const res = await localHub.sceneAllOff(ctx.hubBaseURL, {
        client_id: newClientId(),
        client_timestamp: nowIso(),
      })
      ensureLocalApplied(res.status, "*")
      return
    }
    await panelService.apagarTodo(casaId)
  },
}
