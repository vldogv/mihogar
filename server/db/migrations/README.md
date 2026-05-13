# Migraciones SQL

Esquema gestionado con SQL crudo (no Alembic — ver `requirements.txt`,
`alembic` está instalado pero sin configurar). Migrar a Alembic queda
como tarea futura.

## Convenciones

- **Orden secuencial** con prefijo numérico `NNN_descripcion.sql`
  (`001_`, `002_`, ...). No reutilizar números.
- **Idempotentes**: usar `IF NOT EXISTS`, `IF EXISTS`, `DO $$ ... EXCEPTION`.
  Cada script debe ser seguro de correr múltiples veces.
- **Sin rollback automático**: si necesitás revertir, agregá `00N_revert_*.sql`.
- **Encabezado obligatorio**: cada script empieza con un comentario
  explicando contexto, qué feature lo requiere y cómo aplicarlo.

## Aplicación manual

Los scripts no se aplican automáticamente. Se corren contra la DB de prod
con `psql` cuando corresponda:

```bash
psql "$DATABASE_URL" -f 001_add_config_zonas_updated_at.sql
```

`init.sql` y `seed.sql` (carpeta padre) se ejecutan solo al inicializar
un contenedor Postgres nuevo vía `docker-entrypoint-initdb.d`. Para una
DB existente, las migraciones de esta carpeta son la vía.

## Verificación post-aplicación

Tras correr una migración, verificar el esquema:

```bash
psql "$DATABASE_URL" -c "\d <tabla>"
```

## Lista de migraciones

| #   | Archivo                                  | Fecha       | Descripción                                              |
| --- | ---------------------------------------- | ----------- | -------------------------------------------------------- |
| 001 | `001_add_config_zonas_updated_at.sql`    | 2026-05-11  | Garantiza `config_zonas.updated_at` para LWW offline.    |
