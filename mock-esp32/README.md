# Mock ESP32 Master

Simula al ESP32 Master para desarrollo y testing del modo offline de la PWA.
No reemplaza al firmware real — solo permite probar end-to-end sin un
dispositivo físico.

## Qué hace (Fase 1)

- Polea `GET /api/device/sync/config` cada N segundos, guarda el estado
  in-memory con un hash para no loguear cuando no cambia nada.
- Manda `POST /api/device/sync/heartbeat` cada M segundos.
- (Opcional, off por default) telemetría dummy random vía
  `POST /api/device/sync/telemetry`. **Nota**: el shape que mandamos
  (`luz_ambiente`, `movimiento`, `temperatura`, `estado_luz`) está
  hardcodeado contra el `SensorReading` actual del backend. Si ese
  Pydantic cambia en el backend, prender este flag va a tirar 422
  hasta que actualicemos `sync_loop.telemetry_loop` para matchear.
- Expone endpoints locales sin auth (`/mock/*`) que reenvían comandos al
  backend con `client_timestamp` para probar la lógica LWW del paso 1.2.3.

## Qué NO hace (todavía)

- **MQTT**: el ESP32 real recibe comandos vía AWS IoT Core MQTT. La
  decisión arquitectónica (2026-05-11) deja eso para Fase 4, donde el
  backend principal usa `boto3` para publicar. El mock acá no se suscribe;
  los endpoints `/mock/*` lo sustituyen para testing local.
- **Provisioning Shelly Gen 4 AP**: no se simula. Agregarlo si hace falta
  más adelante.
- **Persistencia**: el estado es 100% in-memory. Reinicio = vuelve a
  pedir `/config` al arrancar.

## Variables de entorno

Ver `.env.example`. La única **requerida** es `MOCK_CASA_ID`. Si no viene,
el lifespan falla con `ValidationError` al arrancar (fail fast).

### Conseguir un MOCK_CASA_ID

Con docker compose corriendo:

```bash
docker compose exec db psql -U mihogar_admin -d mihogar -c \
  "SELECT id, nombre FROM casas LIMIT 5;"
```

Copiá un UUID y pegalo en `.env` (o exportalo como env var).

## Correr en standalone (sin docker)

```bash
cd mock-esp32
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# editar .env: poner MOCK_CASA_ID y dejar BACKEND_URL=http://localhost:8000
uvicorn app.main:app --reload --port 8080
```

Requiere que el backend principal esté corriendo (en standalone: `localhost:8000`).

## Correr en docker-compose

Setear `MOCK_CASA_ID` en `.env` del raíz del repo (o pasarlo en la línea):

```bash
MOCK_CASA_ID=<uuid> docker compose up mock-esp32
```

## Endpoints de testing (sin auth, solo desarrollo)

### `POST /mock/toggle/{zona_id}`

Toggle simple. Reenvía al backend con `client_timestamp` (si no se pasa,
se usa `now()`).

```bash
curl -X POST http://localhost:8080/mock/toggle/<zona_id> \
  -H "Content-Type: application/json" \
  -d '{"encendida": true}'
```

Respuesta:

```json
{
  "result": {
    "client_id": null,
    "zona_id": "...",
    "status": "applied",
    "server_timestamp": "2026-05-11T..."
  },
  "local_updated": true
}
```

### `POST /mock/state/batch`

Batch crudo. Útil para probar LWW con timestamps mezclados (uno viejo,
uno nuevo, uno con zona inválida):

```bash
curl -X POST http://localhost:8080/mock/state/batch \
  -H "Content-Type: application/json" \
  -d '{
    "updates": [
      {"zona_id": "abc", "encendida": true,  "client_id": "1", "client_timestamp": "2026-05-11T10:00:00+00:00"},
      {"zona_id": "abc", "encendida": false, "client_id": "2", "client_timestamp": "2020-01-01T00:00:00+00:00"},
      {"zona_id": "no-existe", "encendida": true, "client_id": "3"}
    ]
  }'
```

Esperado: `applied`, `stale`, `unknown_zone` respectivamente.

### `GET /mock/state`

Dump completo del estado in-memory del mock.

### `GET /health`

Diagnóstico rápido (casa_id, backend_url, conteos, último sync).

## Arquitectura

```
app/
├── main.py            — FastAPI(lifespan=...) — arranque/shutdown limpio de tasks
├── config.py          — Settings con pydantic-settings (.env + env vars)
├── state.py           — InMemoryState con asyncio.Lock + hash para no-op polls
├── backend_client.py  — httpx.AsyncClient + X-Device-Token + backoff exponencial
├── sync_loop.py       — Background tasks: config_poll, heartbeat, telemetry
└── routes/
    ├── health.py      — GET /health
    └── mock.py        — POST /mock/toggle/{zona_id}, POST /mock/state/batch, GET /mock/state
```
