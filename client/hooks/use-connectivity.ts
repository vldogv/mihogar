"use client"

import { useEffect, useState } from "react"
import { getOnline, subscribe } from "@/lib/offline/connectivity"

export function useConnectivity(): { isOnline: boolean } {
  const [isOnline, setIsOnline] = useState<boolean>(() => getOnline())

  useEffect(() => {
    setIsOnline(getOnline())
    return subscribe(setIsOnline)
  }, [])

  return { isOnline }
}
