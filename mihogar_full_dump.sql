--
-- PostgreSQL database dump
--

\restrict rbeSh4hs2CF2gjHbPtXetiI1Vprdo2H53zP35fJIbtcbNOdfgv4xzY1gLnVdXiN

-- Dumped from database version 16.13
-- Dumped by pg_dump version 16.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: estado_dispositivo; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.estado_dispositivo AS ENUM (
    'online',
    'offline',
    'error',
    'actualizando'
);


--
-- Name: metodo_acceso; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.metodo_acceso AS ENUM (
    'email',
    'pin'
);


--
-- Name: modo_zona; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.modo_zona AS ENUM (
    'automatico',
    'manual',
    'temporizador'
);


--
-- Name: rol_usuario; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.rol_usuario AS ENUM (
    'administrador',
    'encargado',
    'usuario'
);


--
-- Name: severidad_alerta; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.severidad_alerta AS ENUM (
    'info',
    'warning',
    'error',
    'success'
);


--
-- Name: tipo_alerta; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.tipo_alerta AS ENUM (
    'sensor_offline',
    'consumo_elevado',
    'firmware_actualizado',
    'temperatura_elevada',
    'dispositivo_error',
    'consumo_nocturno_alto',
    'umbral_superado'
);


--
-- Name: tipo_dispositivo; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.tipo_dispositivo AS ENUM (
    'modulo_shelly',
    'sensor_pir',
    'sensor_crepuscular',
    'camara_ip'
);


--
-- Name: tipo_temporizador; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.tipo_temporizador AS ENUM (
    'horario_fijo',
    'por_sensor'
);


