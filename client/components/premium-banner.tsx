"use client"

import { Crown, Home, ArrowRight } from "lucide-react"

interface PremiumBannerProps {
  currentHouses: number
  maxHouses: number
}

export function PremiumBanner({ currentHouses, maxHouses }: PremiumBannerProps) {
  return (
    <div className="rounded-xl sm:rounded-2xl bg-gradient-to-r from-amber-50 to-amber-100 border border-amber-200 p-3 sm:p-4 lg:p-5">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 sm:h-10 sm:w-10 lg:h-12 lg:w-12 items-center justify-center rounded-lg sm:rounded-xl bg-amber-200/50 flex-shrink-0">
          <Crown className="h-4 w-4 sm:h-5 sm:w-5 lg:h-6 lg:w-6 text-amber-600" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-amber-800 text-xs sm:text-sm lg:text-base">Premium</h3>
            <span className="text-[10px] sm:text-xs text-amber-600 flex items-center gap-1">
              <Home className="h-3 w-3" />
              {currentHouses}/{maxHouses}
            </span>
          </div>
          <p className="text-[10px] sm:text-xs text-amber-700 mt-0.5 line-clamp-1">
            Gestiona hasta 3 casas
          </p>
        </div>

        <button className="flex items-center justify-center gap-1.5 px-3 sm:px-4 py-2 sm:py-2.5 rounded-lg sm:rounded-xl bg-amber-600 text-amber-50 font-medium text-[10px] sm:text-xs lg:text-sm hover:bg-amber-700 active:bg-amber-700 transition-colors whitespace-nowrap flex-shrink-0">
          <span className="hidden sm:inline">Obtener</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}
