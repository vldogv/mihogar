# Spec MQTT Pi-hub ↔ ESP32 — Mi Hogar (Fase 6)

> **Estado:** validado por el smoke test E2E (Pi-hub + mock-esp32 sobre Mosquitto local) — los 4 casos pasan: `applied`, `stale`, `unknown_zone`, `ack timeout`. Plus ack tardío (descartado limpio) y online/offline (LWT + offline retained).
>
> **Extensión 21/jun/2026:** se agregan los topics `telemetry` y `alerts` (sección 3, payloads) y su consumo en `pi-hub` (encolado en `telemetry_queue`/`alerts_queue`, drenado hacia EC2). Definidos y con código escrito, **pendientes de validar contra el ESP32-C5 físico real** — el firmware lo publica, pero no se ha confirmado end-to-end en hardware todavía.
>
> **Scope:** solo el link **Pi ↔ ESP32** sobre un broker MQTT local (Mosquitto) que corre en la Pi. La sincronización del ESP32 con la nube está fuera del scope de este doc.

---

## 1) Convenciones

- **Broker:** Mosquitto corriendo en la Pi. Puerto 1883 sin TLS en v1 (red LAN doméstica). El ESP32 se conecta como cliente MQTT con `client_id= "esp32-<casa_id>"`.
- **Auth:** anonymous en v1. A revisar para v2: username/password o ACL por casa.
- **QoS:** 1 (at-least-once) en todos los publishes. La Pi y el ESP32 deben ser idempotentes sobre `req_id` (no aplicar dos veces el mismo comando si llega duplicado).
- **Retained:** los topics de estado (`state`, `info`) se publican con `retained=true`. Los comandos, acks, telemetría y alertas NO son retained (son efímeros/streaming).
- **Payloads:** JSON UTF-8.
- **IDs:** UUID v4 strings (mismos que viven en RDS, los que la PWA ya cacheó en su snapshot).
- **Timestamps:** ISO 8601 con timezone (`2026-05-24T12:34:56+00:00`). El `server_timestamp` lo pone el ESP32 con su RTC.
- **Last Will & Testament (LWT):** el ESP32 configura LWT en `mihogar/<casa_id>/status` con payload `{"online": false}` (retained). Al conectar, publica `{"online": true}`. Esto le permite a la Pi (y a la PWA, vía `/info`) detectar si el ESP32 se cayó sin desconexión limpia.

---

## 2) Topic tree

Todos los topics están scopeados por `casa_id` para que en el futuro varias casas puedan compartir broker sin colisión.
**Suscripciones:**

- Pi se suscribe a: `mihogar/<casa_id>/info`, `mihogar/<casa_id>/state`, `mihogar/<casa_id>/status`, `mihogar/<casa_id>/telemetry`, `mihogar/<casa_id>/alerts`, `mihogar/<casa_id>/ack/+`.
- ESP32 se suscribe a: `mihogar/<casa_id>/cmd/#` (un solo filter que cubre todos los comandos).

---

## 3) Payloads — publicaciones del ESP32

### `mihogar/<casa_id>/info` (retained)

Publicado una vez al conectar. Se reemplaza si cambia algo (firmware update).

```json
{
  "device_id": "esp32-master-aa-bb-cc",
  "casa_id": "8b3e7d91-...-...",
  "firmware_version": "1.0.0",
  "capabilities": ["zones.toggle", "zones.mode", "scene.all-on", "scene.all-off"]
}
```

### `mihogar/<casa_id>/state` (retained)

Publicado al conectar (con el estado actual conocido) y cada vez que cambia. **Shape idéntico** al body de `GET /state` del [contrato HTTP](contrato-api-local-esp32.md) — la Pi devuelve este payload casi tal cual.

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

### `mihogar/<casa_id>/status` (retained, LWT + graceful)

```json
{"online": true}
```

Publicado retained al **conectar** (después de CONNECT exitoso).

Para que el hub vea `esp32_online=false` correctamente en cualquier tipo de
caída, el ESP32 cubre **dos escenarios**:

