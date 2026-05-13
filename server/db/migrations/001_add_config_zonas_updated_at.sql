-- Migration 001 — Garantiza columna updated_at en config_zonas (idempotente)
--
-- Contexto: la columna ya está en server/db/init.sql desde el bootstrap,
-- pero este script existe para garantizar que entornos creados antes de
-- esa línea (potencialmente RDS prod) la tengan también.
--
-- Requerida por: lógica de Last-Writer-Wins en POST /api/device/sync/state
-- (resolución de conflictos por timestamp para modo offline).
--
-- Aplicación manual:
--   psql "$DATABASE_URL" -f 001_add_config_zonas_updated_at.sql
--
-- Idempotente: seguro de correr múltiples veces.

ALTER TABLE config_zonas
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

-- Backfill: si la columna ya existía pero algún row tiene NULL por alguna
-- razón histórica, lo asentamos. NOT NULL ya lo previene en filas nuevas.
UPDATE config_zonas
SET updated_at = NOW()
WHERE updated_at IS NULL;
