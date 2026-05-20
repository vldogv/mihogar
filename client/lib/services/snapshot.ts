import { api } from "@/lib/api/client"
import type { SnapshotData } from "@/lib/offline/types"

export const snapshotService = {
  get: (casaId: string) => api.get<SnapshotData>(`/casas/${casaId}/snapshot`),
}