1. **Desconexión sucia** (cable arrancado, kernel panic, watchdog reset, pérdida
   de WiFi, keepalive timeout): el ESP32 configura LWT en el packet de CONNECT
   con `topic=mihogar/<casa_id>/status`, `payload={"online": false}`, `qos=1`,
   `retain=true`. El broker dispara el LWT automáticamente cuando detecta la
   desconexión.
2. **Shutdown graceful** (reboot ordenado, OTA, comando de stop): el firmware
   debe **publicar manualmente** `{"online": false}` retained antes de cerrar
   la sesión MQTT. Razón: el spec MQTT dice que el broker NO dispara el LWT
   cuando el cliente envía un DISCONNECT limpio — pierdes la señal si confiás
   solo en el LWT. Es un best-effort: si falla el publish, no abortar el
   shutdown, solo loguear.

Implementación de referencia en el mock: ver `mock-esp32/app/mqtt_loop.py`,
`_publish_info_and_state` (publica `online: true` al conectar) y el bloque
`except asyncio.CancelledError` (publica `online: false` retained en el
shutdown del lifespan).

### `mihogar/<casa_id>/telemetry` (NO retained)

Publicado periódicamente por el ESP32 (intervalo sugerido: 60s — el mismo
orden de magnitud que `TELEMETRY_SECONDS` del mock). **Shape idéntico** al
body de `POST /api/device/sync/telemetry` del backend
(`TelemetryBatch`/`SensorReading` en `device_sync_routes.py`) — el Pi-hub
encola y reenvía el payload casi tal cual, sin transformarlo.

```json
{
  "lecturas": [
    {
      "zona_id": "uuid",
      "timestamp": "2026-06-21T20:00:00+00:00",
      "luz_ambiente": 35,
      "movimiento": true,
      "temperatura": 24.5,
      "consumo_watts": 12.3,
      "estado_luz": "encendida"
    }
  ]
}
```

Todos los campos de cada lectura son opcionales excepto `zona_id` y
`timestamp` — el ESP32 manda lo que tenga disponible según los sensores
físicamente conectados a esa zona (no todas las zonas tienen PIR, no todos
los Shelly reportan consumo, etc.).

### `mihogar/<casa_id>/alerts` (NO retained)

Publicado por el ESP32 cuando detecta una condición anómala localmente
(sensor sin respuesta, error de comunicación con un dispositivo, etc.).
**Shape idéntico** a `AlertsBatch`/`DeviceAlert` del backend.

```json
{
  "alertas": [
    {
      "tipo": "sensor_offline",
      "zona_id": "uuid",
      "dispositivo_mac": "AA:BB:CC:DD:EE:FF",
      "titulo": "Sensor sin respuesta",
      "mensaje": "El módulo Shelly de Sala no responde desde hace 5 minutos",
      "severidad": "warning"
    }
  ]
}
```

`severidad` ∈ `{"info", "warning", "error", "success"}` (mismos valores que
el backend). `zona_id` y `dispositivo_mac` son opcionales — depende de si
la alerta se puede atribuir a una zona/dispositivo específico.

### `mihogar/<casa_id>/ack/<req_id>`

Publicado por el ESP32 en respuesta a cada comando. NO retained (efímero).

Para comandos sobre una sola zona (`toggle`, `mode`):
```json
{
  "req_id": "uuid",
  "client_id": "uuid-opcional",
  "zona_id": "uuid",
  "status": "applied",
  "server_timestamp": "2026-05-24T12:34:57+00:00"
}
```

Para comandos de escena (`scene/all-on`, `scene/all-off`):
```json
{
  "req_id": "uuid",
  "client_id": "uuid-opcional",
  "status": "applied",
  "server_timestamp": "2026-05-24T12:34:57+00:00",
  "zonas_afectadas": ["uuid1", "uuid2", "uuid3"]
}
```

`status` ∈ `{"applied", "stale", "unknown_zone"}`. Mismo significado que en el contrato HTTP.

---

## 4) Payloads — publicaciones de la Pi (comandos)

### `mihogar/<casa_id>/cmd/zones/<zona_id>/toggle`