--
-- Name: tipo_zona; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.tipo_zona AS ENUM (
    'habitacion',
    'zona_de_paso',
    'exterior'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alertas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alertas (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    casa_id uuid NOT NULL,
    zona_id uuid,
    dispositivo_id uuid,
    tipo public.tipo_alerta NOT NULL,
    severidad public.severidad_alerta DEFAULT 'info'::public.severidad_alerta NOT NULL,
    titulo character varying(200) NOT NULL,
    mensaje text NOT NULL,
    leida boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: casas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.casas (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    owner_id uuid NOT NULL,
    nombre character varying(100) NOT NULL,
    direccion character varying(255),
    zona_horaria character varying(50) DEFAULT 'America/Mexico_City'::character varying NOT NULL,
    wifi_ssid character varying(100),
    wifi_password_enc character varying(255),
    nombre_instalacion character varying(100),
    email_alertas character varying(255),
    corte_cfe_dia smallint DEFAULT 15,
    activa boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: config_zonas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.config_zonas (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    zona_id uuid NOT NULL,
    encendida boolean DEFAULT false NOT NULL,
    modo public.modo_zona DEFAULT 'automatico'::public.modo_zona NOT NULL,
    umbral_oscuridad smallint DEFAULT 40 NOT NULL,
    auto_encender boolean DEFAULT true NOT NULL,
    tiempo_apagado_auto smallint DEFAULT 60 NOT NULL,
    luz_ambiente_actual smallint,
    movimiento_detectado boolean DEFAULT false,
    temperatura_actual numeric(5,2),
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: consumo_bimestral; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.consumo_bimestral (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    casa_id uuid NOT NULL,
    bimestre smallint NOT NULL,
    anio smallint NOT NULL,
    kwh_total numeric(10,4) DEFAULT 0 NOT NULL,
    costo_estimado numeric(10,2) DEFAULT 0 NOT NULL,
    horas_uso_dia numeric(6,2) DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: consumo_diario; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.consumo_diario (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    zona_id uuid NOT NULL,
    casa_id uuid NOT NULL,
    fecha date NOT NULL,
    kwh_total numeric(8,4) DEFAULT 0 NOT NULL,
    horas_encendido numeric(6,2) DEFAULT 0 NOT NULL,
    minutos_nocturno numeric(6,2) DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: dispositivos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dispositivos (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    zona_id uuid NOT NULL,
    casa_id uuid NOT NULL,
    tipo public.tipo_dispositivo NOT NULL,
    nombre character varying(100) NOT NULL,
    mac_address character varying(17),
    ip_local character varying(45),
    firmware_version character varying(20),
    estado public.estado_dispositivo DEFAULT 'offline'::public.estado_dispositivo NOT NULL,
    ultimo_heartbeat timestamp with time zone,
    configuracion jsonb DEFAULT '{}'::jsonb,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: horas_pico; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.horas_pico (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    zona_id uuid NOT NULL,
    casa_id uuid NOT NULL,
    hora smallint NOT NULL,
    dia_semana smallint NOT NULL,
    minutos_promedio numeric(6,2) DEFAULT 0 NOT NULL,
    periodo_inicio date NOT NULL,
    periodo_fin date NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: modo_nocturno; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.modo_nocturno (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    casa_id uuid NOT NULL,
    habilitado boolean DEFAULT false NOT NULL,
    deteccion_inteligente boolean DEFAULT true NOT NULL,
    hora_inicio time without time zone DEFAULT '23:00:00'::time without time zone NOT NULL,
    hora_fin time without time zone DEFAULT '06:00:00'::time without time zone NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: owners; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.owners (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    nombre character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    telefono character varying(20),
    max_casas smallint DEFAULT 3 NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: perfiles_sagemaker; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.perfiles_sagemaker (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    zona_id uuid NOT NULL,
    casa_id uuid NOT NULL,
    umbral_oscuridad_sugerido smallint,
    tiempo_apagado_sugerido smallint,
    horas_uso_optimas jsonb,
    patron_detectado character varying(100),
    modelo_version character varying(50),
    confianza numeric(5,4),
    datos_entrenamiento_desde date,
    datos_entrenamiento_hasta date,
    aplicado boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: permisos_zona; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.permisos_zona (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    usuario_id uuid NOT NULL,
    zona_id uuid NOT NULL,
    puede_controlar boolean DEFAULT true NOT NULL,
    puede_configurar boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: temporizadores; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.temporizadores (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    zona_id uuid NOT NULL,
    casa_id uuid NOT NULL,
    tipo public.tipo_temporizador DEFAULT 'horario_fijo'::public.tipo_temporizador NOT NULL,
    hora_inicio time without time zone NOT NULL,
    hora_fin time without time zone NOT NULL,
    lunes boolean DEFAULT true NOT NULL,
    martes boolean DEFAULT true NOT NULL,
    miercoles boolean DEFAULT true NOT NULL,
    jueves boolean DEFAULT true NOT NULL,
    viernes boolean DEFAULT true NOT NULL,
    sabado boolean DEFAULT false NOT NULL,
    domingo boolean DEFAULT false NOT NULL,
    solo_si_oscuro boolean DEFAULT false NOT NULL,
    habilitado boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: usuarios_casa; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usuarios_casa (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    casa_id uuid NOT NULL,
    owner_id uuid,
    nombre character varying(100) NOT NULL,
    email character varying(255),
    password_hash character varying(255),
    pin_hash character varying(255),
    rol public.rol_usuario DEFAULT 'usuario'::public.rol_usuario NOT NULL,
    metodo_acceso public.metodo_acceso DEFAULT 'email'::public.metodo_acceso NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: zonas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.zonas (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    casa_id uuid NOT NULL,
    nombre character varying(100) NOT NULL,
    tipo public.tipo_zona DEFAULT 'habitacion'::public.tipo_zona NOT NULL,
    icono character varying(50),
    orden smallint DEFAULT 0 NOT NULL,
    activa boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: zonas_nocturnas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.zonas_nocturnas (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    modo_nocturno_id uuid NOT NULL,
    zona_id uuid NOT NULL,
    habilitada boolean DEFAULT true NOT NULL
);


--
-- Data for Name: alertas; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alertas (id, casa_id, zona_id, dispositivo_id, tipo, severidad, titulo, mensaje, leida, created_at) FROM stdin;
5f5fef23-58f1-4b15-b6ba-bbb46fa06327	b0000001-0000-0000-0000-000000000001	d0000001-0000-0000-0000-000000000005	f0000001-0000-0000-0000-000000000007	sensor_offline	warning	Sensor fuera de línea	El sensor de movimiento del pasillo no responde desde hace 2 horas.	f	2026-03-24 02:18:32.872322+00
37f4fed0-3ef1-4197-bc17-067744d11bad	b0000001-0000-0000-0000-000000000001	\N	\N	consumo_nocturno_alto	warning	Consumo nocturno elevado	Se detectó un aumento del 25% en consumo nocturno. Revisa el carnet de instrucciones.	f	2026-03-23 23:18:32.872322+00
340f36dd-c70f-4531-ba2b-bbd728e43332	b0000001-0000-0000-0000-000000000001	d0000001-0000-0000-0000-000000000001	f0000001-0000-0000-0000-000000000001	firmware_actualizado	success	Firmware actualizado	El módulo Shelly de la sala se actualizó correctamente a la versión 1.4.2.	f	2026-03-23 04:18:32.872322+00
5f17021a-8915-4caf-833c-4b7c9475ac43	b0000001-0000-0000-0000-000000000001	d0000001-0000-0000-0000-000000000002	f0000001-0000-0000-0000-000000000004	temperatura_elevada	error	Temperatura elevada	El módulo Shelly de la cocina reporta temperatura de 42°C.	f	2026-03-23 04:18:32.872322+00
\.


--
-- Data for Name: casas; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.casas (id, owner_id, nombre, direccion, zona_horaria, wifi_ssid, wifi_password_enc, nombre_instalacion, email_alertas, corte_cfe_dia, activa, created_at, updated_at) FROM stdin;
b0000001-0000-0000-0000-000000000002	a0000001-0000-0000-0000-000000000001	Casa de Playa	Playa del Carmen, QR	America/Mexico_City	\N	\N	\N	admin@mihogar.com	15	t	2026-03-24 04:18:32.866088+00	2026-03-24 04:18:32.866088+00
b0000001-0000-0000-0000-000000000001	a0000001-0000-0000-0000-000000000001	Casa Principal	Av. Reforma 123, CDMX	America/Mexico_City	\N	\N	\N	admin@mihogar.com	10	t	2026-03-24 04:18:32.866088+00	2026-03-26 02:19:15.958935+00
\.


--
-- Data for Name: config_zonas; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.config_zonas (id, zona_id, encendida, modo, umbral_oscuridad, auto_encender, tiempo_apagado_auto, luz_ambiente_actual, movimiento_detectado, temperatura_actual, updated_at) FROM stdin;
91696938-9e26-40db-a6d3-b5f8e1a54b9e	d0000001-0000-0000-0000-000000000002	t	temporizador	15	t	600	20	t	42.00	2026-03-26 21:00:10.411653+00
c699606b-39d3-4d21-9d6c-400bb11635f2	d0000001-0000-0000-0000-000000000003	t	manual	40	t	60	80	f	26.00	2026-03-26 21:00:10.413972+00
4256e52b-1c15-4932-8547-0e2d66fd03b6	d0000001-0000-0000-0000-000000000004	t	automatico	40	t	60	75	f	25.50	2026-03-26 21:00:10.416977+00
e7f68034-d5f9-4902-939c-da2bb7f64030	d0000001-0000-0000-0000-000000000005	t	automatico	30	t	30	\N	f	\N	2026-03-26 21:00:10.419184+00
0794a01e-78f8-4bfa-9106-a5c47f77937b	d0000001-0000-0000-0000-000000000006	t	automatico	30	t	30	\N	f	\N	2026-03-26 21:00:10.420918+00
e7ed6f3e-c3af-4007-9cfd-af0164a73f7a	d0000001-0000-0000-0000-000000000001	t	manual	40	t	60	35	t	28.50	2026-03-26 21:00:14.575548+00
\.


--
-- Data for Name: consumo_bimestral; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.consumo_bimestral (id, casa_id, bimestre, anio, kwh_total, costo_estimado, horas_uso_dia, created_at, updated_at) FROM stdin;
deeac37d-7a18-4561-85b0-4ea3b1c11ce9	b0000001-0000-0000-0000-000000000001	1	2025	70.0000	260.00	14.50	2026-03-24 04:18:32.871952+00	2026-03-24 04:18:32.871952+00
e557f7ef-b341-46e6-8b86-2f4ee5f6fe4f	b0000001-0000-0000-0000-000000000001	2	2025	75.0000	275.00	15.20	2026-03-24 04:18:32.871952+00	2026-03-24 04:18:32.871952+00
a4fd8964-875b-4c39-a0c0-37668a881098	b0000001-0000-0000-0000-000000000001	3	2025	65.0000	235.00	13.80	2026-03-24 04:18:32.871952+00	2026-03-24 04:18:32.871952+00
61bda11b-58a5-48f5-85c4-6fb14f5bb294	b0000001-0000-0000-0000-000000000001	4	2025	58.0000	210.00	12.50	2026-03-24 04:18:32.871952+00	2026-03-24 04:18:32.871952+00
44cc1191-9094-4738-834c-0470813c2a61	b0000001-0000-0000-0000-000000000001	5	2025	50.0000	180.00	11.80	2026-03-24 04:18:32.871952+00	2026-03-24 04:18:32.871952+00
3d282ac1-5716-41d5-940a-70a4635aca87	b0000001-0000-0000-0000-000000000001	6	2025	42.5000	156.00	12.90	2026-03-24 04:18:32.871952+00	2026-03-24 04:18:32.871952+00
\.


--
-- Data for Name: consumo_diario; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.consumo_diario (id, zona_id, casa_id, fecha, kwh_total, horas_encendido, minutos_nocturno, created_at) FROM stdin;
260913d4-f28c-46ab-bc10-e2dc81e224a8	d0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	2026-03-18	0.3800	4.20	15.00	2026-03-24 04:18:32.870851+00
02c9d13e-aff0-47fb-acef-89328aefd5e5	d0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	2026-03-19	0.3500	3.80	12.00	2026-03-24 04:18:32.870851+00
544394ba-962a-4e19-b58a-0564f1d7eb43	d0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	2026-03-20	0.4000	4.50	18.00	2026-03-24 04:18:32.870851+00
3d7c345d-6942-4a97-a7b2-ba65aa1137b5	d0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	2026-03-21	0.4200	4.60	20.00	2026-03-24 04:18:32.870851+00
41339f95-69e5-4f4c-8a58-c73924bd38a1	d0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	2026-03-22	0.4500	5.00	22.00	2026-03-24 04:18:32.870851+00
539a3e22-98c2-48ef-9bfd-60b1e406cbe7	d0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	2026-03-23	0.4800	5.20	25.00	2026-03-24 04:18:32.870851+00
90ed4e00-83b4-48ca-ab6b-133d83f51253	d0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	2026-03-24	0.4200	4.20	15.00	2026-03-24 04:18:32.870851+00
879a982d-50bf-4562-9b7e-08fe38209230	d0000001-0000-0000-0000-000000000002	b0000001-0000-0000-0000-000000000001	2026-03-18	0.3000	3.50	5.00	2026-03-24 04:18:32.870851+00
66c77a1e-5559-4002-af87-c38b75e38cf0	d0000001-0000-0000-0000-000000000002	b0000001-0000-0000-0000-000000000001	2026-03-19	0.3200	3.60	8.00	2026-03-24 04:18:32.870851+00
7affe008-6a96-4e1c-82a8-e9a0446f6fd0	d0000001-0000-0000-0000-000000000002	b0000001-0000-0000-0000-000000000001	2026-03-20	0.2800	3.20	4.00	2026-03-24 04:18:32.870851+00
18b770ee-7e27-4c6b-936a-78beb315add9	d0000001-0000-0000-0000-000000000002	b0000001-0000-0000-0000-000000000001	2026-03-21	0.3500	3.80	6.00	2026-03-24 04:18:32.870851+00
dedd89d0-37f8-46c7-8dac-0285637a9108	d0000001-0000-0000-0000-000000000002	b0000001-0000-0000-0000-000000000001	2026-03-22	0.3800	4.00	8.00	2026-03-24 04:18:32.870851+00
d9529eab-b2f3-49f4-bf58-03fc9aa99f12	d0000001-0000-0000-0000-000000000002	b0000001-0000-0000-0000-000000000001	2026-03-23	0.4000	4.20	10.00	2026-03-24 04:18:32.870851+00
69883495-7ce4-46cf-b26b-9b4f6456fb04	d0000001-0000-0000-0000-000000000002	b0000001-0000-0000-0000-000000000001	2026-03-24	0.3500	3.50	5.00	2026-03-24 04:18:32.870851+00
421ca52f-697c-4cf8-82f0-0b736bd12f16	d0000001-0000-0000-0000-000000000003	b0000001-0000-0000-0000-000000000001	2026-03-18	0.1500	1.80	80.00	2026-03-24 04:18:32.870851+00
c5090730-40a8-400c-b831-6737ef5c7971	d0000001-0000-0000-0000-000000000003	b0000001-0000-0000-0000-000000000001	2026-03-19	0.1800	2.00	85.00	2026-03-24 04:18:32.870851+00
2b6bc6b0-48cc-4215-9d8d-70e7448fda88	d0000001-0000-0000-0000-000000000003	b0000001-0000-0000-0000-000000000001	2026-03-20	0.1600	1.90	82.00	2026-03-24 04:18:32.870851+00
3473fb2d-bb3e-4e51-a089-c07081637176	d0000001-0000-0000-0000-000000000003	b0000001-0000-0000-0000-000000000001	2026-03-21	0.2000	2.20	88.00	2026-03-24 04:18:32.870851+00
b7843e46-d3b5-4981-8aa2-a0e9cec1863e	d0000001-0000-0000-0000-000000000003	b0000001-0000-0000-0000-000000000001	2026-03-22	0.1800	1.80	85.00	2026-03-24 04:18:32.870851+00
c031bc9a-16ce-4959-9c5d-8e469fcd792a	d0000001-0000-0000-0000-000000000003	b0000001-0000-0000-0000-000000000001	2026-03-23	0.2200	2.40	90.00	2026-03-24 04:18:32.870851+00
e0cf9ae8-18f8-4279-bfdb-3c09809464bb	d0000001-0000-0000-0000-000000000003	b0000001-0000-0000-0000-000000000001	2026-03-24	0.1800	1.80	85.00	2026-03-24 04:18:32.870851+00
af1b15ab-c547-42f6-bdb6-e28645ccc7bc	d0000001-0000-0000-0000-000000000004	b0000001-0000-0000-0000-000000000001	2026-03-18	0.2000	2.50	70.00	2026-03-24 04:18:32.870851+00
c2e36da8-a80a-4777-b5e7-413f81aed489	d0000001-0000-0000-0000-000000000004	b0000001-0000-0000-0000-000000000001	2026-03-19	0.2200	2.60	72.00	2026-03-24 04:18:32.870851+00
094a7988-9921-44c1-b605-855fdf88c1df	d0000001-0000-0000-0000-000000000004	b0000001-0000-0000-0000-000000000001	2026-03-20	0.1800	2.20	68.00	2026-03-24 04:18:32.870851+00
9e1ee2ab-4981-487e-bb33-dcda04fb4e26	d0000001-0000-0000-0000-000000000004	b0000001-0000-0000-0000-000000000001	2026-03-21	0.2500	2.80	75.00	2026-03-24 04:18:32.870851+00
e7a417fd-d882-49b5-b2ee-3c783312ddab	d0000001-0000-0000-0000-000000000004	b0000001-0000-0000-0000-000000000001	2026-03-22	0.2200	2.50	72.00	2026-03-24 04:18:32.870851+00
01a30f36-b2a4-4403-9912-ebc9a643ff02	d0000001-0000-0000-0000-000000000004	b0000001-0000-0000-0000-000000000001	2026-03-23	0.2800	3.00	78.00	2026-03-24 04:18:32.870851+00
71de4b2b-bfdb-42e4-a51b-ddc50aecce2a	d0000001-0000-0000-0000-000000000004	b0000001-0000-0000-0000-000000000001	2026-03-24	0.2100	2.50	70.00	2026-03-24 04:18:32.870851+00
05106e2a-4ecd-4598-ba4b-35aa0dc8eae9	d0000001-0000-0000-0000-000000000005	b0000001-0000-0000-0000-000000000001	2026-03-18	0.0800	0.80	40.00	2026-03-24 04:18:32.870851+00
ab5d7ee5-81d0-488e-ad05-281c921d4bdc	d0000001-0000-0000-0000-000000000005	b0000001-0000-0000-0000-000000000001	2026-03-19	0.1000	1.00	45.00	2026-03-24 04:18:32.870851+00
1b3d429d-9a5b-4eaf-9477-7bfeb7803615	d0000001-0000-0000-0000-000000000005	b0000001-0000-0000-0000-000000000001	2026-03-20	0.0900	0.90	42.00	2026-03-24 04:18:32.870851+00
e34039e4-8bdc-4565-b0ac-e52cb716569d	d0000001-0000-0000-0000-000000000005	b0000001-0000-0000-0000-000000000001	2026-03-21	0.1200	1.20	50.00	2026-03-24 04:18:32.870851+00
b5cddea7-89d5-46cc-a133-64e4061d5ec4	d0000001-0000-0000-0000-000000000005	b0000001-0000-0000-0000-000000000001	2026-03-22	0.1000	1.00	45.00	2026-03-24 04:18:32.870851+00
d5dc1e11-a298-4597-b9b7-ae7be42bbefe	d0000001-0000-0000-0000-000000000005	b0000001-0000-0000-0000-000000000001	2026-03-23	0.1400	1.40	55.00	2026-03-24 04:18:32.870851+00
19a2320f-a56f-43dc-8625-82ce40bc768b	d0000001-0000-0000-0000-000000000005	b0000001-0000-0000-0000-000000000001	2026-03-24	0.0800	0.80	40.00	2026-03-24 04:18:32.870851+00
6947712e-be93-4250-a0b3-df708a1d9d25	d0000001-0000-0000-0000-000000000006	b0000001-0000-0000-0000-000000000001	2026-03-18	0.0500	0.60	30.00	2026-03-24 04:18:32.870851+00
ffdc433d-cba7-4ae9-8aac-72d9adb89985	d0000001-0000-0000-0000-000000000006	b0000001-0000-0000-0000-000000000001	2026-03-19	0.0600	0.70	35.00	2026-03-24 04:18:32.870851+00
c565cd60-ecce-49f4-8fba-a46eb083176f	d0000001-0000-0000-0000-000000000006	b0000001-0000-0000-0000-000000000001	2026-03-20	0.0500	0.60	30.00	2026-03-24 04:18:32.870851+00
353d066e-b506-4c26-93d9-d9e9334cbd7e	d0000001-0000-0000-0000-000000000006	b0000001-0000-0000-0000-000000000001	2026-03-21	0.0700	0.80	38.00	2026-03-24 04:18:32.870851+00
7b19e57d-fc49-475f-9e79-50f2de9529d2	d0000001-0000-0000-0000-000000000006	b0000001-0000-0000-0000-000000000001	2026-03-22	0.0600	0.70	35.00	2026-03-24 04:18:32.870851+00
5ba975f2-ff8a-41b7-9e3a-15c5427862aa	d0000001-0000-0000-0000-000000000006	b0000001-0000-0000-0000-000000000001	2026-03-23	0.0800	0.90	40.00	2026-03-24 04:18:32.870851+00
6fce36eb-3899-4055-9111-d2d45235cc3b	d0000001-0000-0000-0000-000000000006	b0000001-0000-0000-0000-000000000001	2026-03-24	0.0500	0.60	30.00	2026-03-24 04:18:32.870851+00
\.


--
-- Data for Name: dispositivos; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dispositivos (id, zona_id, casa_id, tipo, nombre, mac_address, ip_local, firmware_version, estado, ultimo_heartbeat, configuracion, activo, created_at, updated_at) FROM stdin;
f0000001-0000-0000-0000-000000000001	d0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	modulo_shelly	Shelly Sala	AA:BB:CC:DD:01:01	\N	1.4.2	online	\N	{}	t	2026-03-24 04:18:32.869055+00	2026-03-24 04:18:32.869055+00
f0000001-0000-0000-0000-000000000002	d0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	sensor_pir	PIR Sala	AA:BB:CC:DD:01:02	\N	1.0.0	online	\N	{}	t	2026-03-24 04:18:32.869055+00	2026-03-24 04:18:32.869055+00
f0000001-0000-0000-0000-000000000003	d0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	sensor_crepuscular	Luz Sala	AA:BB:CC:DD:01:03	\N	1.0.0	online	\N	{}	t	2026-03-24 04:18:32.869055+00	2026-03-24 04:18:32.869055+00
f0000001-0000-0000-0000-000000000004	d0000001-0000-0000-0000-000000000002	b0000001-0000-0000-0000-000000000001	modulo_shelly	Shelly Cocina	AA:BB:CC:DD:02:01	\N	1.4.2	online	\N	{}	t	2026-03-24 04:18:32.869055+00	2026-03-24 04:18:32.869055+00
f0000001-0000-0000-0000-000000000005	d0000001-0000-0000-0000-000000000003	b0000001-0000-0000-0000-000000000001	modulo_shelly	Shelly Rec	AA:BB:CC:DD:03:01	\N	1.4.1	online	\N	{}	t	2026-03-24 04:18:32.869055+00	2026-03-24 04:18:32.869055+00
f0000001-0000-0000-0000-000000000006	d0000001-0000-0000-0000-000000000004	b0000001-0000-0000-0000-000000000001	modulo_shelly	Shelly Rec2	AA:BB:CC:DD:04:01	\N	1.4.2	online	\N	{}	t	2026-03-24 04:18:32.869055+00	2026-03-24 04:18:32.869055+00
f0000001-0000-0000-0000-000000000007	d0000001-0000-0000-0000-000000000005	b0000001-0000-0000-0000-000000000001	sensor_pir	PIR Pasillo	AA:BB:CC:DD:05:01	\N	1.0.0	offline	\N	{}	t	2026-03-24 04:18:32.869055+00	2026-03-24 04:18:32.869055+00
f0000001-0000-0000-0000-000000000008	d0000001-0000-0000-0000-000000000006	b0000001-0000-0000-0000-000000000001	modulo_shelly	Shelly Baño	AA:BB:CC:DD:06:01	\N	1.4.2	online	\N	{}	t	2026-03-24 04:18:32.869055+00	2026-03-24 04:18:32.869055+00
\.


--
-- Data for Name: horas_pico; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.horas_pico (id, zona_id, casa_id, hora, dia_semana, minutos_promedio, periodo_inicio, periodo_fin, updated_at) FROM stdin;
57a1bfee-677d-4627-b016-e456b455821b	d0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	7	0	35.00	2026-03-17	2026-03-24	2026-03-24 04:18:32.87293+00
54906384-8891-477a-882b-536fd90537eb	d0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	8	0	30.00	2026-03-17	2026-03-24	2026-03-24 04:18:32.87293+00
b41239b9-2275-426e-bee5-942fabedf840	d0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	18	0	50.00	2026-03-17	2026-03-24	2026-03-24 04:18:32.87293+00
eef3712e-fa20-4582-9cfe-5efdfbcda19e	d0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	19	0	55.00	2026-03-17	2026-03-24	2026-03-24 04:18:32.87293+00
63735d38-9afb-48d5-8c7f-4db2d69a24b9	d0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	20	0	50.00	2026-03-17	2026-03-24	2026-03-24 04:18:32.87293+00
73e2bea1-188d-47fe-b3ad-5798f06594ba	d0000001-0000-0000-0000-000000000002	b0000001-0000-0000-0000-000000000001	6	0	40.00	2026-03-17	2026-03-24	2026-03-24 04:18:32.87293+00
0adfe594-d379-488f-94f9-acd7d89c501e	d0000001-0000-0000-0000-000000000002	b0000001-0000-0000-0000-000000000001	7	0	55.00	2026-03-17	2026-03-24	2026-03-24 04:18:32.87293+00
5c293476-e265-4a15-854a-913533f3374d	d0000001-0000-0000-0000-000000000002	b0000001-0000-0000-0000-000000000001	8	0	45.00	2026-03-17	2026-03-24	2026-03-24 04:18:32.87293+00
01036966-0b85-495d-9960-c37ba654013f	d0000001-0000-0000-0000-000000000002	b0000001-0000-0000-0000-000000000001	13	0	50.00	2026-03-17	2026-03-24	2026-03-24 04:18:32.87293+00
7a6ec680-bc60-4544-b8f1-712bd2457a29	d0000001-0000-0000-0000-000000000002	b0000001-0000-0000-0000-000000000001	14	0	45.00	2026-03-17	2026-03-24	2026-03-24 04:18:32.87293+00
\.


--
-- Data for Name: modo_nocturno; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.modo_nocturno (id, casa_id, habilitado, deteccion_inteligente, hora_inicio, hora_fin, updated_at) FROM stdin;
e0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	t	t	23:00:00	06:00:00	2026-03-24 04:18:32.870092+00
\.


--
-- Data for Name: owners; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.owners (id, nombre, email, password_hash, telefono, max_casas, activo, created_at, updated_at) FROM stdin;
a0000001-0000-0000-0000-000000000001	Admin Principal	admin@mihogar.com	$2b$12$9gXqBtPjKGD8iMRg7rzINudxZPoGa2bPBux0t9RdeiLGGSNw1lsMC	\N	3	t	2026-03-24 04:18:32.865542+00	2026-03-24 04:18:32.865542+00
\.


--
-- Data for Name: perfiles_sagemaker; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.perfiles_sagemaker (id, zona_id, casa_id, umbral_oscuridad_sugerido, tiempo_apagado_sugerido, horas_uso_optimas, patron_detectado, modelo_version, confianza, datos_entrenamiento_desde, datos_entrenamiento_hasta, aplicado, created_at) FROM stdin;
\.


--
-- Data for Name: permisos_zona; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.permisos_zona (id, usuario_id, zona_id, puede_controlar, puede_configurar, created_at) FROM stdin;
59bed213-a912-4169-9aa4-7c03aa6e74b3	c0000001-0000-0000-0000-000000000002	d0000001-0000-0000-0000-000000000001	t	t	2026-03-24 04:18:32.868589+00
e36e4f61-c4b5-4aec-ad9f-accb4223f7a5	c0000001-0000-0000-0000-000000000002	d0000001-0000-0000-0000-000000000002	t	t	2026-03-24 04:18:32.868589+00
fb098786-8828-45b4-8c54-da0f40409a11	c0000001-0000-0000-0000-000000000002	d0000001-0000-0000-0000-000000000003	t	t	2026-03-24 04:18:32.868589+00
a28f646d-a64d-44fa-82d9-66a3cafe90d2	c0000001-0000-0000-0000-000000000003	d0000001-0000-0000-0000-000000000004	t	f	2026-03-24 04:18:32.868589+00
\.


--
-- Data for Name: temporizadores; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.temporizadores (id, zona_id, casa_id, tipo, hora_inicio, hora_fin, lunes, martes, miercoles, jueves, viernes, sabado, domingo, solo_si_oscuro, habilitado, created_at, updated_at) FROM stdin;
0adcadee-ab27-49cb-adec-8028761a2d83	d0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	horario_fijo	18:00:00	23:00:00	t	t	t	t	t	f	f	t	t	2026-03-24 04:18:32.869668+00	2026-03-24 04:18:32.869668+00
eb3cccf6-c95c-43be-b67d-20bb9d080d90	d0000001-0000-0000-0000-000000000002	b0000001-0000-0000-0000-000000000001	horario_fijo	06:00:00	08:00:00	t	t	t	t	t	t	t	f	t	2026-03-24 04:18:32.869668+00	2026-03-24 04:18:32.869668+00
43d59584-ad95-4c1c-9417-8b094d703127	d0000001-0000-0000-0000-000000000003	b0000001-0000-0000-0000-000000000001	horario_fijo	22:00:00	06:00:00	t	t	t	t	t	t	t	f	f	2026-03-24 04:18:32.869668+00	2026-03-24 04:18:32.869668+00
\.


--
-- Data for Name: usuarios_casa; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.usuarios_casa (id, casa_id, owner_id, nombre, email, password_hash, pin_hash, rol, metodo_acceso, activo, created_at, updated_at) FROM stdin;
c0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	a0000001-0000-0000-0000-000000000001	Admin Principal	admin@mihogar.com	$2b$12$9gXqBtPjKGD8iMRg7rzINudxZPoGa2bPBux0t9RdeiLGGSNw1lsMC	\N	administrador	email	t	2026-03-24 04:18:32.866666+00	2026-03-24 04:18:32.866666+00
c0000001-0000-0000-0000-000000000002	b0000001-0000-0000-0000-000000000001	\N	María García	maria@mihogar.com	$2b$12$wjBOA37ZDg9YZh.iaHjiVOBLBB/7YQ0wuFyqZ.tngGGmQGKmWN1Da	\N	encargado	email	t	2026-03-24 04:18:32.867154+00	2026-03-24 04:18:32.867154+00
c0000001-0000-0000-0000-000000000003	b0000001-0000-0000-0000-000000000001	\N	Carlos Jr.	\N	\N	$2b$12$7d4IGNY3spxKiAPCI280fuwQoegfp5eEniiI3KA0cGdkuLUrd8VW6	usuario	pin	t	2026-03-24 04:18:32.867327+00	2026-03-24 04:18:32.867327+00
\.


--
-- Data for Name: zonas; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.zonas (id, casa_id, nombre, tipo, icono, orden, activa, created_at, updated_at) FROM stdin;
d0000001-0000-0000-0000-000000000001	b0000001-0000-0000-0000-000000000001	Sala	habitacion	\N	1	t	2026-03-24 04:18:32.867498+00	2026-03-24 04:18:32.867498+00
d0000001-0000-0000-0000-000000000002	b0000001-0000-0000-0000-000000000001	Cocina	habitacion	\N	2	t	2026-03-24 04:18:32.867498+00	2026-03-24 04:18:32.867498+00
d0000001-0000-0000-0000-000000000003	b0000001-0000-0000-0000-000000000001	Recámara Principal	habitacion	\N	3	t	2026-03-24 04:18:32.867498+00	2026-03-24 04:18:32.867498+00
d0000001-0000-0000-0000-000000000004	b0000001-0000-0000-0000-000000000001	Recámara 2	habitacion	\N	4	t	2026-03-24 04:18:32.867498+00	2026-03-24 04:18:32.867498+00
d0000001-0000-0000-0000-000000000005	b0000001-0000-0000-0000-000000000001	Pasillo	zona_de_paso	\N	5	t	2026-03-24 04:18:32.867498+00	2026-03-24 04:18:32.867498+00
d0000001-0000-0000-0000-000000000006	b0000001-0000-0000-0000-000000000001	Baño	zona_de_paso	\N	6	t	2026-03-24 04:18:32.867498+00	2026-03-24 04:18:32.867498+00
\.


--
-- Data for Name: zonas_nocturnas; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.zonas_nocturnas (id, modo_nocturno_id, zona_id, habilitada) FROM stdin;
69414418-8821-44a8-9f42-81fd62591b03	e0000001-0000-0000-0000-000000000001	d0000001-0000-0000-0000-000000000005	t
f420b09a-08c1-42a6-9f90-62e04a490efa	e0000001-0000-0000-0000-000000000001	d0000001-0000-0000-0000-000000000006	t
1aa201db-0f3b-4a95-afa2-310f15be22b4	e0000001-0000-0000-0000-000000000001	d0000001-0000-0000-0000-000000000003	f
d126f584-2530-4663-9bb6-802bee2068d2	e0000001-0000-0000-0000-000000000001	d0000001-0000-0000-0000-000000000004	f
\.


--
-- Name: alertas alertas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alertas
    ADD CONSTRAINT alertas_pkey PRIMARY KEY (id);


--
-- Name: casas casas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.casas
    ADD CONSTRAINT casas_pkey PRIMARY KEY (id);


--
-- Name: config_zonas config_zonas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_zonas
    ADD CONSTRAINT config_zonas_pkey PRIMARY KEY (id);


--
-- Name: config_zonas config_zonas_zona_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_zonas
    ADD CONSTRAINT config_zonas_zona_id_key UNIQUE (zona_id);


--
-- Name: consumo_bimestral consumo_bimestral_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.consumo_bimestral
    ADD CONSTRAINT consumo_bimestral_pkey PRIMARY KEY (id);


--
-- Name: consumo_diario consumo_diario_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.consumo_diario
    ADD CONSTRAINT consumo_diario_pkey PRIMARY KEY (id);


--
-- Name: dispositivos dispositivos_mac_address_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispositivos
    ADD CONSTRAINT dispositivos_mac_address_key UNIQUE (mac_address);


--
-- Name: dispositivos dispositivos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispositivos
    ADD CONSTRAINT dispositivos_pkey PRIMARY KEY (id);


--
-- Name: horas_pico horas_pico_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.horas_pico
    ADD CONSTRAINT horas_pico_pkey PRIMARY KEY (id);


--
-- Name: modo_nocturno modo_nocturno_casa_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modo_nocturno
    ADD CONSTRAINT modo_nocturno_casa_id_key UNIQUE (casa_id);


--
-- Name: modo_nocturno modo_nocturno_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modo_nocturno
    ADD CONSTRAINT modo_nocturno_pkey PRIMARY KEY (id);


--
-- Name: owners owners_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.owners
    ADD CONSTRAINT owners_email_key UNIQUE (email);


--
-- Name: owners owners_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.owners
    ADD CONSTRAINT owners_pkey PRIMARY KEY (id);


--
-- Name: perfiles_sagemaker perfiles_sagemaker_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.perfiles_sagemaker
    ADD CONSTRAINT perfiles_sagemaker_pkey PRIMARY KEY (id);


--
-- Name: permisos_zona permisos_zona_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permisos_zona
    ADD CONSTRAINT permisos_zona_pkey PRIMARY KEY (id);


--
-- Name: temporizadores temporizadores_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.temporizadores
    ADD CONSTRAINT temporizadores_pkey PRIMARY KEY (id);


--
-- Name: consumo_bimestral uq_bimestre_casa; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.consumo_bimestral
    ADD CONSTRAINT uq_bimestre_casa UNIQUE (casa_id, bimestre, anio);


--
-- Name: consumo_diario uq_consumo_dia_zona; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.consumo_diario
    ADD CONSTRAINT uq_consumo_dia_zona UNIQUE (zona_id, fecha);


--
-- Name: usuarios_casa uq_email_por_casa; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios_casa
    ADD CONSTRAINT uq_email_por_casa UNIQUE (casa_id, email);


--
-- Name: horas_pico uq_hora_pico; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.horas_pico
    ADD CONSTRAINT uq_hora_pico UNIQUE (zona_id, hora, dia_semana, periodo_inicio);


--
-- Name: permisos_zona uq_permiso_usuario_zona; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permisos_zona
    ADD CONSTRAINT uq_permiso_usuario_zona UNIQUE (usuario_id, zona_id);


--
-- Name: zonas_nocturnas uq_zona_nocturna; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zonas_nocturnas
    ADD CONSTRAINT uq_zona_nocturna UNIQUE (modo_nocturno_id, zona_id);


--
-- Name: zonas uq_zona_nombre_casa; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zonas
    ADD CONSTRAINT uq_zona_nombre_casa UNIQUE (casa_id, nombre);


--
-- Name: usuarios_casa usuarios_casa_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios_casa
    ADD CONSTRAINT usuarios_casa_pkey PRIMARY KEY (id);


--
-- Name: zonas_nocturnas zonas_nocturnas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zonas_nocturnas
    ADD CONSTRAINT zonas_nocturnas_pkey PRIMARY KEY (id);


--
-- Name: zonas zonas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zonas
    ADD CONSTRAINT zonas_pkey PRIMARY KEY (id);


--
-- Name: idx_alertas_casa; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alertas_casa ON public.alertas USING btree (casa_id, created_at DESC);


--
-- Name: idx_casas_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_casas_owner ON public.casas USING btree (owner_id);


--
-- Name: idx_config_zona; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_config_zona ON public.config_zonas USING btree (zona_id);


--
-- Name: idx_consumo_casa_fecha; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_consumo_casa_fecha ON public.consumo_diario USING btree (casa_id, fecha);


--
-- Name: idx_dispositivos_casa; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dispositivos_casa ON public.dispositivos USING btree (casa_id);


--
-- Name: idx_dispositivos_zona; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dispositivos_zona ON public.dispositivos USING btree (zona_id);


--
-- Name: idx_temporizadores_casa; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temporizadores_casa ON public.temporizadores USING btree (casa_id);


--
-- Name: idx_temporizadores_zona; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temporizadores_zona ON public.temporizadores USING btree (zona_id);


--
-- Name: idx_usuarios_casa; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_usuarios_casa ON public.usuarios_casa USING btree (casa_id);


--
-- Name: idx_usuarios_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_usuarios_email ON public.usuarios_casa USING btree (email);


--
-- Name: idx_zonas_casa; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_zonas_casa ON public.zonas USING btree (casa_id);


--
-- Name: alertas alertas_casa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alertas
    ADD CONSTRAINT alertas_casa_id_fkey FOREIGN KEY (casa_id) REFERENCES public.casas(id) ON DELETE CASCADE;


--
-- Name: alertas alertas_dispositivo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alertas
    ADD CONSTRAINT alertas_dispositivo_id_fkey FOREIGN KEY (dispositivo_id) REFERENCES public.dispositivos(id) ON DELETE SET NULL;


--
-- Name: alertas alertas_zona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alertas
    ADD CONSTRAINT alertas_zona_id_fkey FOREIGN KEY (zona_id) REFERENCES public.zonas(id) ON DELETE SET NULL;


--
-- Name: casas casas_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.casas
    ADD CONSTRAINT casas_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.owners(id) ON DELETE CASCADE;


--
-- Name: config_zonas config_zonas_zona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_zonas
    ADD CONSTRAINT config_zonas_zona_id_fkey FOREIGN KEY (zona_id) REFERENCES public.zonas(id) ON DELETE CASCADE;


--
-- Name: consumo_bimestral consumo_bimestral_casa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.consumo_bimestral
    ADD CONSTRAINT consumo_bimestral_casa_id_fkey FOREIGN KEY (casa_id) REFERENCES public.casas(id) ON DELETE CASCADE;


--
-- Name: consumo_diario consumo_diario_casa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.consumo_diario
    ADD CONSTRAINT consumo_diario_casa_id_fkey FOREIGN KEY (casa_id) REFERENCES public.casas(id) ON DELETE CASCADE;


--
-- Name: consumo_diario consumo_diario_zona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.consumo_diario
    ADD CONSTRAINT consumo_diario_zona_id_fkey FOREIGN KEY (zona_id) REFERENCES public.zonas(id) ON DELETE CASCADE;


--
-- Name: dispositivos dispositivos_casa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispositivos
    ADD CONSTRAINT dispositivos_casa_id_fkey FOREIGN KEY (casa_id) REFERENCES public.casas(id) ON DELETE CASCADE;


--
-- Name: dispositivos dispositivos_zona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispositivos
    ADD CONSTRAINT dispositivos_zona_id_fkey FOREIGN KEY (zona_id) REFERENCES public.zonas(id) ON DELETE CASCADE;


--
-- Name: horas_pico horas_pico_casa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.horas_pico
    ADD CONSTRAINT horas_pico_casa_id_fkey FOREIGN KEY (casa_id) REFERENCES public.casas(id) ON DELETE CASCADE;


--
-- Name: horas_pico horas_pico_zona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.horas_pico
    ADD CONSTRAINT horas_pico_zona_id_fkey FOREIGN KEY (zona_id) REFERENCES public.zonas(id) ON DELETE CASCADE;


--
-- Name: modo_nocturno modo_nocturno_casa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modo_nocturno
    ADD CONSTRAINT modo_nocturno_casa_id_fkey FOREIGN KEY (casa_id) REFERENCES public.casas(id) ON DELETE CASCADE;


--
-- Name: perfiles_sagemaker perfiles_sagemaker_casa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.perfiles_sagemaker
    ADD CONSTRAINT perfiles_sagemaker_casa_id_fkey FOREIGN KEY (casa_id) REFERENCES public.casas(id) ON DELETE CASCADE;


--
-- Name: perfiles_sagemaker perfiles_sagemaker_zona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.perfiles_sagemaker
    ADD CONSTRAINT perfiles_sagemaker_zona_id_fkey FOREIGN KEY (zona_id) REFERENCES public.zonas(id) ON DELETE CASCADE;


--
-- Name: permisos_zona permisos_zona_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permisos_zona
    ADD CONSTRAINT permisos_zona_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios_casa(id) ON DELETE CASCADE;


--
-- Name: permisos_zona permisos_zona_zona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permisos_zona
    ADD CONSTRAINT permisos_zona_zona_id_fkey FOREIGN KEY (zona_id) REFERENCES public.zonas(id) ON DELETE CASCADE;


--
-- Name: temporizadores temporizadores_casa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.temporizadores
    ADD CONSTRAINT temporizadores_casa_id_fkey FOREIGN KEY (casa_id) REFERENCES public.casas(id) ON DELETE CASCADE;


--
-- Name: temporizadores temporizadores_zona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.temporizadores
    ADD CONSTRAINT temporizadores_zona_id_fkey FOREIGN KEY (zona_id) REFERENCES public.zonas(id) ON DELETE CASCADE;


--
-- Name: usuarios_casa usuarios_casa_casa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios_casa
    ADD CONSTRAINT usuarios_casa_casa_id_fkey FOREIGN KEY (casa_id) REFERENCES public.casas(id) ON DELETE CASCADE;


--
-- Name: usuarios_casa usuarios_casa_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios_casa
    ADD CONSTRAINT usuarios_casa_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.owners(id);


--
-- Name: zonas zonas_casa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zonas
    ADD CONSTRAINT zonas_casa_id_fkey FOREIGN KEY (casa_id) REFERENCES public.casas(id) ON DELETE CASCADE;


--
-- Name: zonas_nocturnas zonas_nocturnas_modo_nocturno_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zonas_nocturnas
    ADD CONSTRAINT zonas_nocturnas_modo_nocturno_id_fkey FOREIGN KEY (modo_nocturno_id) REFERENCES public.modo_nocturno(id) ON DELETE CASCADE;


--
-- Name: zonas_nocturnas zonas_nocturnas_zona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zonas_nocturnas
    ADD CONSTRAINT zonas_nocturnas_zona_id_fkey FOREIGN KEY (zona_id) REFERENCES public.zonas(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict rbeSh4hs2CF2gjHbPtXetiI1Vprdo2H53zP35fJIbtcbNOdfgv4xzY1gLnVdXiN

