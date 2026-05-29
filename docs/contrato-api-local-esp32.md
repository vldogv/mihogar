# Contrato API local PWA ↔ Pi-hub — Mi Hogar (Fase 6)

> **Propósito:** que la PWA, conectada a la WiFi de casa sin internet, pueda controlar el hogar contra un **hub local que corre en una Raspberry Pi**. La Pi sirve la PWA y expone esta API en LAN; internamente le habla al ESP32 (que controla el hardware) por MQTT. Reemplaza al call a la nube (`Vercel /api → EC2 FastAPI`) cuando el hub local es alcanzable.
>
> **Cambio respecto a versiones previas:** este contrato originalmente describía el API HTTP que iba a exponer el ESP32. La arquitectura de Fase 6 mete una Raspberry Pi en el medio (resuelve mixed-content sirviendo la PWA local, mismo origen). Los 7 endpoints son los mismos — sólo cambia quién los expone: ahora la Pi. El firmware del ESP32 deja de necesitar un servidor HTTP; habla MQTT con la Pi. Ver [topics-mqtt-pi-esp32.md](topics-mqtt-pi-esp32.md) (BORRADOR).
>
> **Estado del mock:** la implementación de referencia del ESP32 vive en [`mock-esp32/`](../mock-esp32/). El mock simula al ESP32 — no a la Pi. Para Fase 6 se le agrega un cliente MQTT que se suscribe a comandos del hub y publica state/acks. Las rutas HTTP `/mock/*` del mock se mantienen (las usa el smoke test de Fase 1) pero ya no son parte de este contrato.

---

## Convenciones

- **Transporte:** HTTP/1.1 entre PWA y Pi sobre LAN. Sin TLS en v1 (LAN doméstica, sin CA local). El plan es que la Pi también **sirva la PWA** en el mismo origen — eso elimina mixed content y CORS deja de ser un tema en prod. En dev (PWA en `localhost:3000` apuntando a la Pi en otro origen) la Pi habilita CORS abierto.
- **Auth:** sin auth en LAN para v1. A revisar para v2: token compartido por casa.
- **Content-Type:** `application/json` en request y response.
- **IDs:** strings UUID v4 (los mismos que viven en RDS — la PWA ya los tiene cacheados del snapshot de Fase 2).
- **Timestamps:** ISO 8601 con timezone (`2026-05-24T12:34:56+00:00`).
- **Errores:** `{"detail": "<mensaje>"}` con HTTP status apropiado (FastAPI default).
- **Latencia esperada:** los `POST` traducen a un publish MQTT + espera de ack del ESP32. El Pi-hub aplica un timeout corto (default 2s, ver implementación). Si el ack no llega: `504 Gateway Timeout` con `{"detail": "ack timeout"}`.

---

## 1) Endpoints del API local (los expone la Pi)

### `GET /health` — liveness check

Mínimo. Solo confirma que hay un Pi-hub de Mi Hogar de esta casa atendiendo. No requiere que el ESP32 esté vivo — la Pi responde con su `casa_id` configurado.

**Request:** sin body.

**Response 200:**
```json
{
  "status": "ok",
  "casa_id": "8b3e7d91-...-..."
}
```

---

### `GET /info` — discovery rico

Lo que la PWA usa para decidir si confía en este hub y qué features negociar. El `device_id`, `firmware_version` y `capabilities` provienen del último mensaje retained que el ESP32 publicó en MQTT al arrancar; la Pi cachea esa data y la devuelve acá.

**Request:** sin body.

**Response 200:**
```json
{
  "device_id": "esp32-master-aa-bb-cc",
  "casa_id": "8b3e7d91-...-...",
  "firmware_version": "1.0.0",
  "capabilities": ["zones.toggle", "zones.mode", "scene.all-on", "scene.all-off"]
}
```

`capabilities` es una lista de strings que permite que un firmware viejo no rompa una PWA nueva: si una capability no está, la PWA degrada (deshabilita el botón correspondiente) en vez de fallar.

---

### `GET /state` — estado actual de la casa

