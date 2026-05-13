"use client"

import type React from "react"
import { useState } from "react"
import { Home, Eye, EyeOff, Mail, Lock, Loader2 } from "lucide-react"
import { useAuth } from "@/lib/auth/auth-context"

export function LoginForm() {
  const { login, selectHouse } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setIsLoading(true)

    const result = await login(email, password)

    if (!result.success) {
      setError("Credenciales incorrectas. Verifica tu correo y contraseña.")
      setIsLoading(false)
      return
    }

    if (result.houses.length === 1) {
      const house = result.houses[0]
      // Guarda sesión antes de navegar
      await selectHouse(house.id, house.rol)
      // Pequeño delay para asegurar que localStorage se escribió
      await new Promise((resolve) => setTimeout(resolve, 50))
      window.location.href = "/"
    } else {
      // Múltiples casas - solo guardamos el user (ya lo hace login)
      // y navegamos a selección
      await new Promise((resolve) => setTimeout(resolve, 50))
      window.location.href = "/select-house"
    }
  }

  return (
    <div className="min-h-screen bg-secondary/30 flex items-center justify-center p-4 safe-area-top safe-area-bottom">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary mx-auto mb-4">
            <Home className="h-8 w-8 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold text-foreground">Mi Hogar</h1>
          <p className="text-muted-foreground mt-1 text-sm">Sistema de Domótica Inteligente</p>
        </div>

        <div className="rounded-2xl border border-border bg-background p-6 shadow-lg">
          <h2 className="text-lg font-semibold text-foreground mb-1">Iniciar sesión</h2>
          <p className="text-sm text-muted-foreground mb-6">Ingresa con tu cuenta</p>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-100 text-red-700 text-sm">{error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Correo electrónico</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="tu@email.com"
                  className="w-full pl-10 pr-4 py-3 rounded-xl border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                  autoComplete="email"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Contraseña</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Tu contraseña"
                  className="w-full pl-10 pr-10 py-3 rounded-xl border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground p-1"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-end">
              <button type="button" className="text-sm text-primary hover:underline">
                Olvidé mi contraseña
              </button>
            </div>

            <button
              type="submit"
              disabled={isLoading || !email || !password}
              className="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-primary text-primary-foreground font-medium hover:bg-primary/90 active:bg-primary/90 transition-colors disabled:opacity-50 min-h-[48px]"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Iniciando sesión...
                </>
              ) : (
                "Iniciar sesión"
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-muted-foreground mt-6">
          ¿No tienes cuenta?{" "}
          <button type="button" className="text-primary font-medium hover:underline">
            Contacta al administrador
          </button>
        </p>
      </div>
    </div>
  )
}
