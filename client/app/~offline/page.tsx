import { WifiOff } from "lucide-react"

export const metadata = {
  title: "Sin conexión — Mi Hogar",
}

export default function OfflinePage() {
  return (
    <div className="min-h-screen bg-secondary/30 flex items-center justify-center p-4 safe-area-top safe-area-bottom">
      <div className="w-full max-w-sm">
        <div className="text-center mb-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary mx-auto mb-4">
            <WifiOff className="h-8 w-8 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold text-foreground">Sin conexión</h1>
        </div>
        <div className="rounded-2xl border border-border bg-background p-6 shadow-lg text-center">
          <p className="text-sm text-foreground mb-2">
            No pudimos cargar esta página estando offline.
          </p>
          <p className="text-sm text-muted-foreground">
            Abrí una vista que ya hayas visitado para ver los datos guardados.
            Cuando vuelva la conexión, todo se sincroniza automáticamente.
          </p>
        </div>
      </div>
    </div>
  )
}
