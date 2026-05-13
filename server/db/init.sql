-- Mi Hogar - Init SQL
-- Se ejecuta al crear el contenedor de PostgreSQL.
-- Crea las extensiones y los tipos ENUM que SQLAlchemy necesita.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enums (SQLAlchemy los referencia con create_type=False)
DO $$ BEGIN
    CREATE TYPE rol_usuario AS ENUM ('administrador', 'encargado', 'usuario');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE metodo_acceso AS ENUM ('email', 'pin');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE modo_zona AS ENUM ('automatico', 'manual', 'temporizador');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE tipo_zona AS ENUM ('habitacion', 'zona_de_paso', 'exterior');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE tipo_dispositivo AS ENUM ('modulo_shelly', 'sensor_pir', 'sensor_crepuscular', 'camara_ip');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE estado_dispositivo AS ENUM ('online', 'offline', 'error', 'actualizando');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE tipo_temporizador AS ENUM ('horario_fijo', 'por_sensor');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE tipo_alerta AS ENUM ('sensor_offline', 'consumo_elevado', 'firmware_actualizado', 'temperatura_elevada', 'dispositivo_error', 'consumo_nocturno_alto', 'umbral_superado');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE severidad_alerta AS ENUM ('info', 'warning', 'error', 'success');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;


-- ══════════════════════════════════════════════════════════════
-- TABLAS
-- ══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS owners (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre          VARCHAR(100)    NOT NULL,
    email           VARCHAR(255)    NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    telefono        VARCHAR(20),
    max_casas       SMALLINT        NOT NULL DEFAULT 3,
    activo          BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS casas (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id        UUID            NOT NULL REFERENCES owners(id) ON DELETE CASCADE,
    nombre          VARCHAR(100)    NOT NULL,
    direccion       VARCHAR(255),
    zona_horaria    VARCHAR(50)     NOT NULL DEFAULT 'America/Mexico_City',
    wifi_ssid       VARCHAR(100),
    wifi_password_enc VARCHAR(255),
    nombre_instalacion VARCHAR(100),
    email_alertas   VARCHAR(255),
    corte_cfe_dia   SMALLINT        DEFAULT 15,
    activa          BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS usuarios_casa (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    casa_id         UUID            NOT NULL REFERENCES casas(id) ON DELETE CASCADE,
    owner_id        UUID            REFERENCES owners(id),
    nombre          VARCHAR(100)    NOT NULL,
    email           VARCHAR(255),
    password_hash   VARCHAR(255),
    pin_hash        VARCHAR(255),
    rol             rol_usuario     NOT NULL DEFAULT 'usuario',
    metodo_acceso   metodo_acceso   NOT NULL DEFAULT 'email',
    activo          BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_email_por_casa UNIQUE(casa_id, email)
);

CREATE TABLE IF NOT EXISTS zonas (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    casa_id         UUID            NOT NULL REFERENCES casas(id) ON DELETE CASCADE,
    nombre          VARCHAR(100)    NOT NULL,
    tipo            tipo_zona       NOT NULL DEFAULT 'habitacion',
    icono           VARCHAR(50),
    orden           SMALLINT        NOT NULL DEFAULT 0,
    activa          BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_zona_nombre_casa UNIQUE(casa_id, nombre)
);

CREATE TABLE IF NOT EXISTS config_zonas (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zona_id         UUID            NOT NULL REFERENCES zonas(id) ON DELETE CASCADE UNIQUE,
    encendida       BOOLEAN         NOT NULL DEFAULT FALSE,
    modo            modo_zona       NOT NULL DEFAULT 'automatico',
    umbral_oscuridad SMALLINT       NOT NULL DEFAULT 40,
    auto_encender   BOOLEAN         NOT NULL DEFAULT TRUE,
    tiempo_apagado_auto SMALLINT    NOT NULL DEFAULT 60,
    luz_ambiente_actual SMALLINT,
    movimiento_detectado BOOLEAN    DEFAULT FALSE,
    temperatura_actual  NUMERIC(5,2),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS permisos_zona (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id      UUID            NOT NULL REFERENCES usuarios_casa(id) ON DELETE CASCADE,
    zona_id         UUID            NOT NULL REFERENCES zonas(id) ON DELETE CASCADE,
    puede_controlar BOOLEAN         NOT NULL DEFAULT TRUE,
    puede_configurar BOOLEAN        NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_permiso_usuario_zona UNIQUE(usuario_id, zona_id)
);

CREATE TABLE IF NOT EXISTS dispositivos (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zona_id         UUID            NOT NULL REFERENCES zonas(id) ON DELETE CASCADE,
    casa_id         UUID            NOT NULL REFERENCES casas(id) ON DELETE CASCADE,
    tipo            tipo_dispositivo NOT NULL,
    nombre          VARCHAR(100)    NOT NULL,
    mac_address     VARCHAR(17)     UNIQUE,
    ip_local        VARCHAR(45),
    firmware_version VARCHAR(20),
    estado          estado_dispositivo NOT NULL DEFAULT 'offline',
    ultimo_heartbeat TIMESTAMPTZ,
    configuracion   JSONB           DEFAULT '{}',
    activo          BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS temporizadores (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zona_id         UUID            NOT NULL REFERENCES zonas(id) ON DELETE CASCADE,
    casa_id         UUID            NOT NULL REFERENCES casas(id) ON DELETE CASCADE,
    tipo            tipo_temporizador NOT NULL DEFAULT 'horario_fijo',
    hora_inicio     TIME            NOT NULL,
    hora_fin        TIME            NOT NULL,
    lunes           BOOLEAN         NOT NULL DEFAULT TRUE,
    martes          BOOLEAN         NOT NULL DEFAULT TRUE,
    miercoles       BOOLEAN         NOT NULL DEFAULT TRUE,
    jueves          BOOLEAN         NOT NULL DEFAULT TRUE,
    viernes         BOOLEAN         NOT NULL DEFAULT TRUE,
    sabado          BOOLEAN         NOT NULL DEFAULT FALSE,
    domingo         BOOLEAN         NOT NULL DEFAULT FALSE,
    solo_si_oscuro  BOOLEAN         NOT NULL DEFAULT FALSE,
    habilitado      BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS modo_nocturno (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    casa_id         UUID            NOT NULL REFERENCES casas(id) ON DELETE CASCADE UNIQUE,
    habilitado      BOOLEAN         NOT NULL DEFAULT FALSE,
    deteccion_inteligente BOOLEAN   NOT NULL DEFAULT TRUE,
    hora_inicio     TIME            NOT NULL DEFAULT '23:00',
    hora_fin        TIME            NOT NULL DEFAULT '06:00',
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS zonas_nocturnas (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    modo_nocturno_id UUID           NOT NULL REFERENCES modo_nocturno(id) ON DELETE CASCADE,
    zona_id         UUID            NOT NULL REFERENCES zonas(id) ON DELETE CASCADE,
    habilitada      BOOLEAN         NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_zona_nocturna UNIQUE(modo_nocturno_id, zona_id)
);

CREATE TABLE IF NOT EXISTS consumo_diario (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zona_id         UUID            NOT NULL REFERENCES zonas(id) ON DELETE CASCADE,
    casa_id         UUID            NOT NULL REFERENCES casas(id) ON DELETE CASCADE,
    fecha           DATE            NOT NULL,
    kwh_total       NUMERIC(8,4)    NOT NULL DEFAULT 0,
    horas_encendido NUMERIC(6,2)    NOT NULL DEFAULT 0,
    minutos_nocturno NUMERIC(6,2)   NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_consumo_dia_zona UNIQUE(zona_id, fecha)
);

CREATE TABLE IF NOT EXISTS consumo_bimestral (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    casa_id         UUID            NOT NULL REFERENCES casas(id) ON DELETE CASCADE,
    bimestre        SMALLINT        NOT NULL,
    anio            SMALLINT        NOT NULL,
    kwh_total       NUMERIC(10,4)   NOT NULL DEFAULT 0,
    costo_estimado  NUMERIC(10,2)   NOT NULL DEFAULT 0,
    horas_uso_dia   NUMERIC(6,2)    NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_bimestre_casa UNIQUE(casa_id, bimestre, anio)
);

CREATE TABLE IF NOT EXISTS horas_pico (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zona_id         UUID            NOT NULL REFERENCES zonas(id) ON DELETE CASCADE,
    casa_id         UUID            NOT NULL REFERENCES casas(id) ON DELETE CASCADE,
    hora            SMALLINT        NOT NULL,
    dia_semana      SMALLINT        NOT NULL,
    minutos_promedio NUMERIC(6,2)   NOT NULL DEFAULT 0,
    periodo_inicio  DATE            NOT NULL,
    periodo_fin     DATE            NOT NULL,
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_hora_pico UNIQUE(zona_id, hora, dia_semana, periodo_inicio)
);

CREATE TABLE IF NOT EXISTS alertas (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    casa_id         UUID            NOT NULL REFERENCES casas(id) ON DELETE CASCADE,
    zona_id         UUID            REFERENCES zonas(id) ON DELETE SET NULL,
    dispositivo_id  UUID            REFERENCES dispositivos(id) ON DELETE SET NULL,
    tipo            tipo_alerta     NOT NULL,
    severidad       severidad_alerta NOT NULL DEFAULT 'info',
    titulo          VARCHAR(200)    NOT NULL,
    mensaje         TEXT            NOT NULL,
    leida           BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS perfiles_sagemaker (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zona_id         UUID            NOT NULL REFERENCES zonas(id) ON DELETE CASCADE,
    casa_id         UUID            NOT NULL REFERENCES casas(id) ON DELETE CASCADE,
    umbral_oscuridad_sugerido SMALLINT,
    tiempo_apagado_sugerido SMALLINT,
    horas_uso_optimas JSONB,
    patron_detectado VARCHAR(100),
    modelo_version  VARCHAR(50),
    confianza       NUMERIC(5,4),
    datos_entrenamiento_desde DATE,
    datos_entrenamiento_hasta DATE,
    aplicado        BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_casas_owner ON casas(owner_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_casa ON usuarios_casa(casa_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios_casa(email);
CREATE INDEX IF NOT EXISTS idx_zonas_casa ON zonas(casa_id);
CREATE INDEX IF NOT EXISTS idx_config_zona ON config_zonas(zona_id);
CREATE INDEX IF NOT EXISTS idx_dispositivos_zona ON dispositivos(zona_id);
CREATE INDEX IF NOT EXISTS idx_dispositivos_casa ON dispositivos(casa_id);
CREATE INDEX IF NOT EXISTS idx_temporizadores_zona ON temporizadores(zona_id);
CREATE INDEX IF NOT EXISTS idx_temporizadores_casa ON temporizadores(casa_id);
CREATE INDEX IF NOT EXISTS idx_consumo_casa_fecha ON consumo_diario(casa_id, fecha);
CREATE INDEX IF NOT EXISTS idx_alertas_casa ON alertas(casa_id, created_at DESC);