```json
{
  "req_id": "uuid-generado-por-pi",
  "encendida": true,
  "client_id": "uuid-opcional",
  "client_timestamp": "2026-05-24T12:34:56+00:00"
}
```

`req_id` es obligatorio (lo genera la Pi para correlacionar el ack). `client_id` y `client_timestamp` son opcionales — vienen de la PWA si los mandó; si no, la Pi pone `client_timestamp = now()` antes de publicar.

### `mihogar/<casa_id>/cmd/zones/<zona_id>/mode`

```json
{
  "req_id": "uuid-generado-por-pi",
  "modo": "automatico",
  "client_id": "uuid-opcional",
  "client_timestamp": "2026-05-24T12:34:56+00:00"
}
```

`modo` ∈ `{"automatico", "manual", "temporizador"}`.

### `mihogar/<casa_id>/cmd/scene/all-on` y `.../scene/all-off`

```json
{
  "req_id": "uuid-generado-por-pi",
  "client_id": "uuid-opcional",
  "client_timestamp": "2026-05-24T12:34:56+00:00"
}
```

---

## 5) Patrón request-response (MQTT RPC)

1. PWA hace `POST /zones/<id>/toggle` a la Pi.
2. La Pi genera `req_id = uuid4()`, registra un `asyncio.Future` en un dict `pending[req_id]`.
3. La Pi publica el comando en el topic correspondiente con QoS 1.
4. La Pi espera el future con `asyncio.wait_for(timeout=ACK_TIMEOUT_SECONDS)`. Default: **2 segundos**.
5. Cuando llega un mensaje en `mihogar/<casa_id>/ack/<req_id>`, el handler MQTT resuelve el future con el payload.
6. La Pi devuelve el ack como respuesta HTTP a la PWA.
7. Si el timeout vence sin ack: la Pi devuelve `504 Gateway Timeout` con `{"detail": "ack timeout"}` y limpia el entry del dict.

**Idempotencia:** si el ESP32 recibe el mismo `req_id` dos veces (QoS 1 puede duplicar), debe responder el mismo ack y NO aplicar dos veces. Mantener un cache pequeño de últimos N `req_id` procesados es la forma estándar.

**Ack tardío:** si el ESP32 publica un ack después de que la Pi ya hizo timeout (devolvió 504 al cliente HTTP), el listener MQTT de la Pi ve un`req_id` que ya no está en su tabla pendiente, loguea y lo descarta. No hay leak. El ESP32 NO necesita lógica especial para esto — siempre publica el ack cuando termina de aplicar.

---

## 6) Casos de error y semántica

| Caso | Quién lo detecta | Respuesta MQTT | Respuesta HTTP de la Pi |
|---|---|---|---|
| Comando válido aplicado | ESP32 | ack con `status: "applied"` | 200 con `status: "applied"` |
| Timestamp viejo (LWW pierde) | ESP32 | ack con `status: "stale"` | 200 con `status: "stale"` |
| Zona inexistente | ESP32 (cache fresca) o Pi (cache cargado) | ack con `status: "unknown_zone"` | 200 con `status: "unknown_zone"` o 404 si la Pi lo cazó local |
| ESP32 desconectado / no responde | Pi (timeout) | — | 504 `{"detail": "ack timeout"}` |
| JSON inválido en el comando | ESP32 | (no responde) → timeout | 504 (mismo path) |
| Broker caído | Pi (al publicar) | — | 503 `{"detail": "MQTT broker no disponible"}` |
| Telemetría/alerta con JSON inválido | Pi (al encolar) | (se descarta, sin reintentar al ESP32 — es streaming, no RPC) | n/a |

---

## 7) Pendientes para v2

- [ ] Confirmar tamaño máximo de payload para `state` con casas grandes (¿N zonas?).
- [ ] Decidir si `info.capabilities` se versiona o crece append-only.
- [ ] Auth (username/password vs. token compartido por casa).
- [ ] TLS sobre 8883 con CA local.
- [ ] Validar `telemetry`/`alerts` end-to-end contra el ESP32-C5 físico real (definido e implementado 21/jun/2026, pendiente de prueba en hardware).
