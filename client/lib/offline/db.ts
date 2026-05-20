import { openDB, type IDBPDatabase, type IDBPTransaction } from "idb"
import type {
  SnapshotCasaInfo,
  SnapshotData,
  SnapshotDispositivo,
  SnapshotMeta,
  SnapshotModoNocturno,
  SnapshotTemporizador,
  SnapshotZona,
} from "./types"

const DB_NAME = "mihogar"
const DB_VERSION = 1

const STORE_META = "snapshot_meta"
const STORE_ZONAS = "zonas"
const STORE_DISPOSITIVOS = "dispositivos"
const STORE_TEMPORIZADORES = "temporizadores"
const STORE_MODO_NOCTURNO = "modo_nocturno"

const ALL_STORES = [
  STORE_META,
  STORE_ZONAS,
  STORE_DISPOSITIVOS,
  STORE_TEMPORIZADORES,
  STORE_MODO_NOCTURNO,
] as const

interface MetaRecord extends SnapshotMeta {
  casa: SnapshotCasaInfo
}

interface ZonaRecord extends SnapshotZona {
  id: string
  casa_id: string
}

interface DispositivoRecord extends SnapshotDispositivo {
  casa_id: string
}

interface TemporizadorRecord extends SnapshotTemporizador {
  casa_id: string
}

interface ModoNocturnoRecord extends SnapshotModoNocturno {
  casa_id: string
}

type RwTx = IDBPTransaction<unknown, string[], "readwrite">

let dbPromise: Promise<IDBPDatabase> | null = null

function getDb(): Promise<IDBPDatabase> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("IndexedDB no disponible en server"))
  }
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains(STORE_META)) {
          db.createObjectStore(STORE_META, { keyPath: "casaId" })
        }
        if (!db.objectStoreNames.contains(STORE_ZONAS)) {
          const s = db.createObjectStore(STORE_ZONAS, { keyPath: "id" })
          s.createIndex("by_casa", "casa_id")
        }
        if (!db.objectStoreNames.contains(STORE_DISPOSITIVOS)) {
          const s = db.createObjectStore(STORE_DISPOSITIVOS, { keyPath: "id" })
          s.createIndex("by_casa", "casa_id")
        }
        if (!db.objectStoreNames.contains(STORE_TEMPORIZADORES)) {
          const s = db.createObjectStore(STORE_TEMPORIZADORES, { keyPath: "id" })
          s.createIndex("by_casa", "casa_id")
        }
        if (!db.objectStoreNames.contains(STORE_MODO_NOCTURNO)) {
          db.createObjectStore(STORE_MODO_NOCTURNO, { keyPath: "casa_id" })
        }
      },
    })
  }
  return dbPromise
}

async function deleteByCasa(
  tx: RwTx,
  storeName: string,
  casaId: string,
): Promise<void> {
  const store = tx.objectStore(storeName)
  const index = store.index("by_casa")
  let cursor = await index.openCursor(IDBKeyRange.only(casaId))
  while (cursor) {
    await cursor.delete()
    cursor = await cursor.continue()
  }
}

export async function saveSnapshot(
  casaId: string,
  snapshot: SnapshotData,
): Promise<void> {
  const db = await getDb()
  const tx = db.transaction([...ALL_STORES], "readwrite") as RwTx

  await deleteByCasa(tx, STORE_ZONAS, casaId)
  await deleteByCasa(tx, STORE_DISPOSITIVOS, casaId)
  await deleteByCasa(tx, STORE_TEMPORIZADORES, casaId)
  await tx.objectStore(STORE_MODO_NOCTURNO).delete(casaId)

  for (const z of snapshot.zonas) {
    const record: ZonaRecord = { ...z, id: z.zona.id, casa_id: casaId }
    await tx.objectStore(STORE_ZONAS).put(record)
  }
  for (const d of snapshot.dispositivos) {
    const record: DispositivoRecord = { ...d, casa_id: casaId }
    await tx.objectStore(STORE_DISPOSITIVOS).put(record)
  }
  for (const t of snapshot.temporizadores) {
    const record: TemporizadorRecord = { ...t, casa_id: casaId }
    await tx.objectStore(STORE_TEMPORIZADORES).put(record)
  }
  if (snapshot.modo_nocturno) {
    const record: ModoNocturnoRecord = { ...snapshot.modo_nocturno, casa_id: casaId }
    await tx.objectStore(STORE_MODO_NOCTURNO).put(record)
  }

  const meta: MetaRecord = {
    casaId,
    server_timestamp: snapshot.server_timestamp,
    last_synced_at: new Date().toISOString(),
    casa: snapshot.casa,
  }
  await tx.objectStore(STORE_META).put(meta)

  await tx.done
}

export async function loadSnapshot(
  casaId: string,
): Promise<SnapshotData | null> {
  const db = await getDb()
  const meta = (await db.get(STORE_META, casaId)) as MetaRecord | undefined
  if (!meta) return null

  const [zonasRaw, dispositivosRaw, temporizadoresRaw, modoNocturnoRaw] =
    await Promise.all([
      db.getAllFromIndex(STORE_ZONAS, "by_casa", casaId) as Promise<ZonaRecord[]>,
      db.getAllFromIndex(STORE_DISPOSITIVOS, "by_casa", casaId) as Promise<DispositivoRecord[]>,
      db.getAllFromIndex(STORE_TEMPORIZADORES, "by_casa", casaId) as Promise<TemporizadorRecord[]>,
      db.get(STORE_MODO_NOCTURNO, casaId) as Promise<ModoNocturnoRecord | undefined>,
    ])

  const zonas: SnapshotZona[] = zonasRaw
    .map(({ casa_id: _c, id: _id, ...rest }) => rest as SnapshotZona)
    .sort((a, b) => a.zona.orden - b.zona.orden)

  const dispositivos: SnapshotDispositivo[] = dispositivosRaw.map(
    ({ casa_id: _c, ...rest }) => rest as SnapshotDispositivo,
  )

  const temporizadores: SnapshotTemporizador[] = temporizadoresRaw.map(
    ({ casa_id: _c, ...rest }) => rest as SnapshotTemporizador,
  )

  const modo_nocturno: SnapshotModoNocturno | null = modoNocturnoRaw
    ? (({ casa_id: _c, ...rest }) => rest as SnapshotModoNocturno)(modoNocturnoRaw)
    : null

  return {
    server_timestamp: meta.server_timestamp,
    casa: meta.casa,
    zonas,
    temporizadores,
    dispositivos,
    modo_nocturno,
  }
}

export async function getSnapshotMeta(
  casaId: string,
): Promise<SnapshotMeta | null> {
  const db = await getDb()
  const meta = (await db.get(STORE_META, casaId)) as MetaRecord | undefined
  if (!meta) return null
  const { casa: _casa, ...rest } = meta
  return rest
}

export async function clearSnapshot(casaId: string): Promise<void> {
  const db = await getDb()
  const tx = db.transaction([...ALL_STORES], "readwrite") as RwTx
  await deleteByCasa(tx, STORE_ZONAS, casaId)
  await deleteByCasa(tx, STORE_DISPOSITIVOS, casaId)
  await deleteByCasa(tx, STORE_TEMPORIZADORES, casaId)
  await tx.objectStore(STORE_MODO_NOCTURNO).delete(casaId)
  await tx.objectStore(STORE_META).delete(casaId)
  await tx.done
}
