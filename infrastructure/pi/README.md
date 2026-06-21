# Deploy hub local en Raspberry Pi (Fase 6)

Pi sirve la PWA por HTTPS y proxea: estático + /api (cloud) + endpoints del pi-hub local.

## Build de la PWA (en la Mac, el Pi 3B no aguanta el build)
cd client
BUILD_TARGET=pi-static NEXT_PUBLIC_API_URL=/api pnpm build
rsync -avz --delete out/ aegv17@<PI_IP>:~/mihogar/www/

## Servicios en el Pi (nativo, no Docker)
- mosquitto (apt) en :1883
- mihogar-pi-hub.service  -> :8081 (venv en ~/mihogar/pi-hub/.venv)
- mihogar-mock-esp32.service (venv en ~/mihogar/mock-esp32/.venv)
- caddy (apt) :443 con `tls internal`, Caddyfile en /etc/caddy/

## HTTPS / Service Worker
Requiere CA confiable. Instalar la root CA de Caddy en cada device:
  sudo find /var/lib/caddy -name root.crt   # extraer y confiar en el cliente

## Ruteo Caddy
- /health /info /state /zones/*/toggle /zones/*/mode /scene/*  -> pi-hub :8081
- /api/*  -> backend cloud (EC2)
- resto  -> static export en ~/mihogar/www
