import type { PrecacheEntry, SerwistGlobalConfig } from "serwist"
import {
  CacheFirst,
  ExpirationPlugin,
  NetworkFirst,
  NetworkOnly,
  Serwist,
} from "serwist"

declare global {
  interface WorkerGlobalScope extends SerwistGlobalConfig {
    __SW_MANIFEST: (PrecacheEntry | string)[] | undefined
  }
}

declare const self: ServiceWorkerGlobalScope

const serwist = new Serwist({
  precacheEntries: self.__SW_MANIFEST,
  skipWaiting: true,
  clientsClaim: true,
  navigationPreload: true,
  runtimeCaching: [
    // /api/*: NUNCA cachear. Los datos viven en IndexedDB (Fase 2).
    {
      matcher: ({ url }) => url.pathname.startsWith("/api/"),
      handler: new NetworkOnly(),
    },
    // _next/static/*: inmutable, hash en filename.
    {
      matcher: ({ url }) => url.pathname.startsWith("/_next/static/"),
      handler: new CacheFirst({ cacheName: "next-static" }),
    },
    // Imágenes locales (icons, placeholders).
    {
      matcher: ({ request, url }) =>
        request.destination === "image" && url.origin === self.location.origin,
      handler: new CacheFirst({
        cacheName: "images",
        plugins: [
          new ExpirationPlugin({
            maxEntries: 64,
            maxAgeSeconds: 60 * 60 * 24 * 30,
          }),
        ],
      }),
    },
    // Navegación HTML: NetworkFirst con timeout corto + fallback a shell.
    {
      matcher: ({ request }) => request.mode === "navigate",
      handler: new NetworkFirst({
        cacheName: "pages",
        networkTimeoutSeconds: 3,
      }),
    },
  ],
  fallbacks: {
    entries: [
      {
        url: "/~offline",
        matcher: ({ request }) => request.mode === "navigate",
      },
    ],
  },
})

serwist.addEventListeners()