Equivalente a lo que la PWA hoy lee del **snapshot** (`GET /api/casas/{casa_id}/snapshot`). En modo local sin internet, este es el reemplazo: "dame el estado actual de la casa según vos, hub". La Pi devuelve el último state que publicó el ESP32 por MQTT (retained); no hace polling al ESP32 — el cache se actualiza por push.

**Si la Pi todavía no recibió un mensaje de state** (recién arrancó y el ESP32 aún no publicó): `503 Service Unavailable` con `{"detail": "Hub aún no recibió state del ESP32"}`.

**Shape: FLAT.** Las zonas vienen como un objeto plano (no anidado en `{zona, config}`). La PWA adapta a su tipo `SnapshotZona` internamente.

**Request:** sin body.

**Response 200:**
```json
{
  "casa_id": "8b3e7d91-...",
  "casa_nombre": "Casa Aldo",
  "server_timestamp": "2026-05-24T12:34:56+00:00",
  "zonas": [
    {
      "zona_id": "uuid",
      "nombre": "Sala",
      "tipo": "sala",
      "orden": 1,
      "encendida": true,
      "modo": "automatico",
      "umbral_oscuridad": 40,
      "auto_encender": true,
      "tiempo_apagado_auto": 60
    }
  ],
  "dispositivos": [
    {
      "id": "uuid",
      "zona_id": "uuid",
      "tipo": "shelly",
      "nombre": "Lámpara sala",
      "mac_address": "AA:BB:CC:DD:EE:FF"
    }
  ]
}
```

> **Lo que NO va en `/state`:** temporizadores, modo nocturno, usuarios, consumo, reportes. Son cloud-only por diseño (viven en RDS, requieren queries/agregaciones/permisos). En modo local la PWA degrada a lectura del snapshot cacheado para esa data y bloquea escritura (patrón Fase 3 ya implementado).

---

### `POST /zones/{zona_id}/toggle` — encender/apagar una zona

**Request:**
```json
{
  "encendida": true,
  "client_id": "uuid-opcional",
  "client_timestamp": "2026-05-24T12:34:56+00:00"
}
```
`client_id` y `client_timestamp` son opcionales. Si `client_timestamp` no viene, la Pi lo completa con su reloj antes de enviar el comando al ESP32 por MQTT.

**Response 200:**
```json
{
  "client_id": "uuid-opcional",
  "zona_id": "uuid",
  "status": "applied",
  "server_timestamp": "2026-05-24T12:34:57+00:00"
}
```

**Response 404:** `{"detail": "Zona <id> no existe en este hub"}` (cuando la Pi puede determinarlo del cache local; si no, lo dictamina el ESP32 vía ack con `status: "unknown_zone"`).

**Response 504:** `{"detail": "ack timeout"}` si el ESP32 no responde dentro del timeout.

`status` puede ser:
- `"applied"`: el cambio se aplicó al hardware.
- `"stale"`: `client_timestamp` es anterior al estado guardado → se descartó (LWW).
- `"unknown_zone"`: la zona no existe en esta casa.

**Comportamiento del flujo:**
1. La PWA hace `POST` al hub (Pi).
2. La Pi genera un `req_id`, publica el comando en MQTT y espera el ack del ESP32 (timeout configurable, default 2s).
3. El ESP32 aplica el cambio al hardware local (GPIO / Shelly / relé) y publica el ack con `status` + `server_timestamp` de su RTC.
4. La Pi traduce el ack a la respuesta HTTP. El detalle del topic tree y los payloads MQTT vive en [topics-mqtt-pi-esp32.md](topics-mqtt-pi-esp32.md).
5. La sincronización con el backend nube (cuando hay internet) es responsabilidad del ESP32, fuera del scope de este contrato.

---

### `POST /zones/{zona_id}/mode` — cambio de modo

Mismo patrón que `/toggle` para el modo (auto / manual / etc.).

**Request:**
```json
{
  "modo": "automatico",
  "client_id": "uuid-opcional",
  "client_timestamp": "2026-05-24T12:34:56+00:00"
}
```

