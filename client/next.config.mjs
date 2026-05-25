import withSerwistInit from "@serwist/next"

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
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://44.195.91.127:8000/api/:path*',
      },
    ]
  },
}

const withSerwist = withSerwistInit({
  swSrc: "app/sw.ts",
  swDest: "public/sw.js",
  disable: process.env.NODE_ENV === "development",
  cacheOnNavigation: true,
})

export default withSerwist(nextConfig)
