"use client"

import { Power, PowerOff, Activity } from "lucide-react"

interface QuickActionsProps {
  onAllOn: () => void
  onAllOff: () => void
  onAutoAll: () => void
  isOnline: boolean
}

export function QuickActions({ onAllOn, onAllOff, onAutoAll, isOnline }: QuickActionsProps) {
  return (
    <section className="grid grid-cols-3 gap-1.5 sm:gap-2 lg:flex lg:flex-wrap lg:gap-3">
      <button
        onClick={onAllOn}
        disabled={!isOnline}
        className="flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-1.5 lg:gap-2 px-2 sm:px-3 lg:px-5 py-2.5 sm:py-3 rounded-lg sm:rounded-xl bg-emerald-50 text-emerald-700 font-medium text-[10px] sm:text-xs lg:text-sm hover:bg-emerald-100 active:bg-emerald-100 transition-colors min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-emerald-50"
      >
        <Power className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
        <span>Encender</span>
      </button>
      <button
        onClick={onAllOff}
        disabled={!isOnline}
        className="flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-1.5 lg:gap-2 px-2 sm:px-3 lg:px-5 py-2.5 sm:py-3 rounded-lg sm:rounded-xl bg-red-50 text-red-700 font-medium text-[10px] sm:text-xs lg:text-sm hover:bg-red-100 active:bg-red-100 transition-colors min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-red-50"
      >
        <PowerOff className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
        <span>Apagar</span>
      </button>
      <button
        onClick={onAutoAll}
        disabled={!isOnline}
        className="flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-1.5 lg:gap-2 px-2 sm:px-3 lg:px-5 py-2.5 sm:py-3 rounded-lg sm:rounded-xl bg-blue-50 text-blue-700 font-medium text-[10px] sm:text-xs lg:text-sm hover:bg-blue-100 active:bg-blue-100 transition-colors min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-blue-50"
      >
        <Activity className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
        <span>Auto</span>
      </button>
    </section>
  )
}
