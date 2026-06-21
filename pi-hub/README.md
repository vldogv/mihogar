# Pi-hub — Mi Hogar (Fase 6)

Servicio local que corre en la Raspberry Pi. Expone el [contrato HTTP
PWA↔hub](../docs/contrato-api-local-esp32.md) en LAN y traduce a MQTT contra el
ESP32 (ver [topics-mqtt-pi-esp32.md](../docs/topics-mqtt-pi-esp32.md)).

Reemplaza al call a la nube (`Vercel /api → EC2 FastAPI`) cuando la PWA está
en la red local de la casa.

## Qué hace

- Mantiene un cache del último `state` e `info` que publicó el ESP32 retained.
- Mantiene una bandera `esp32_online` actualizada por LWT + offline retained
  (cubre tanto desconexión sucia como graceful).
- Expone los 7 endpoints del contrato HTTP. Los `GET` (health/info/state) se
  responden desde el cache. Los `POST` (toggle/mode/scene) generan un `req_id`,
  publican el comando por MQTT, esperan el ack del ESP32 con timeout
  (`ACK_TIMEOUT_SECONDS`, default 2s) y devuelven el resultado.
- Reconnect con backoff exponencial al broker si la conexión se cae.
- Idempotente sobre ack tardío: si un ack llega después del timeout, se loguea
  y descarta — no hay leak de futures.

## Qué NO hace (todavía)

- **Auth.** v1 confía en la LAN. v2: token compartido por casa.
- **TLS.** v1 broker plano (1883). v2 con CA local si hace falta.
- **Servir la PWA.** En prod, la idea es que la Pi también sirva los assets
  estáticos de la PWA en el mismo origen (elimina mixed content y CORS). Hoy
  el pi-hub solo expone el API; el static-serving es scope posterior.
- **Persistencia.** El cache de state/info es in-memory. Reinicio = se vuelve
  a hidratar desde los retained del broker.

## Variables de entorno

| Var | Default | Descripción |
|---|---|---|
| `CASA_ID` | — (requerida) | UUID de la casa. Mismo valor que el ESP32 usa en sus topics. |
| `MQTT_BROKER_URL` | `mqtt://localhost:1883` | Broker MQTT. En compose: `mqtt://mosquitto:1883`. |
| `DEVICE_ID` | `pi-hub` | Identificador MQTT del hub (`<DEVICE_ID>-<CASA_ID>`). |
| `ACK_TIMEOUT_SECONDS` | `2.0` | Cuánto espera la Pi el ack del ESP32 antes de devolver 504. |
| `HTTP_PORT` | `8081` | Puerto donde escucha el API local. |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Solo dev. En prod, mismo origen. |
| `LOG_LEVEL` | `INFO` | stdlib logging. |

`CASA_ID` es requerida — si no viene, el lifespan falla con `ValidationError` al
arrancar (fail fast).

## Correr en docker-compose

Lo más fácil. Levanta broker + mock + hub:

```bash
docker compose up -d --build mosquitto mock-esp32 pi-hub
```

Health check:

```bash
curl http://localhost:8081/health
# {"status":"ok","casa_id":"b0000001-...","esp32_online":true}
```

## Correr en standalone (sin docker)

Requiere Python 3.12+ y un broker MQTT alcanzable (`brew install mosquitto`).

```bash
cd pi-hub
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export CASA_ID=b0000001-0000-0000-0000-000000000001
export MQTT_BROKER_URL=mqtt://localhost:1883
uvicorn app.main:app --reload --port 8081
```

## Smoke test E2E (4 casos)

Con el stack arriba (`docker compose up -d`):

```bash
SALA=11111111-1111-4111-8111-111111111111
NOW=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
OLD="2020-01-01T00:00:00+00:00"
GHOST=ffffffff-ffff-4fff-8fff-ffffffffffff

# 1) applied
curl -X POST "http://localhost:8081/zones/$SALA/toggle" \
  -H "Content-Type: application/json" \
  -d "{\"encendida\": true, \"client_timestamp\": \"$NOW\"}"

# 2) stale (timestamp anterior al de la zona)
curl -X POST "http://localhost:8081/zones/$SALA/toggle" \
  -H "Content-Type: application/json" \
  -d "{\"encendida\": false, \"client_timestamp\": \"$OLD\"}"

# 3) unknown_zone
curl -X POST "http://localhost:8081/zones/$GHOST/toggle" \
  -H "Content-Type: application/json" \
  -d "{\"encendida\": true, \"client_timestamp\": \"$NOW\"}"

# 4) ack timeout (parar el mock primero)
docker compose stop mock-esp32
curl -X POST "http://localhost:8081/zones/$SALA/toggle" \
  -H "Content-Type: application/json" \
  -d "{\"encendida\": true, \"client_timestamp\": \"$NOW\"}"
# → 504 {"detail":"ack timeout"} en ~ACK_TIMEOUT_SECONDS

docker compose start mock-esp32
```

## Arquitectura

```
app/
├── main.py            — FastAPI(lifespan=...) — arranque y shutdown del cliente MQTT
├── config.py          — Settings con pydantic-settings
├── state.py           — LastKnownState (cache de state/info/esp32_online)
├── mqtt_client.py     — aiomqtt + correlation-id dict + futures con timeout
└── routes/
    ├── health.py      — GET /health, GET /info
    ├── state.py       — GET /state
    ├── zones.py       — POST /zones/{id}/toggle, POST /zones/{id}/mode
    └── scenes.py      — POST /scene/all-on, POST /scene/all-off
```

### Flujo de un comando

1. PWA → `POST /zones/<id>/toggle` (HTTP, JSON).
2. Pi-hub genera `req_id = uuid4()`, registra `_pending[req_id] = Future`.
3. Publica `mihogar/<casa>/cmd/zones/<id>/toggle` con `req_id` en el body, QoS 1.
4. Espera el future con `asyncio.wait_for(timeout=ACK_TIMEOUT_SECONDS)`.
5. ESP32 (o mock) recibe, aplica al hardware, publica
   `mihogar/<casa>/ack/<req_id>` con `status` y `server_timestamp`.
6. El listener MQTT del hub hace `pop(req_id)` del dict, resuelve el future.
7. La Pi devuelve la respuesta HTTP a la PWA.
8. Timeout: si el future no se resuelve, `AckTimeout` → HTTP 504. El `finally`
   limpia el `req_id` del dict. Si el ack llega después, el handler ve un
   `req_id` desconocido, loguea y lo descarta.
