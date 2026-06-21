import withSerwistInit from "@serwist/next"

// Build target switch:
//   BUILD_TARGET=pi-static  → static export servido desde la Pi por Caddy.
//   (default, sin var)      → build estándar (Vercel / dev / standalone).
// Static export no soporta rewrites(); en la Pi el proxy /api/* lo hace Caddy.
const isPiStatic = process.env.BUILD_TARGET === "pi-static"

/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {
    root: ".",
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  ...(isPiStatic
    ? { output: "export" }
    : {
        async rewrites() {
          return [
            {
              source: '/api/:path*',
              destination: 'http://3.212.121.202:8000/api/:path*',
            },
          ]
        },
      }),
}

const withSerwist = withSerwistInit({
  swSrc: "app/sw.ts",
  swDest: "public/sw.js",
  disable: process.env.NODE_ENV === "development",
  cacheOnNavigation: true,
})

export default withSerwist(nextConfig)