`modo` ∈ `{"automatico", "manual", "temporizador"}` (espejo del enum `ModoZona` en el backend hoy — `server/app/domain/entities/models.py:27`).

**Response 200:**
```json
{
  "client_id": "uuid-opcional",
  "zona_id": "uuid",
  "status": "applied",
  "server_timestamp": "2026-05-24T12:34:57+00:00"
}
```

**Response 404:** `{"detail": "Zona <id> no existe en este hub"}` (idem comentario en `/toggle`).

**Response 504:** `{"detail": "ack timeout"}`.

`status` mismas tres opciones que en `/toggle`: `applied | stale | unknown_zone`.

---

### `POST /scene/all-on` — encender todo

Atómico en el ESP32 (sin paralelizar N requests desde la PWA — un ESP32 con conexiones concurrentes es frágil).

**Request:**
```json
{
  "client_id": "uuid-opcional",
  "client_timestamp": "2026-05-24T12:34:56+00:00"
}
```

**Response 200:**
```json
{
  "client_id": "uuid-opcional",
  "status": "applied",
  "server_timestamp": "2026-05-24T12:34:57+00:00",
  "zonas_afectadas": ["uuid1", "uuid2", "uuid3"]
}
```

---

### `POST /scene/all-off` — apagar todo

Mismo shape que `/scene/all-on`.

**Request:**
```json
{
  "client_id": "uuid-opcional",
  "client_timestamp": "2026-05-24T12:34:56+00:00"
}
```

**Response 200:**
```json
{
  "client_id": "uuid-opcional",
  "status": "applied",
  "server_timestamp": "2026-05-24T12:34:57+00:00",
  "zonas_afectadas": ["uuid1", "uuid2", "uuid3"]
}
```

---

## 2) Arquitectura interna del hub y rol del mock

```
┌──────────┐  HTTP/JSON  ┌──────────────┐  MQTT  ┌──────────┐
│   PWA    │ ──────────▶ │   Pi-hub     │ ◀────▶ │  ESP32   │
│ (browser)│ ◀────────── │ (FastAPI +   │        │ (firmware│
└──────────┘             │  Mosquitto)  │        │  o mock) │
                         └──────────────┘        └──────────┘
```

- La **Pi-hub** implementa este contrato (FastAPI). Mantiene un cache del último state recibido por MQTT, traduce cada `POST` de la PWA a un publish + espera de ack.
- El **ESP32** se suscribe a los topics de comando, aplica al hardware, publica state retained y acks. El protocolo MQTT entre Pi y ESP32 está especificado en [topics-mqtt-pi-esp32.md](topics-mqtt-pi-esp32.md) (BORRADOR).
- El **mock ESP32** en [`mock-esp32/`](../mock-esp32/) cumple el rol del ESP32 a efectos de testing E2E: se conecta al mismo broker MQTT, atiende los topics de comando, mantiene un `InMemoryState` y publica state/acks. Las rutas HTTP `/mock/*` viejas se mantienen para no romper los smoke tests de Fase 1, pero no son parte de Fase 6.

---

## 3) Resumen para Miguel (TL;DR)

El firmware del ESP32 **ya no expone HTTP**. Lo que tiene que hacer en LAN es conectarse al broker MQTT que corre en la Pi, suscribirse a los topics de comando y publicar state + acks. El detalle de topics, payloads y semántica de retained vive en [topics-mqtt-pi-esp32.md](topics-mqtt-pi-esp32.md) — ése es el contrato de referencia para el firmware.

Resumen del flujo:

| Operación | Lo que hace el ESP32 |
|---|---|
| Arranque | Publica `state` y `info` con flag retained=true |
| Comando recibido (`cmd/zones/<id>/toggle`, etc.) | Aplica al hardware, publica ack en `cmd/<req_id>/ack` con `status` ∈ `{applied, stale, unknown_zone}` y `server_timestamp` |
| Cambio de estado | Publica el nuevo `state` (retained) |

JSON only, sin auth en v1 (red LAN). Todos los comandos llevan `req_id` (para correlacionar ack) y opcionalmente `client_id` + `client_timestamp` (para LWW).
