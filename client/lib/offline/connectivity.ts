type Listener = (online: boolean) => void

let currentOnline: boolean =
  typeof navigator === "undefined" ? true : navigator.onLine

const listeners = new Set<Listener>()

function emit(): void {
  for (const l of listeners) l(currentOnline)
}

export function getOnline(): boolean {
  return currentOnline
}

export function markOnline(): void {
  if (currentOnline) return
  currentOnline = true
  emit()
}

export function markOffline(): void {
  if (!currentOnline) return
  currentOnline = false
  emit()
}

export function subscribe(listener: Listener): () => void {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

if (typeof window !== "undefined") {
  window.addEventListener("online", markOnline)
  window.addEventListener("offline", markOffline)
}
