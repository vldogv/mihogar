# Mi Hogar — Backend FastAPI (Arquitectura Hexagonal)

## Levantar el proyecto

```bash
# 1. Descomprimir
tar -xzf smart-home-backend.tar.gz
cd smart-home

# 2. Levantar con Docker Compose
docker compose up --build

# 3. Listo!
# API:  http://localhost:8000
# Docs: http://localhost:8000/docs
# DB:   localhost:5432 (mihogar_admin / mihogar_local_2026)
```

## Credenciales de prueba

| Usuario          | Contraseña | Rol            |
|------------------|-----------|----------------|
| admin@mihogar.com | admin123  | Owner (Admin)  |
| maria@mihogar.com | maria123  | Encargado      |
| Carlos Jr.        | PIN: 1234 | Usuario        |

## Flujo de autenticación

```
1. POST /api/auth/login {email, password}
   → Si es owner: devuelve token + lista de casas
   → Si es usuario: devuelve token + casa_id

2. POST /api/auth/select-casa {casa_id}  (solo owners)
   → Token con casa_id incluido

3. POST /api/auth/pin {casa_id, pin}  (usuarios con PIN)
   → Token directo
```

## Endpoints principales

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/api/auth/login` | POST | Login email/password |
| `/api/auth/pin` | POST | Login con PIN |
| `/api/auth/select-casa` | POST | Owner selecciona casa |
| `/api/casas/{id}/panel` | GET | Panel de control |
| `/api/casas/{id}/zonas` | GET | Lista de zonas |
| `/api/zonas/{id}/toggle` | PUT | Encender/apagar zona |
| `/api/zonas/{id}/modo` | PUT | Cambiar modo (auto/manual/timer) |
| `/api/zonas/{id}/config` | PUT | Config sensores |
| `/api/casas/{id}/encender-todo` | POST | Encender todas |
| `/api/casas/{id}/apagar-todo` | POST | Apagar todas |
| `/api/casas/{id}/temporizadores` | GET/POST | CRUD temporizadores |
| `/api/casas/{id}/modo-nocturno` | GET/PUT | Modo nocturno |
| `/api/casas/{id}/consumo/resumen` | GET | Resumen consumo |
| `/api/casas/{id}/consumo/diario` | GET | Consumo diario |
| `/api/casas/{id}/consumo/horas-pico` | GET | Heatmap horas pico |
| `/api/casas/{id}/consumo/bimestral` | GET | Comparativa bimestral |
| `/api/casas/{id}/alertas` | GET | Alertas del sistema |
| `/api/casas/{id}/dispositivos` | GET/POST | CRUD dispositivos |
| `/api/casas/{id}/usuarios` | GET/POST | CRUD usuarios |
| `/api/casas/{id}/wifi-config` | POST | Config WiFi ESP32 |

## Arquitectura hexagonal

```
domain/          → Entidades, value objects, interfaces de repos, reglas de negocio
                   NO depende de NADA externo

application/     → Casos de uso (pendiente: orchestration layer)
                   Depende solo del dominio

infrastructure/  → SQLAlchemy models, implementación de repos, adaptadores AWS
                   Implementa las interfaces del dominio

interfaces/      → Rutas FastAPI, DTOs Pydantic
                   Punto de entrada HTTP

core/            → Config, security, database, dependency injection
                   Cableado técnico
```

## Conectar con tu frontend Next.js

En tu frontend, apunta las peticiones a `http://localhost:8000/api/`.
El CORS ya está configurado para `localhost:3000` y `localhost:5173`.

## Próximos pasos

- [ ] Conectar DynamoDB local (LocalStack o DynamoDB Local)
- [ ] Implementar WebSocket para estado en tiempo real
- [ ] Integrar AWS IoT Core adapter
- [ ] Implementar application/use_cases/ con lógica de orchestration
- [ ] Agregar tests unitarios (pytest-asyncio)
- [ ] Configurar Alembic para migraciones
