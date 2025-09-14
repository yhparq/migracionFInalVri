--
-- PostgreSQL database dump
--

\restrict wsod1mFO2jW2ZaehKs7NPNADM5COeEPGrV0Nx5F2wyxEzkhnROYcEggwTayMA5z

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: fuzzystrmatch; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS fuzzystrmatch WITH SCHEMA public;


--
-- Name: EXTENSION fuzzystrmatch; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION fuzzystrmatch IS 'determine similarities and distance between strings';


--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: dic_acciones; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_acciones (
    id integer NOT NULL,
    nombre text NOT NULL,
    descripcion text NOT NULL,
    id_etapa_pertenencia integer,
    id_servicios integer
);


ALTER TABLE public.dic_acciones OWNER TO admin;

--
-- Name: COLUMN dic_acciones.id_etapa_pertenencia; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.dic_acciones.id_etapa_pertenencia IS 'si es NULL significa que esta acción puede ocurrir en cualquier etapa';


--
-- Name: dic_areas_ocde; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_areas_ocde (
    id integer NOT NULL,
    nombre text NOT NULL,
    estado_area smallint NOT NULL
);


ALTER TABLE public.dic_areas_ocde OWNER TO admin;

--
-- Name: COLUMN dic_areas_ocde.estado_area; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.dic_areas_ocde.estado_area IS '0 = inactivo
1 = activo';


--
-- Name: dic_carreras; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_carreras (
    id integer NOT NULL,
    id_facultad integer NOT NULL,
    nombre text NOT NULL,
    estado_carrera smallint NOT NULL
);


ALTER TABLE public.dic_carreras OWNER TO admin;

--
-- Name: COLUMN dic_carreras.estado_carrera; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.dic_carreras.estado_carrera IS '0 = inactivo
1 = activo';


--
-- Name: dic_categoria; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_categoria (
    id integer NOT NULL,
    tipo character(1) NOT NULL,
    nombre text NOT NULL,
    abreviatura character varying,
    estado_categoria character varying NOT NULL
);


ALTER TABLE public.dic_categoria OWNER TO admin;

--
-- Name: dic_categoria_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.dic_categoria_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dic_categoria_id_seq OWNER TO admin;

--
-- Name: dic_categoria_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.dic_categoria_id_seq OWNED BY public.dic_categoria.id;


--
-- Name: dic_denominaciones; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_denominaciones (
    id integer NOT NULL,
    id_especialidad integer NOT NULL,
    nombre text NOT NULL,
    denominacion_actual smallint NOT NULL
);


ALTER TABLE public.dic_denominaciones OWNER TO admin;

--
-- Name: COLUMN dic_denominaciones.denominacion_actual; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.dic_denominaciones.denominacion_actual IS '1 = activo
2 = inactivo';


--
-- Name: dic_disciplinas; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_disciplinas (
    id integer NOT NULL,
    id_subarea integer NOT NULL,
    nombre text NOT NULL,
    estado_disciplina smallint NOT NULL
);


ALTER TABLE public.dic_disciplinas OWNER TO admin;

--
-- Name: COLUMN dic_disciplinas.estado_disciplina; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.dic_disciplinas.estado_disciplina IS '0 = inactivo
1 = activo';


--
-- Name: dic_especialidades; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_especialidades (
    id integer NOT NULL,
    id_carrera integer,
    nombre text NOT NULL,
    estado_especialidad smallint NOT NULL
);


ALTER TABLE public.dic_especialidades OWNER TO admin;

--
-- Name: COLUMN dic_especialidades.estado_especialidad; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.dic_especialidades.estado_especialidad IS '0 = inactivo
1 = activo';


--
-- Name: dic_etapas; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_etapas (
    id integer NOT NULL,
    nombre text NOT NULL,
    descripcion text NOT NULL
);


ALTER TABLE public.dic_etapas OWNER TO admin;

--
-- Name: dic_facultades; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_facultades (
    id integer NOT NULL,
    nombre text NOT NULL,
    abreviatura character varying(10) NOT NULL,
    id_area integer NOT NULL,
    estado_facultad smallint NOT NULL
);


ALTER TABLE public.dic_facultades OWNER TO admin;

--
-- Name: COLUMN dic_facultades.id_area; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.dic_facultades.id_area IS 'Es el area de OCDE';


--
-- Name: COLUMN dic_facultades.estado_facultad; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.dic_facultades.estado_facultad IS '0 = inactivo
1 = activo';


--
-- Name: dic_grados_academicos; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_grados_academicos (
    id integer NOT NULL,
    nombre character varying(255) NOT NULL,
    abreviatura character varying(20),
    estado_dic_grados_academicos smallint DEFAULT 1 NOT NULL
);


ALTER TABLE public.dic_grados_academicos OWNER TO admin;

--
-- Name: dic_grados_academicos_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.dic_grados_academicos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dic_grados_academicos_id_seq OWNER TO admin;

--
-- Name: dic_grados_academicos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.dic_grados_academicos_id_seq OWNED BY public.dic_grados_academicos.id;


--
-- Name: dic_lineas_universidad; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_lineas_universidad (
    id integer NOT NULL,
    nombre text NOT NULL,
    estado_linea_universidad smallint NOT NULL
);


ALTER TABLE public.dic_lineas_universidad OWNER TO admin;

--
-- Name: dic_modalidades; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_modalidades (
    id integer NOT NULL,
    descripcion text NOT NULL,
    ruta text NOT NULL,
    estado_modalidad smallint NOT NULL
);


ALTER TABLE public.dic_modalidades OWNER TO admin;

--
-- Name: COLUMN dic_modalidades.estado_modalidad; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.dic_modalidades.estado_modalidad IS '0 = inactivo
1 = activo';


--
-- Name: dic_modalidades_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.dic_modalidades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dic_modalidades_id_seq OWNER TO admin;

--
-- Name: dic_modalidades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.dic_modalidades_id_seq OWNED BY public.dic_modalidades.id;


--
-- Name: dic_nivel_admin; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_nivel_admin (
    id integer NOT NULL,
    nombre text,
    descripcion text,
    estado smallint
);


ALTER TABLE public.dic_nivel_admin OWNER TO admin;

--
-- Name: dic_nivel_admin_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.dic_nivel_admin_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dic_nivel_admin_id_seq OWNER TO admin;

--
-- Name: dic_nivel_admin_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.dic_nivel_admin_id_seq OWNED BY public.dic_nivel_admin.id;


--
-- Name: dic_nivel_coordinador; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_nivel_coordinador (
    id integer NOT NULL,
    nombre text NOT NULL,
    descripcion text,
    estado smallint
);


ALTER TABLE public.dic_nivel_coordinador OWNER TO admin;

--
-- Name: dic_nivel_coordinador_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.dic_nivel_coordinador_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dic_nivel_coordinador_id_seq OWNER TO admin;

--
-- Name: dic_nivel_coordinador_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.dic_nivel_coordinador_id_seq OWNED BY public.dic_nivel_coordinador.id;


--
-- Name: dic_obtencion_studios; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_obtencion_studios (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text
);


ALTER TABLE public.dic_obtencion_studios OWNER TO admin;

--
-- Name: dic_obtencion_studios_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.dic_obtencion_studios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dic_obtencion_studios_id_seq OWNER TO admin;

--
-- Name: dic_obtencion_studios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.dic_obtencion_studios_id_seq OWNED BY public.dic_obtencion_studios.id;


--
-- Name: dic_orden_jurado; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_orden_jurado (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    abreviatura character varying(20),
    estado smallint DEFAULT 1 NOT NULL
);


ALTER TABLE public.dic_orden_jurado OWNER TO admin;

--
-- Name: dic_orden_jurado_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.dic_orden_jurado_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dic_orden_jurado_id_seq OWNER TO admin;

--
-- Name: dic_orden_jurado_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.dic_orden_jurado_id_seq OWNED BY public.dic_orden_jurado.id;


--
-- Name: dic_sedes; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_sedes (
    id integer NOT NULL,
    nombre text NOT NULL
);


ALTER TABLE public.dic_sedes OWNER TO admin;

--
-- Name: dic_sedes_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.dic_sedes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dic_sedes_id_seq OWNER TO admin;

--
-- Name: dic_sedes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.dic_sedes_id_seq OWNED BY public.dic_sedes.id;


--
-- Name: dic_servicios; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_servicios (
    id integer NOT NULL,
    nombre text NOT NULL,
    descripcion text
);


ALTER TABLE public.dic_servicios OWNER TO admin;

--
-- Name: dic_servicios_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.dic_servicios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dic_servicios_id_seq OWNER TO admin;

--
-- Name: dic_servicios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.dic_servicios_id_seq OWNED BY public.dic_servicios.id;


--
-- Name: dic_subareas_ocde; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_subareas_ocde (
    id integer NOT NULL,
    id_area integer NOT NULL,
    nombre text NOT NULL,
    estado_subarea smallint NOT NULL
);


ALTER TABLE public.dic_subareas_ocde OWNER TO admin;

--
-- Name: COLUMN dic_subareas_ocde.estado_subarea; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.dic_subareas_ocde.estado_subarea IS '0 = inactivo
1 = activo';


--
-- Name: dic_tipo_archivo; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_tipo_archivo (
    id integer NOT NULL,
    nombre text NOT NULL,
    descripcion text
);


ALTER TABLE public.dic_tipo_archivo OWNER TO admin;

--
-- Name: dic_tipo_trabajos; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_tipo_trabajos (
    id integer NOT NULL,
    nombre text NOT NULL,
    detalle text NOT NULL,
    estado_tipo_trabajo smallint NOT NULL
);


ALTER TABLE public.dic_tipo_trabajos OWNER TO admin;

--
-- Name: COLUMN dic_tipo_trabajos.estado_tipo_trabajo; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.dic_tipo_trabajos.estado_tipo_trabajo IS '0 = inactivo
1 = activo';


--
-- Name: dic_tipo_trabajos_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.dic_tipo_trabajos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dic_tipo_trabajos_id_seq OWNER TO admin;

--
-- Name: dic_tipo_trabajos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.dic_tipo_trabajos_id_seq OWNED BY public.dic_tipo_trabajos.id;


--
-- Name: dic_tipoevento_jurado; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_tipoevento_jurado (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    estado smallint DEFAULT 1 NOT NULL
);


ALTER TABLE public.dic_tipoevento_jurado OWNER TO admin;

--
-- Name: dic_tipoevento_jurado_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.dic_tipoevento_jurado_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dic_tipoevento_jurado_id_seq OWNER TO admin;

--
-- Name: dic_tipoevento_jurado_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.dic_tipoevento_jurado_id_seq OWNED BY public.dic_tipoevento_jurado.id;


--
-- Name: dic_universidades; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_universidades (
    id integer NOT NULL,
    nombre text,
    abreviatura character varying(50),
    estado_dic_universidades smallint,
    pais character varying(100),
    tipo_institucion character(1),
    tipo_gestion character(1)
);


ALTER TABLE public.dic_universidades OWNER TO admin;

--
-- Name: dic_visto_bueno; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.dic_visto_bueno (
    id integer NOT NULL,
    descripcion text NOT NULL,
    id_etapa integer NOT NULL
);


ALTER TABLE public.dic_visto_bueno OWNER TO admin;

--
-- Name: log_acciones; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.log_acciones (
    id bigint NOT NULL,
    id_tramite bigint NOT NULL,
    id_accion integer NOT NULL,
    id_etapa integer NOT NULL,
    id_usuario integer NOT NULL,
    fecha timestamp without time zone NOT NULL,
    mensaje text NOT NULL
);


ALTER TABLE public.log_acciones OWNER TO admin;

--
-- Name: log_acciones_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.log_acciones_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.log_acciones_id_seq OWNER TO admin;

--
-- Name: log_acciones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.log_acciones_id_seq OWNED BY public.log_acciones.id;


--
-- Name: tbl_admins; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_admins (
    id integer NOT NULL,
    id_usuario integer NOT NULL,
    nivel_admin integer NOT NULL,
    cargo text NOT NULL,
    estado_admin smallint NOT NULL
);


ALTER TABLE public.tbl_admins OWNER TO admin;

--
-- Name: COLUMN tbl_admins.nivel_admin; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_admins.nivel_admin IS 'nivel de autoridad y permisos en admin';


--
-- Name: tbl_admins_historial; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_admins_historial (
    id bigint NOT NULL,
    id_admin integer NOT NULL,
    cargo text NOT NULL,
    estado_admin smallint NOT NULL,
    detalle text,
    fecha_cambio timestamp without time zone NOT NULL
);


ALTER TABLE public.tbl_admins_historial OWNER TO admin;

--
-- Name: tbl_admins_historial_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_admins_historial_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_admins_historial_id_seq OWNER TO admin;

--
-- Name: tbl_admins_historial_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_admins_historial_id_seq OWNED BY public.tbl_admins_historial.id;


--
-- Name: tbl_admins_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_admins_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_admins_id_seq OWNER TO admin;

--
-- Name: tbl_admins_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_admins_id_seq OWNED BY public.tbl_admins.id;


--
-- Name: tbl_archivos_tramites; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_archivos_tramites (
    id integer NOT NULL,
    id_tramite bigint NOT NULL,
    id_etapa integer NOT NULL,
    id_tramites_metadatos integer NOT NULL,
    id_tipo_archivo integer NOT NULL,
    nombre_archivo text NOT NULL,
    storage text NOT NULL,
    bucket text NOT NULL,
    fecha timestamp without time zone NOT NULL,
    estado_archivo smallint NOT NULL
);


ALTER TABLE public.tbl_archivos_tramites OWNER TO admin;

--
-- Name: tbl_archivos_tramites_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_archivos_tramites_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_archivos_tramites_id_seq OWNER TO admin;

--
-- Name: tbl_archivos_tramites_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_archivos_tramites_id_seq OWNED BY public.tbl_archivos_tramites.id;


--
-- Name: tbl_asignacion_jurado; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_asignacion_jurado (
    id integer NOT NULL,
    tramite_id integer NOT NULL,
    id_etapa integer NOT NULL,
    id_orden integer NOT NULL,
    iteracion smallint NOT NULL,
    id_tipo_evento integer NOT NULL,
    docente_id integer NOT NULL,
    id_usuario_asignador integer NOT NULL,
    fecha_evento timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    estado smallint DEFAULT 1 NOT NULL
);


ALTER TABLE public.tbl_asignacion_jurado OWNER TO admin;

--
-- Name: tbl_coasesores; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_coasesores (
    id integer NOT NULL,
    id_investigador integer NOT NULL,
    estado_coasesor bigint NOT NULL
);


ALTER TABLE public.tbl_coasesores OWNER TO admin;

--
-- Name: COLUMN tbl_coasesores.estado_coasesor; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_coasesores.estado_coasesor IS '1 = activo
0 = inactivo';


--
-- Name: tbl_coasesores_historial; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_coasesores_historial (
    id bigint NOT NULL,
    id_coasesor integer NOT NULL,
    fecha_cambio timestamp without time zone NOT NULL,
    id_usuario_verificador integer NOT NULL,
    detalle text,
    estado_coasesor smallint NOT NULL,
    id_accion integer
);


ALTER TABLE public.tbl_coasesores_historial OWNER TO admin;

--
-- Name: tbl_coasesores_historial_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_coasesores_historial_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_coasesores_historial_id_seq OWNER TO admin;

--
-- Name: tbl_coasesores_historial_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_coasesores_historial_id_seq OWNED BY public.tbl_coasesores_historial.id;


--
-- Name: tbl_coasesores_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_coasesores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_coasesores_id_seq OWNER TO admin;

--
-- Name: tbl_coasesores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_coasesores_id_seq OWNED BY public.tbl_coasesores.id;


--
-- Name: tbl_conformacion_jurado_historial_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_conformacion_jurado_historial_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_conformacion_jurado_historial_id_seq OWNER TO admin;

--
-- Name: tbl_conformacion_jurado_historial_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_conformacion_jurado_historial_id_seq OWNED BY public.tbl_asignacion_jurado.id;


--
-- Name: tbl_conformacion_jurados; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_conformacion_jurados (
    id integer NOT NULL,
    id_tramite integer NOT NULL,
    id_docente integer NOT NULL,
    id_orden integer NOT NULL,
    id_etapa integer NOT NULL,
    id_usuario_asignador integer NOT NULL,
    id_asignacion integer,
    fecha_asignacion timestamp without time zone,
    estado_cj smallint NOT NULL
);


ALTER TABLE public.tbl_conformacion_jurados OWNER TO admin;

--
-- Name: tbl_conformacion_jurados_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_conformacion_jurados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_conformacion_jurados_id_seq OWNER TO admin;

--
-- Name: tbl_conformacion_jurados_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_conformacion_jurados_id_seq OWNED BY public.tbl_conformacion_jurados.id;


--
-- Name: tbl_coordinador_carrera; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_coordinador_carrera (
    id integer NOT NULL,
    id_coordinador integer NOT NULL,
    nivel_coordinador integer,
    id_facultad integer,
    id_carrera integer,
    fecha date,
    estado smallint
);


ALTER TABLE public.tbl_coordinador_carrera OWNER TO admin;

--
-- Name: tbl_coordinador_carrera_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_coordinador_carrera_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_coordinador_carrera_id_seq OWNER TO admin;

--
-- Name: tbl_coordinador_carrera_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_coordinador_carrera_id_seq OWNED BY public.tbl_coordinador_carrera.id;


--
-- Name: tbl_coordinadores; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_coordinadores (
    id integer NOT NULL,
    id_usuario integer NOT NULL,
    nivel_coordinador bigint NOT NULL,
    correo_oficina character varying(320),
    direccion_oficina text,
    horario text,
    telefono character varying(20),
    estado_coordinador smallint
);


ALTER TABLE public.tbl_coordinadores OWNER TO admin;

--
-- Name: COLUMN tbl_coordinadores.nivel_coordinador; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_coordinadores.nivel_coordinador IS '1 = básico
2 = intermedio
3 = avanzado';


--
-- Name: COLUMN tbl_coordinadores.estado_coordinador; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_coordinadores.estado_coordinador IS '0 = inactivo
1 = activo';


--
-- Name: tbl_coordinadores_historial; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_coordinadores_historial (
    id bigint NOT NULL,
    id_coordinador integer NOT NULL,
    estado_coordinador_historial smallint NOT NULL,
    fecha timestamp without time zone NOT NULL,
    numero_resolucion text,
    comentario text,
    id_accion integer,
    id_facultad integer,
    id_carrera integer,
    id_nivel_coordinador integer
);


ALTER TABLE public.tbl_coordinadores_historial OWNER TO admin;

--
-- Name: COLUMN tbl_coordinadores_historial.estado_coordinador_historial; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_coordinadores_historial.estado_coordinador_historial IS 'si estuvo activo (1) o no activo (2) en ese momento';


--
-- Name: tbl_coordinadores_historial_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_coordinadores_historial_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_coordinadores_historial_id_seq OWNER TO admin;

--
-- Name: tbl_coordinadores_historial_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_coordinadores_historial_id_seq OWNED BY public.tbl_coordinadores_historial.id;


--
-- Name: tbl_coordinadores_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_coordinadores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_coordinadores_id_seq OWNER TO admin;

--
-- Name: tbl_coordinadores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_coordinadores_id_seq OWNED BY public.tbl_coordinadores.id;


--
-- Name: tbl_correcciones_jurados; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_correcciones_jurados (
    id bigint NOT NULL,
    id_conformacion_jurado integer NOT NULL,
    orden smallint NOT NULL,
    mensaje_correccion text,
    "Fecha_correccion" timestamp without time zone NOT NULL,
    estado_correccion smallint NOT NULL,
    id_etapa integer
);


ALTER TABLE public.tbl_correcciones_jurados OWNER TO admin;

--
-- Name: tbl_correcciones_jurados_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_correcciones_jurados_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_correcciones_jurados_id_seq OWNER TO admin;

--
-- Name: tbl_correcciones_jurados_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_correcciones_jurados_id_seq OWNED BY public.tbl_correcciones_jurados.id;


--
-- Name: tbl_dictamenes_info; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_dictamenes_info (
    id bigint NOT NULL,
    id_tramite bigint NOT NULL,
    codigo_proyecto character varying(20),
    tipo_aprobacion integer NOT NULL,
    titulo text,
    denominacion text,
    tesista1 text,
    tesista2 text,
    escuela_profesional text,
    presidente text,
    primer_miembro text,
    segundo_miembro text,
    asesor text,
    coasesor text,
    fecha_dictamen timestamp without time zone,
    token text,
    estado smallint,
    tipo_acta smallint,
    folio integer,
    fecha_sustentacion timestamp without time zone,
    lugar_sustentacion text
);


ALTER TABLE public.tbl_dictamenes_info OWNER TO admin;

--
-- Name: COLUMN tbl_dictamenes_info.tipo_acta; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_dictamenes_info.tipo_acta IS '1 = Dictamen, 2 = Sustentación';


--
-- Name: tbl_dictamenes_info_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_dictamenes_info_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_dictamenes_info_id_seq OWNER TO admin;

--
-- Name: tbl_dictamenes_info_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_dictamenes_info_id_seq OWNED BY public.tbl_dictamenes_info.id;


--
-- Name: tbl_docente_categoria_historial; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_docente_categoria_historial (
    id integer NOT NULL,
    id_docente integer,
    id_categoria integer NOT NULL,
    fecha_resolucion date,
    resolucion character varying(255),
    estado smallint
);


ALTER TABLE public.tbl_docente_categoria_historial OWNER TO admin;

--
-- Name: tbl_docente_categoria_historial_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_docente_categoria_historial_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_docente_categoria_historial_id_seq OWNER TO admin;

--
-- Name: tbl_docente_categoria_historial_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_docente_categoria_historial_id_seq OWNED BY public.tbl_docente_categoria_historial.id;


--
-- Name: tbl_docentes; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_docentes (
    id integer NOT NULL,
    id_usuario integer NOT NULL,
    id_categoria integer NOT NULL,
    codigo_airhs character varying(10) NOT NULL,
    id_especialidad integer NOT NULL,
    estado_docente smallint NOT NULL,
    id_antiguo bigint
);


ALTER TABLE public.tbl_docentes OWNER TO admin;

--
-- Name: COLUMN tbl_docentes.estado_docente; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_docentes.estado_docente IS '0 = inactivo
1 = activo';


--
-- Name: tbl_docentes_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_docentes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_docentes_id_seq OWNER TO admin;

--
-- Name: tbl_docentes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_docentes_id_seq OWNED BY public.tbl_docentes.id;


--
-- Name: tbl_docentes_lineas; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_docentes_lineas (
    id bigint NOT NULL,
    id_docente integer NOT NULL,
    id_sublinea_vri integer NOT NULL,
    tipo smallint NOT NULL,
    id_estado_linea smallint NOT NULL
);


ALTER TABLE public.tbl_docentes_lineas OWNER TO admin;

--
-- Name: COLUMN tbl_docentes_lineas.tipo; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_docentes_lineas.tipo IS '1 = Principal
2 = Secundario';


--
-- Name: COLUMN tbl_docentes_lineas.id_estado_linea; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_docentes_lineas.id_estado_linea IS '0 = inactivo
1 = activo';


--
-- Name: tbl_docentes_lineas_historial; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_docentes_lineas_historial (
    id bigint NOT NULL,
    id_docente integer NOT NULL,
    id_sublinea_vri integer NOT NULL,
    id_estado_historial integer NOT NULL,
    fecha_registro timestamp without time zone NOT NULL,
    numero_resolucion text NOT NULL,
    comentario text,
    estado smallint
);


ALTER TABLE public.tbl_docentes_lineas_historial OWNER TO admin;

--
-- Name: COLUMN tbl_docentes_lineas_historial.id_estado_historial; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_docentes_lineas_historial.id_estado_historial IS '-1 = Renuncia
0 = Rechazado
1 = Disponible
2 = Aprobado';


--
-- Name: tbl_docentes_lineas_historial_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_docentes_lineas_historial_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_docentes_lineas_historial_id_seq OWNER TO admin;

--
-- Name: tbl_docentes_lineas_historial_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_docentes_lineas_historial_id_seq OWNED BY public.tbl_docentes_lineas_historial.id;


--
-- Name: tbl_docentes_lineas_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_docentes_lineas_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_docentes_lineas_id_seq OWNER TO admin;

--
-- Name: tbl_docentes_lineas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_docentes_lineas_id_seq OWNED BY public.tbl_docentes_lineas.id;


--
-- Name: tbl_estructura_academica; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_estructura_academica (
    id integer NOT NULL,
    nombre text,
    id_especialidad integer NOT NULL,
    id_sede integer NOT NULL,
    estado_ea smallint NOT NULL
);


ALTER TABLE public.tbl_estructura_academica OWNER TO admin;

--
-- Name: tbl_estudios; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_estudios (
    id integer NOT NULL,
    id_usuario integer NOT NULL,
    id_universidad integer NOT NULL,
    id_grado_academico integer NOT NULL,
    titulo_profesional text,
    especialidad character varying(255),
    fecha_emision date,
    resolucion character varying(100),
    fecha_resolucion date,
    flag_resolucion_nulidad character varying(10),
    nro_resolucion_nulidad character varying(100),
    fecha_resolucion_nulidad date,
    id_tipo_obtencion integer
);


ALTER TABLE public.tbl_estudios OWNER TO admin;

--
-- Name: TABLE tbl_estudios; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON TABLE public.tbl_estudios IS 'Almacena los grados y títulos obtenidos por los usuarios, basado en la información consultada de fuentes como SUNEDU.';


--
-- Name: COLUMN tbl_estudios.id_tipo_obtencion; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_estudios.id_tipo_obtencion IS 'Indica el método por el cual se obtuvo el registro del estudio (Manual, API SUNEDU, etc.). Referencia a dic_obtencion_studios.';


--
-- Name: tbl_estudios_id_seq1; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_estudios_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_estudios_id_seq1 OWNER TO admin;

--
-- Name: tbl_estudios_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_estudios_id_seq1 OWNED BY public.tbl_estudios.id;


--
-- Name: tbl_grado_docente; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_grado_docente (
    id integer NOT NULL,
    id_docente integer,
    antiguedad_categoria date,
    estado_tbl_grado_docente smallint,
    id_grado_academico integer,
    id_categoria integer
);


ALTER TABLE public.tbl_grado_docente OWNER TO admin;

--
-- Name: tbl_grado_docente_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_grado_docente_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_grado_docente_id_seq OWNER TO admin;

--
-- Name: tbl_grado_docente_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_grado_docente_id_seq OWNED BY public.tbl_grado_docente.id;


--
-- Name: tbl_integrantes; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_integrantes (
    id integer NOT NULL,
    id_tramite integer NOT NULL,
    id_tesista integer NOT NULL,
    tipo_integrante smallint NOT NULL,
    fecha_registro timestamp without time zone NOT NULL,
    estado_integrante smallint NOT NULL
);


ALTER TABLE public.tbl_integrantes OWNER TO admin;

--
-- Name: COLUMN tbl_integrantes.tipo_integrante; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_integrantes.tipo_integrante IS '1 = principal
2 = secundario';


--
-- Name: COLUMN tbl_integrantes.estado_integrante; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_integrantes.estado_integrante IS '0 = inactivo
1 = activo';


--
-- Name: tbl_integrantes_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_integrantes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_integrantes_id_seq OWNER TO admin;

--
-- Name: tbl_integrantes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_integrantes_id_seq OWNED BY public.tbl_integrantes.id;


--
-- Name: tbl_observaciones; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_observaciones (
    id integer NOT NULL,
    id_tramite bigint NOT NULL,
    id_etapa integer NOT NULL,
    id_usuario integer NOT NULL,
    id_rol integer NOT NULL,
    visto_bueno smallint NOT NULL,
    observacion text,
    fecha timestamp without time zone NOT NULL
);


ALTER TABLE public.tbl_observaciones OWNER TO admin;

--
-- Name: COLUMN tbl_observaciones.visto_bueno; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_observaciones.visto_bueno IS '1 = aceptado
0 = rechazado (para corregir)
-1 = rechazo definitivo';


--
-- Name: tbl_observaciones_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_observaciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_observaciones_id_seq OWNER TO admin;

--
-- Name: tbl_observaciones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_observaciones_id_seq OWNED BY public.tbl_observaciones.id;


--
-- Name: tbl_perfil_investigador; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_perfil_investigador (
    id integer NOT NULL,
    id_usuario integer NOT NULL,
    institucion text,
    afiliacion text,
    orcid text,
    ctivitae text,
    codigo_renacyt text,
    nivel_renacyt text,
    scopus_id text,
    wos_id text,
    alternativo_scopus_id text,
    estado_investigador bigint NOT NULL
);


ALTER TABLE public.tbl_perfil_investigador OWNER TO admin;

--
-- Name: tbl_perfil_investigador_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_perfil_investigador_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_perfil_investigador_id_seq OWNER TO admin;

--
-- Name: tbl_perfil_investigador_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_perfil_investigador_id_seq OWNED BY public.tbl_perfil_investigador.id;


--
-- Name: tbl_sublineas_vri; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_sublineas_vri (
    id integer NOT NULL,
    id_linea_universidad integer NOT NULL,
    nombre text NOT NULL,
    id_disciplina integer NOT NULL,
    id_carrera integer NOT NULL,
    fecha_registro timestamp without time zone NOT NULL,
    fecha_modificacion timestamp without time zone NOT NULL,
    estado_sublinea_vri smallint NOT NULL
);


ALTER TABLE public.tbl_sublineas_vri OWNER TO admin;

--
-- Name: COLUMN tbl_sublineas_vri.estado_sublinea_vri; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_sublineas_vri.estado_sublinea_vri IS '0 = inactivo
1 = activo';


--
-- Name: tbl_tesistas; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_tesistas (
    id integer NOT NULL,
    id_usuario integer NOT NULL,
    codigo_estudiante character varying(6) NOT NULL,
    id_estructura_academica integer NOT NULL,
    estado smallint NOT NULL,
    id_antiguo bigint
);


ALTER TABLE public.tbl_tesistas OWNER TO admin;

--
-- Name: tbl_tesistas_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_tesistas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_tesistas_id_seq OWNER TO admin;

--
-- Name: tbl_tesistas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_tesistas_id_seq OWNED BY public.tbl_tesistas.id;


--
-- Name: tbl_tramites; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_tramites (
    id bigint NOT NULL,
    id_antiguo integer,
    codigo_proyecto character varying(10) NOT NULL,
    id_etapa integer NOT NULL,
    id_sublinea_vri integer NOT NULL,
    id_modalidad integer NOT NULL,
    id_tipo_trabajo integer NOT NULL,
    id_denominacion integer NOT NULL,
    fecha_registro timestamp without time zone NOT NULL,
    estado_tramite smallint NOT NULL
);


ALTER TABLE public.tbl_tramites OWNER TO admin;

--
-- Name: COLUMN tbl_tramites.id_modalidad; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_tramites.id_modalidad IS 'ruta de las etapas que debe seguir el tramite segun el dic_etapas';


--
-- Name: COLUMN tbl_tramites.id_tipo_trabajo; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_tramites.id_tipo_trabajo IS 'tesis, articulos, examen de suficiencia, etc';


--
-- Name: COLUMN tbl_tramites.id_denominacion; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_tramites.id_denominacion IS 'Denominacion del grado actual';


--
-- Name: COLUMN tbl_tramites.estado_tramite; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_tramites.estado_tramite IS '0 = invalido
1 = valido';


--
-- Name: tbl_tramites_historial; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_tramites_historial (
    id bigint NOT NULL,
    id_tramite bigint NOT NULL,
    id_etapa integer NOT NULL,
    estado_tramite_historial smallint NOT NULL,
    fecha_cambio timestamp without time zone NOT NULL,
    comentario text NOT NULL
);


ALTER TABLE public.tbl_tramites_historial OWNER TO admin;

--
-- Name: COLUMN tbl_tramites_historial.estado_tramite_historial; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_tramites_historial.estado_tramite_historial IS 'que estado tuvo en ese momento 0 si estaba inactivo en esta etapa o 1 si estaba activo
';


--
-- Name: tbl_tramites_historial_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_tramites_historial_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_tramites_historial_id_seq OWNER TO admin;

--
-- Name: tbl_tramites_historial_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_tramites_historial_id_seq OWNED BY public.tbl_tramites_historial.id;


--
-- Name: tbl_tramites_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_tramites_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_tramites_id_seq OWNER TO admin;

--
-- Name: tbl_tramites_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_tramites_id_seq OWNED BY public.tbl_tramites.id;


--
-- Name: tbl_tramites_metadatos; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_tramites_metadatos (
    id integer NOT NULL,
    id_tramite bigint NOT NULL,
    titulo text NOT NULL,
    abstract text NOT NULL,
    keywords text NOT NULL,
    conclusiones text NOT NULL,
    presupuesto numeric NOT NULL,
    id_etapa integer NOT NULL,
    fecha timestamp without time zone NOT NULL,
    estado_tm smallint NOT NULL
);


ALTER TABLE public.tbl_tramites_metadatos OWNER TO admin;

--
-- Name: tbl_tramites_metadatos_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_tramites_metadatos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_tramites_metadatos_id_seq OWNER TO admin;

--
-- Name: tbl_tramites_metadatos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_tramites_metadatos_id_seq OWNED BY public.tbl_tramites_metadatos.id;


--
-- Name: tbl_tramitesdet; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_tramitesdet (
    id bigint NOT NULL,
    id_tramite bigint NOT NULL,
    id_docente integer NOT NULL,
    id_etapa integer NOT NULL,
    id_visto_bueno integer NOT NULL,
    fecha_registro timestamp without time zone NOT NULL,
    detalle text,
    id_orden integer,
    estado smallint
);


ALTER TABLE public.tbl_tramitesdet OWNER TO admin;

--
-- Name: tbl_tramitesdet_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_tramitesdet_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_tramitesdet_id_seq OWNER TO admin;

--
-- Name: tbl_tramitesdet_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_tramitesdet_id_seq OWNED BY public.tbl_tramitesdet.id;


--
-- Name: tbl_tramitesdoc; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_tramitesdoc (
    id integer NOT NULL,
    id_tramite bigint NOT NULL,
    id_etapa integer NOT NULL,
    id_tramites_metadatos integer NOT NULL,
    fecha_registro timestamp without time zone NOT NULL
);


ALTER TABLE public.tbl_tramitesdoc OWNER TO admin;

--
-- Name: tbl_tramitesdoc_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_tramitesdoc_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_tramitesdoc_id_seq OWNER TO admin;

--
-- Name: tbl_tramitesdoc_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_tramitesdoc_id_seq OWNED BY public.tbl_tramitesdoc.id;


--
-- Name: tbl_universidades_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_universidades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_universidades_id_seq OWNER TO admin;

--
-- Name: tbl_universidades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_universidades_id_seq OWNED BY public.dic_universidades.id;


--
-- Name: tbl_usuarios; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_usuarios (
    id integer NOT NULL,
    nombres character varying(90),
    apellidos character varying(90),
    tipo_doc_identidad character varying(30),
    num_doc_identidad character varying(12) NOT NULL,
    correo character varying(320) NOT NULL,
    correo_google character varying(320),
    telefono character varying(20),
    pais character varying(3),
    direccion text,
    sexo character varying(10),
    fecha_nacimiento date,
    contrasenia character varying(255),
    ruta_foto character varying(500),
    estado smallint
);


ALTER TABLE public.tbl_usuarios OWNER TO admin;

--
-- Name: COLUMN tbl_usuarios.tipo_doc_identidad; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.tbl_usuarios.tipo_doc_identidad IS '(''DNI'', ''CARNET DE EXTRANJERIA'', ''PASAPORTE'')';


--
-- Name: tbl_usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_usuarios_id_seq OWNER TO admin;

--
-- Name: tbl_usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_usuarios_id_seq OWNED BY public.tbl_usuarios.id;


--
-- Name: tbl_usuarios_servicios; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.tbl_usuarios_servicios (
    id integer NOT NULL,
    id_usuario integer NOT NULL,
    id_servicio integer NOT NULL,
    fecha_asignacion timestamp without time zone NOT NULL,
    estado smallint NOT NULL
);


ALTER TABLE public.tbl_usuarios_servicios OWNER TO admin;

--
-- Name: tbl_usuarios_servicios_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.tbl_usuarios_servicios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tbl_usuarios_servicios_id_seq OWNER TO admin;

--
-- Name: tbl_usuarios_servicios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.tbl_usuarios_servicios_id_seq OWNED BY public.tbl_usuarios_servicios.id;


--
-- Name: dic_categoria id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_categoria ALTER COLUMN id SET DEFAULT nextval('public.dic_categoria_id_seq'::regclass);


--
-- Name: dic_grados_academicos id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_grados_academicos ALTER COLUMN id SET DEFAULT nextval('public.dic_grados_academicos_id_seq'::regclass);


--
-- Name: dic_modalidades id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_modalidades ALTER COLUMN id SET DEFAULT nextval('public.dic_modalidades_id_seq'::regclass);


--
-- Name: dic_nivel_admin id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_nivel_admin ALTER COLUMN id SET DEFAULT nextval('public.dic_nivel_admin_id_seq'::regclass);


--
-- Name: dic_nivel_coordinador id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_nivel_coordinador ALTER COLUMN id SET DEFAULT nextval('public.dic_nivel_coordinador_id_seq'::regclass);


--
-- Name: dic_obtencion_studios id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_obtencion_studios ALTER COLUMN id SET DEFAULT nextval('public.dic_obtencion_studios_id_seq'::regclass);


--
-- Name: dic_orden_jurado id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_orden_jurado ALTER COLUMN id SET DEFAULT nextval('public.dic_orden_jurado_id_seq'::regclass);


--
-- Name: dic_sedes id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_sedes ALTER COLUMN id SET DEFAULT nextval('public.dic_sedes_id_seq'::regclass);


--
-- Name: dic_servicios id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_servicios ALTER COLUMN id SET DEFAULT nextval('public.dic_servicios_id_seq'::regclass);


--
-- Name: dic_tipo_trabajos id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_tipo_trabajos ALTER COLUMN id SET DEFAULT nextval('public.dic_tipo_trabajos_id_seq'::regclass);


--
-- Name: dic_tipoevento_jurado id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_tipoevento_jurado ALTER COLUMN id SET DEFAULT nextval('public.dic_tipoevento_jurado_id_seq'::regclass);


--
-- Name: dic_universidades id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_universidades ALTER COLUMN id SET DEFAULT nextval('public.tbl_universidades_id_seq'::regclass);


--
-- Name: log_acciones id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.log_acciones ALTER COLUMN id SET DEFAULT nextval('public.log_acciones_id_seq'::regclass);


--
-- Name: tbl_admins id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_admins ALTER COLUMN id SET DEFAULT nextval('public.tbl_admins_id_seq'::regclass);


--
-- Name: tbl_admins_historial id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_admins_historial ALTER COLUMN id SET DEFAULT nextval('public.tbl_admins_historial_id_seq'::regclass);


--
-- Name: tbl_archivos_tramites id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_archivos_tramites ALTER COLUMN id SET DEFAULT nextval('public.tbl_archivos_tramites_id_seq'::regclass);


--
-- Name: tbl_asignacion_jurado id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_asignacion_jurado ALTER COLUMN id SET DEFAULT nextval('public.tbl_conformacion_jurado_historial_id_seq'::regclass);


--
-- Name: tbl_coasesores id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coasesores ALTER COLUMN id SET DEFAULT nextval('public.tbl_coasesores_id_seq'::regclass);


--
-- Name: tbl_coasesores_historial id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coasesores_historial ALTER COLUMN id SET DEFAULT nextval('public.tbl_coasesores_historial_id_seq'::regclass);


--
-- Name: tbl_conformacion_jurados id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_conformacion_jurados ALTER COLUMN id SET DEFAULT nextval('public.tbl_conformacion_jurados_id_seq'::regclass);


--
-- Name: tbl_coordinador_carrera id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coordinador_carrera ALTER COLUMN id SET DEFAULT nextval('public.tbl_coordinador_carrera_id_seq'::regclass);


--
-- Name: tbl_coordinadores id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coordinadores ALTER COLUMN id SET DEFAULT nextval('public.tbl_coordinadores_id_seq'::regclass);


--
-- Name: tbl_coordinadores_historial id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coordinadores_historial ALTER COLUMN id SET DEFAULT nextval('public.tbl_coordinadores_historial_id_seq'::regclass);


--
-- Name: tbl_correcciones_jurados id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_correcciones_jurados ALTER COLUMN id SET DEFAULT nextval('public.tbl_correcciones_jurados_id_seq'::regclass);


--
-- Name: tbl_dictamenes_info id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_dictamenes_info ALTER COLUMN id SET DEFAULT nextval('public.tbl_dictamenes_info_id_seq'::regclass);


--
-- Name: tbl_docente_categoria_historial id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_docente_categoria_historial ALTER COLUMN id SET DEFAULT nextval('public.tbl_docente_categoria_historial_id_seq'::regclass);


--
-- Name: tbl_docentes id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_docentes ALTER COLUMN id SET DEFAULT nextval('public.tbl_docentes_id_seq'::regclass);


--
-- Name: tbl_docentes_lineas id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_docentes_lineas ALTER COLUMN id SET DEFAULT nextval('public.tbl_docentes_lineas_id_seq'::regclass);


--
-- Name: tbl_docentes_lineas_historial id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_docentes_lineas_historial ALTER COLUMN id SET DEFAULT nextval('public.tbl_docentes_lineas_historial_id_seq'::regclass);


--
-- Name: tbl_estudios id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_estudios ALTER COLUMN id SET DEFAULT nextval('public.tbl_estudios_id_seq1'::regclass);


--
-- Name: tbl_grado_docente id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_grado_docente ALTER COLUMN id SET DEFAULT nextval('public.tbl_grado_docente_id_seq'::regclass);


--
-- Name: tbl_integrantes id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_integrantes ALTER COLUMN id SET DEFAULT nextval('public.tbl_integrantes_id_seq'::regclass);


--
-- Name: tbl_observaciones id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_observaciones ALTER COLUMN id SET DEFAULT nextval('public.tbl_observaciones_id_seq'::regclass);


--
-- Name: tbl_perfil_investigador id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_perfil_investigador ALTER COLUMN id SET DEFAULT nextval('public.tbl_perfil_investigador_id_seq'::regclass);


--
-- Name: tbl_tesistas id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tesistas ALTER COLUMN id SET DEFAULT nextval('public.tbl_tesistas_id_seq'::regclass);


--
-- Name: tbl_tramites id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramites ALTER COLUMN id SET DEFAULT nextval('public.tbl_tramites_id_seq'::regclass);


--
-- Name: tbl_tramites_historial id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramites_historial ALTER COLUMN id SET DEFAULT nextval('public.tbl_tramites_historial_id_seq'::regclass);


--
-- Name: tbl_tramites_metadatos id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramites_metadatos ALTER COLUMN id SET DEFAULT nextval('public.tbl_tramites_metadatos_id_seq'::regclass);


--
-- Name: tbl_tramitesdet id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramitesdet ALTER COLUMN id SET DEFAULT nextval('public.tbl_tramitesdet_id_seq'::regclass);


--
-- Name: tbl_tramitesdoc id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramitesdoc ALTER COLUMN id SET DEFAULT nextval('public.tbl_tramitesdoc_id_seq'::regclass);


--
-- Name: tbl_usuarios id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_usuarios ALTER COLUMN id SET DEFAULT nextval('public.tbl_usuarios_id_seq'::regclass);


--
-- Name: tbl_usuarios_servicios id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_usuarios_servicios ALTER COLUMN id SET DEFAULT nextval('public.tbl_usuarios_servicios_id_seq'::regclass);


--
-- Name: dic_acciones dic_acciones_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_acciones
    ADD CONSTRAINT dic_acciones_pkey PRIMARY KEY (id);


--
-- Name: dic_areas_ocde dic_areas_ocde_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_areas_ocde
    ADD CONSTRAINT dic_areas_ocde_pkey PRIMARY KEY (id);


--
-- Name: dic_carreras dic_carreras_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_carreras
    ADD CONSTRAINT dic_carreras_pkey PRIMARY KEY (id);


--
-- Name: dic_categoria dic_categoria_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_categoria
    ADD CONSTRAINT dic_categoria_pkey PRIMARY KEY (id);


--
-- Name: dic_denominaciones dic_denominaciones_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_denominaciones
    ADD CONSTRAINT dic_denominaciones_pkey PRIMARY KEY (id);


--
-- Name: dic_disciplinas dic_disciplinas_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_disciplinas
    ADD CONSTRAINT dic_disciplinas_pkey PRIMARY KEY (id);


--
-- Name: dic_especialidades dic_especialidades_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_especialidades
    ADD CONSTRAINT dic_especialidades_pkey PRIMARY KEY (id);


--
-- Name: dic_etapas dic_etapas_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_etapas
    ADD CONSTRAINT dic_etapas_pkey PRIMARY KEY (id);


--
-- Name: dic_facultades dic_facultades_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_facultades
    ADD CONSTRAINT dic_facultades_pkey PRIMARY KEY (id);


--
-- Name: dic_grados_academicos dic_grados_academicos_abreviatura_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_grados_academicos
    ADD CONSTRAINT dic_grados_academicos_abreviatura_key UNIQUE (abreviatura);


--
-- Name: dic_grados_academicos dic_grados_academicos_nombre_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_grados_academicos
    ADD CONSTRAINT dic_grados_academicos_nombre_key UNIQUE (nombre);


--
-- Name: dic_grados_academicos dic_grados_academicos_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_grados_academicos
    ADD CONSTRAINT dic_grados_academicos_pkey PRIMARY KEY (id);


--
-- Name: dic_lineas_universidad dic_lineas_universidad_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_lineas_universidad
    ADD CONSTRAINT dic_lineas_universidad_pkey PRIMARY KEY (id);


--
-- Name: dic_modalidades dic_modalidades_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_modalidades
    ADD CONSTRAINT dic_modalidades_pkey PRIMARY KEY (id);


--
-- Name: dic_nivel_admin dic_nivel_admin_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_nivel_admin
    ADD CONSTRAINT dic_nivel_admin_pkey PRIMARY KEY (id);


--
-- Name: dic_nivel_coordinador dic_nivel_coordinador_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_nivel_coordinador
    ADD CONSTRAINT dic_nivel_coordinador_pkey PRIMARY KEY (id);


--
-- Name: dic_obtencion_studios dic_obtencion_studios_nombre_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_obtencion_studios
    ADD CONSTRAINT dic_obtencion_studios_nombre_key UNIQUE (nombre);


--
-- Name: dic_obtencion_studios dic_obtencion_studios_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_obtencion_studios
    ADD CONSTRAINT dic_obtencion_studios_pkey PRIMARY KEY (id);


--
-- Name: dic_orden_jurado dic_orden_jurado_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_orden_jurado
    ADD CONSTRAINT dic_orden_jurado_pkey PRIMARY KEY (id);


--
-- Name: dic_sedes dic_sedes_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_sedes
    ADD CONSTRAINT dic_sedes_pkey PRIMARY KEY (id);


--
-- Name: dic_servicios dic_servicios_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_servicios
    ADD CONSTRAINT dic_servicios_pkey PRIMARY KEY (id);


--
-- Name: dic_subareas_ocde dic_subareas_ocde_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_subareas_ocde
    ADD CONSTRAINT dic_subareas_ocde_pkey PRIMARY KEY (id);


--
-- Name: dic_tipo_archivo dic_tipo_archivo_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_tipo_archivo
    ADD CONSTRAINT dic_tipo_archivo_pkey PRIMARY KEY (id);


--
-- Name: dic_tipo_trabajos dic_tipo_trabajos_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_tipo_trabajos
    ADD CONSTRAINT dic_tipo_trabajos_pkey PRIMARY KEY (id);


--
-- Name: dic_tipoevento_jurado dic_tipoevento_jurado_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_tipoevento_jurado
    ADD CONSTRAINT dic_tipoevento_jurado_pkey PRIMARY KEY (id);


--
-- Name: dic_visto_bueno dic_visto_bueno_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_visto_bueno
    ADD CONSTRAINT dic_visto_bueno_pkey PRIMARY KEY (id);


--
-- Name: log_acciones log_acciones_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.log_acciones
    ADD CONSTRAINT log_acciones_pkey PRIMARY KEY (id);


--
-- Name: tbl_admins_historial tbl_admins_historial_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_admins_historial
    ADD CONSTRAINT tbl_admins_historial_pkey PRIMARY KEY (id);


--
-- Name: tbl_admins tbl_admins_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_admins
    ADD CONSTRAINT tbl_admins_pkey PRIMARY KEY (id);


--
-- Name: tbl_archivos_tramites tbl_archivos_tramites_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_archivos_tramites
    ADD CONSTRAINT tbl_archivos_tramites_pkey PRIMARY KEY (id);


--
-- Name: tbl_coasesores_historial tbl_coasesores_historial_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coasesores_historial
    ADD CONSTRAINT tbl_coasesores_historial_pkey PRIMARY KEY (id);


--
-- Name: tbl_coasesores tbl_coasesores_id_investigador_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coasesores
    ADD CONSTRAINT tbl_coasesores_id_investigador_key UNIQUE (id_investigador);


--
-- Name: tbl_coasesores tbl_coasesores_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coasesores
    ADD CONSTRAINT tbl_coasesores_pkey PRIMARY KEY (id);


--
-- Name: tbl_asignacion_jurado tbl_conformacion_jurado_historial_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_asignacion_jurado
    ADD CONSTRAINT tbl_conformacion_jurado_historial_pkey PRIMARY KEY (id);


--
-- Name: tbl_conformacion_jurados tbl_conformacion_jurados_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_conformacion_jurados
    ADD CONSTRAINT tbl_conformacion_jurados_pkey PRIMARY KEY (id);


--
-- Name: tbl_coordinador_carrera tbl_coordinador_carrera_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coordinador_carrera
    ADD CONSTRAINT tbl_coordinador_carrera_pkey PRIMARY KEY (id);


--
-- Name: tbl_coordinadores_historial tbl_coordinadores_historial_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coordinadores_historial
    ADD CONSTRAINT tbl_coordinadores_historial_pkey PRIMARY KEY (id);


--
-- Name: tbl_coordinadores tbl_coordinadores_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coordinadores
    ADD CONSTRAINT tbl_coordinadores_pkey PRIMARY KEY (id);


--
-- Name: tbl_correcciones_jurados tbl_correcciones_jurados_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_correcciones_jurados
    ADD CONSTRAINT tbl_correcciones_jurados_pkey PRIMARY KEY (id);


--
-- Name: tbl_dictamenes_info tbl_dictamenes_info_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_dictamenes_info
    ADD CONSTRAINT tbl_dictamenes_info_pkey PRIMARY KEY (id);


--
-- Name: tbl_docente_categoria_historial tbl_docente_categoria_historial_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_docente_categoria_historial
    ADD CONSTRAINT tbl_docente_categoria_historial_pkey PRIMARY KEY (id);


--
-- Name: tbl_docentes_lineas_historial tbl_docentes_lineas_historial_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_docentes_lineas_historial
    ADD CONSTRAINT tbl_docentes_lineas_historial_pkey PRIMARY KEY (id);


--
-- Name: tbl_docentes_lineas tbl_docentes_lineas_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_docentes_lineas
    ADD CONSTRAINT tbl_docentes_lineas_pkey PRIMARY KEY (id);


--
-- Name: tbl_docentes tbl_docentes_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_docentes
    ADD CONSTRAINT tbl_docentes_pkey PRIMARY KEY (id);


--
-- Name: tbl_estructura_academica tbl_estructura_academica_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_estructura_academica
    ADD CONSTRAINT tbl_estructura_academica_pkey PRIMARY KEY (id);


--
-- Name: tbl_estudios tbl_estudios_pkey1; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_estudios
    ADD CONSTRAINT tbl_estudios_pkey1 PRIMARY KEY (id);


--
-- Name: tbl_grado_docente tbl_grado_docente_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_grado_docente
    ADD CONSTRAINT tbl_grado_docente_pkey PRIMARY KEY (id);


--
-- Name: tbl_integrantes tbl_integrantes_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_integrantes
    ADD CONSTRAINT tbl_integrantes_pkey PRIMARY KEY (id);


--
-- Name: tbl_observaciones tbl_observaciones_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_observaciones
    ADD CONSTRAINT tbl_observaciones_pkey PRIMARY KEY (id);


--
-- Name: tbl_perfil_investigador tbl_perfil_investigador_id_usuario_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_perfil_investigador
    ADD CONSTRAINT tbl_perfil_investigador_id_usuario_key UNIQUE (id_usuario);


--
-- Name: tbl_perfil_investigador tbl_perfil_investigador_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_perfil_investigador
    ADD CONSTRAINT tbl_perfil_investigador_pkey PRIMARY KEY (id);


--
-- Name: tbl_sublineas_vri tbl_sublineas_vri_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_sublineas_vri
    ADD CONSTRAINT tbl_sublineas_vri_pkey PRIMARY KEY (id);


--
-- Name: tbl_tesistas tbl_tesistas_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tesistas
    ADD CONSTRAINT tbl_tesistas_pkey PRIMARY KEY (id);


--
-- Name: tbl_tramites_historial tbl_tramites_historial_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramites_historial
    ADD CONSTRAINT tbl_tramites_historial_pkey PRIMARY KEY (id);


--
-- Name: tbl_tramites_metadatos tbl_tramites_metadatos_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramites_metadatos
    ADD CONSTRAINT tbl_tramites_metadatos_pkey PRIMARY KEY (id);


--
-- Name: tbl_tramites tbl_tramites_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramites
    ADD CONSTRAINT tbl_tramites_pkey PRIMARY KEY (id);


--
-- Name: tbl_tramitesdet tbl_tramitesdet_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramitesdet
    ADD CONSTRAINT tbl_tramitesdet_pkey PRIMARY KEY (id);


--
-- Name: tbl_tramitesdoc tbl_tramitesdoc_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramitesdoc
    ADD CONSTRAINT tbl_tramitesdoc_pkey PRIMARY KEY (id);


--
-- Name: dic_universidades tbl_universidades_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_universidades
    ADD CONSTRAINT tbl_universidades_pkey PRIMARY KEY (id);


--
-- Name: tbl_usuarios tbl_usuarios_correo_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_usuarios
    ADD CONSTRAINT tbl_usuarios_correo_key UNIQUE (correo);


--
-- Name: tbl_usuarios tbl_usuarios_num_doc_identidad_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_usuarios
    ADD CONSTRAINT tbl_usuarios_num_doc_identidad_key UNIQUE (num_doc_identidad);


--
-- Name: tbl_usuarios tbl_usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_usuarios
    ADD CONSTRAINT tbl_usuarios_pkey PRIMARY KEY (id);


--
-- Name: tbl_usuarios_servicios tbl_usuarios_servicios_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_usuarios_servicios
    ADD CONSTRAINT tbl_usuarios_servicios_pkey PRIMARY KEY (id);


--
-- Name: tbl_usuarios_servicios unique_usuario_servicio; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_usuarios_servicios
    ADD CONSTRAINT unique_usuario_servicio UNIQUE (id_usuario, id_servicio);


--
-- Name: dic_carreras_id_facultad; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX dic_carreras_id_facultad ON public.dic_carreras USING btree (id_facultad);


--
-- Name: dic_denominaciones_id_especialidad; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX dic_denominaciones_id_especialidad ON public.dic_denominaciones USING btree (id_especialidad);


--
-- Name: log_acciones_id_accion; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX log_acciones_id_accion ON public.log_acciones USING btree (id_accion);


--
-- Name: log_acciones_id_etapa; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX log_acciones_id_etapa ON public.log_acciones USING btree (id_etapa);


--
-- Name: log_acciones_id_tramite; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX log_acciones_id_tramite ON public.log_acciones USING btree (id_tramite);


--
-- Name: log_acciones_id_usuario; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX log_acciones_id_usuario ON public.log_acciones USING btree (id_usuario);


--
-- Name: tbl_admins_estado_admin; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_admins_estado_admin ON public.tbl_admins USING btree (estado_admin);


--
-- Name: tbl_admins_historial_estado_admin; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_admins_historial_estado_admin ON public.tbl_admins_historial USING btree (estado_admin);


--
-- Name: tbl_admins_historial_id_admin; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_admins_historial_id_admin ON public.tbl_admins_historial USING btree (id_admin);


--
-- Name: tbl_admins_id_usuario; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_admins_id_usuario ON public.tbl_admins USING btree (id_usuario);


--
-- Name: tbl_admins_nivel_admin; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_admins_nivel_admin ON public.tbl_admins USING btree (nivel_admin);


--
-- Name: tbl_archivos_tramites_bucket; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_archivos_tramites_bucket ON public.tbl_archivos_tramites USING btree (bucket);


--
-- Name: tbl_archivos_tramites_fecha; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_archivos_tramites_fecha ON public.tbl_archivos_tramites USING btree (fecha);


--
-- Name: tbl_archivos_tramites_id_tipo_archivo; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_archivos_tramites_id_tipo_archivo ON public.tbl_archivos_tramites USING btree (id_tipo_archivo);


--
-- Name: tbl_archivos_tramites_id_tramite; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_archivos_tramites_id_tramite ON public.tbl_archivos_tramites USING btree (id_tramite);


--
-- Name: tbl_archivos_tramites_id_tramite_metadato; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_archivos_tramites_id_tramite_metadato ON public.tbl_archivos_tramites USING btree (id_tramites_metadatos);


--
-- Name: tbl_archivos_tramites_storage; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_archivos_tramites_storage ON public.tbl_archivos_tramites USING btree (storage);


--
-- Name: tbl_archivos_tramites_tramite_estado; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_archivos_tramites_tramite_estado ON public.tbl_archivos_tramites USING btree (id_tramite, estado_archivo);


--
-- Name: tbl_archivos_tramites_tramite_etapa; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_archivos_tramites_tramite_etapa ON public.tbl_archivos_tramites USING btree (id_tramite, id_etapa);


--
-- Name: tbl_archivos_tramites_tramite_metadato; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_archivos_tramites_tramite_metadato ON public.tbl_archivos_tramites USING btree (id_tramite, id_tramites_metadatos);


--
-- Name: tbl_coasesores_estado_coasesor; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_coasesores_estado_coasesor ON public.tbl_coasesores USING btree (estado_coasesor);


--
-- Name: tbl_coasesores_historial_estado_coasesor; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_coasesores_historial_estado_coasesor ON public.tbl_coasesores_historial USING btree (estado_coasesor);


--
-- Name: tbl_coasesores_historial_id_coasesor; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_coasesores_historial_id_coasesor ON public.tbl_coasesores_historial USING btree (id_coasesor);


--
-- Name: tbl_coasesores_id_investigador; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_coasesores_id_investigador ON public.tbl_coasesores USING btree (id_investigador);


--
-- Name: tbl_coordinadores_historial_id_coordinador; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_coordinadores_historial_id_coordinador ON public.tbl_coordinadores_historial USING btree (id_coordinador);


--
-- Name: tbl_coordinadores_id_usuario; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_coordinadores_id_usuario ON public.tbl_coordinadores USING btree (id_usuario);


--
-- Name: tbl_docentes_codigo_airhs; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_docentes_codigo_airhs ON public.tbl_docentes USING btree (codigo_airhs);


--
-- Name: tbl_docentes_id_especialidad; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_docentes_id_especialidad ON public.tbl_docentes USING btree (id_especialidad);


--
-- Name: tbl_docentes_id_usuario; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_docentes_id_usuario ON public.tbl_docentes USING btree (id_usuario);


--
-- Name: tbl_docentes_index_5; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_docentes_index_5 ON public.tbl_docentes USING btree (id_categoria);


--
-- Name: tbl_docentes_lineas_historial_id_docente; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_docentes_lineas_historial_id_docente ON public.tbl_docentes_lineas_historial USING btree (id_docente);


--
-- Name: tbl_docentes_lineas_historial_id_sublinea_vri; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_docentes_lineas_historial_id_sublinea_vri ON public.tbl_docentes_lineas_historial USING btree (id_sublinea_vri);


--
-- Name: tbl_docentes_lineas_id_docente; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_docentes_lineas_id_docente ON public.tbl_docentes_lineas USING btree (id_docente);


--
-- Name: tbl_docentes_lineas_id_estado_linea; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_docentes_lineas_id_estado_linea ON public.tbl_docentes_lineas USING btree (id_estado_linea);


--
-- Name: tbl_docentes_lineas_id_sublinea_vri; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_docentes_lineas_id_sublinea_vri ON public.tbl_docentes_lineas USING btree (id_sublinea_vri);


--
-- Name: tbl_integrantes_id_tesista; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_integrantes_id_tesista ON public.tbl_integrantes USING btree (id_tesista);


--
-- Name: tbl_integrantes_id_tramite; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_integrantes_id_tramite ON public.tbl_integrantes USING btree (id_tramite);


--
-- Name: tbl_integrantes_tipo_integrante; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_integrantes_tipo_integrante ON public.tbl_integrantes USING btree (tipo_integrante);


--
-- Name: tbl_observaciones_fecha; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_observaciones_fecha ON public.tbl_observaciones USING btree (fecha);


--
-- Name: tbl_observaciones_id_etapa; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_observaciones_id_etapa ON public.tbl_observaciones USING btree (id_etapa);


--
-- Name: tbl_observaciones_id_rol; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_observaciones_id_rol ON public.tbl_observaciones USING btree (id_rol);


--
-- Name: tbl_observaciones_id_tramite; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_observaciones_id_tramite ON public.tbl_observaciones USING btree (id_tramite);


--
-- Name: tbl_observaciones_id_usuario; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_observaciones_id_usuario ON public.tbl_observaciones USING btree (id_usuario);


--
-- Name: tbl_observaciones_tramite_vb; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_observaciones_tramite_vb ON public.tbl_observaciones USING btree (id_tramite, visto_bueno);


--
-- Name: tbl_perfil_investigador_estado_investigador; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_perfil_investigador_estado_investigador ON public.tbl_perfil_investigador USING btree (estado_investigador);


--
-- Name: tbl_perfil_investigador_id_usuario; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_perfil_investigador_id_usuario ON public.tbl_perfil_investigador USING btree (id_usuario);


--
-- Name: tbl_sublineas_vri_id_carrera; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_sublineas_vri_id_carrera ON public.tbl_sublineas_vri USING btree (id_carrera);


--
-- Name: tbl_sublineas_vri_id_disciplina; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_sublineas_vri_id_disciplina ON public.tbl_sublineas_vri USING btree (id_disciplina);


--
-- Name: tbl_sublineas_vri_id_linea_universidad; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_sublineas_vri_id_linea_universidad ON public.tbl_sublineas_vri USING btree (id_linea_universidad);


--
-- Name: tbl_tesistas_codigo_estudiante; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tesistas_codigo_estudiante ON public.tbl_tesistas USING btree (codigo_estudiante);


--
-- Name: tbl_tesistas_id_est_ac; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tesistas_id_est_ac ON public.tbl_tesistas USING btree (id_estructura_academica);


--
-- Name: tbl_tesistas_id_usuario; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tesistas_id_usuario ON public.tbl_tesistas USING btree (id_usuario);


--
-- Name: tbl_tramites_codigo_proyecto; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramites_codigo_proyecto ON public.tbl_tramites USING btree (codigo_proyecto);


--
-- Name: tbl_tramites_fecha_registro; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramites_fecha_registro ON public.tbl_tramites USING btree (fecha_registro);


--
-- Name: tbl_tramites_historial_id_etapa; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramites_historial_id_etapa ON public.tbl_tramites_historial USING btree (id_etapa);


--
-- Name: tbl_tramites_historial_id_tramite; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramites_historial_id_tramite ON public.tbl_tramites_historial USING btree (id_tramite);


--
-- Name: tbl_tramites_id_denominacion; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramites_id_denominacion ON public.tbl_tramites USING btree (id_denominacion);


--
-- Name: tbl_tramites_id_etapa; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramites_id_etapa ON public.tbl_tramites USING btree (id_etapa);


--
-- Name: tbl_tramites_id_integrantes; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramites_id_integrantes ON public.tbl_tramites USING btree (id_antiguo);


--
-- Name: tbl_tramites_id_sublinea_vri; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramites_id_sublinea_vri ON public.tbl_tramites USING btree (id_sublinea_vri);


--
-- Name: tbl_tramites_id_tipo_trabajo; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramites_id_tipo_trabajo ON public.tbl_tramites USING btree (id_tipo_trabajo);


--
-- Name: tbl_tramites_metadatos_fecha; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramites_metadatos_fecha ON public.tbl_tramites_metadatos USING btree (fecha);


--
-- Name: tbl_tramites_metadatos_id_tramite; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramites_metadatos_id_tramite ON public.tbl_tramites_metadatos USING btree (id_tramite);


--
-- Name: tbl_tramites_metadatos_tramite_estado; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramites_metadatos_tramite_estado ON public.tbl_tramites_metadatos USING btree (id_tramite, estado_tm);


--
-- Name: tbl_tramites_metadatos_tramite_etapa; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramites_metadatos_tramite_etapa ON public.tbl_tramites_metadatos USING btree (id_tramite, id_etapa);


--
-- Name: tbl_tramites_metadatos_tramite_fecha; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramites_metadatos_tramite_fecha ON public.tbl_tramites_metadatos USING btree (id_tramite, fecha);


--
-- Name: tbl_tramitesdet_id_docente; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramitesdet_id_docente ON public.tbl_tramitesdet USING btree (id_docente);


--
-- Name: tbl_tramitesdet_id_tramite; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramitesdet_id_tramite ON public.tbl_tramitesdet USING btree (id_tramite);


--
-- Name: tbl_tramitesdet_id_visto_bueno; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramitesdet_id_visto_bueno ON public.tbl_tramitesdet USING btree (id_visto_bueno);


--
-- Name: tbl_tramitesdoc_id_tramite; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramitesdoc_id_tramite ON public.tbl_tramitesdoc USING btree (id_tramite);


--
-- Name: tbl_tramitesdoc_tramite_metadato; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_tramitesdoc_tramite_metadato ON public.tbl_tramitesdoc USING btree (id_tramite, id_tramites_metadatos);


--
-- Name: tbl_usuarios_num_doc_identidad; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_usuarios_num_doc_identidad ON public.tbl_usuarios USING btree (num_doc_identidad);


--
-- Name: tbl_usuarios_servicios_id_servicio; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_usuarios_servicios_id_servicio ON public.tbl_usuarios_servicios USING btree (id_servicio);


--
-- Name: tbl_usuarios_servicios_id_usuario; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX tbl_usuarios_servicios_id_usuario ON public.tbl_usuarios_servicios USING btree (id_usuario);


--
-- Name: tbl_coordinador_carrera fk_carrera; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coordinador_carrera
    ADD CONSTRAINT fk_carrera FOREIGN KEY (id_carrera) REFERENCES public.dic_carreras(id);


--
-- Name: tbl_docente_categoria_historial fk_categoria; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_docente_categoria_historial
    ADD CONSTRAINT fk_categoria FOREIGN KEY (id_categoria) REFERENCES public.dic_categoria(id);


--
-- Name: tbl_grado_docente fk_categoria; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_grado_docente
    ADD CONSTRAINT fk_categoria FOREIGN KEY (id_categoria) REFERENCES public.dic_categoria(id);


--
-- Name: tbl_coasesores_historial fk_coasesores_historial_id_accion; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coasesores_historial
    ADD CONSTRAINT fk_coasesores_historial_id_accion FOREIGN KEY (id_accion) REFERENCES public.dic_acciones(id);


--
-- Name: tbl_conformacion_jurados fk_conf_asignacion; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_conformacion_jurados
    ADD CONSTRAINT fk_conf_asignacion FOREIGN KEY (id_asignacion) REFERENCES public.tbl_asignacion_jurado(id);


--
-- Name: tbl_conformacion_jurados fk_conf_docente; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_conformacion_jurados
    ADD CONSTRAINT fk_conf_docente FOREIGN KEY (id_docente) REFERENCES public.tbl_docentes(id);


--
-- Name: tbl_conformacion_jurados fk_conf_etapa; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_conformacion_jurados
    ADD CONSTRAINT fk_conf_etapa FOREIGN KEY (id_etapa) REFERENCES public.dic_etapas(id);


--
-- Name: tbl_conformacion_jurados fk_conf_orden; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_conformacion_jurados
    ADD CONSTRAINT fk_conf_orden FOREIGN KEY (id_orden) REFERENCES public.dic_orden_jurado(id);


--
-- Name: tbl_conformacion_jurados fk_conf_tramite; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_conformacion_jurados
    ADD CONSTRAINT fk_conf_tramite FOREIGN KEY (id_tramite) REFERENCES public.tbl_tramites(id);


--
-- Name: tbl_conformacion_jurados fk_conf_usuario; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_conformacion_jurados
    ADD CONSTRAINT fk_conf_usuario FOREIGN KEY (id_usuario_asignador) REFERENCES public.tbl_usuarios(id);


--
-- Name: tbl_coordinador_carrera fk_coordinador; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coordinador_carrera
    ADD CONSTRAINT fk_coordinador FOREIGN KEY (id_coordinador) REFERENCES public.tbl_coordinadores(id);


--
-- Name: tbl_correcciones_jurados fk_correcciones_conformacion_jurado; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_correcciones_jurados
    ADD CONSTRAINT fk_correcciones_conformacion_jurado FOREIGN KEY (id_conformacion_jurado) REFERENCES public.tbl_conformacion_jurados(id);


--
-- Name: dic_acciones fk_dic_acciones_id_etapa_pertenencia_dic_etapas_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_acciones
    ADD CONSTRAINT fk_dic_acciones_id_etapa_pertenencia_dic_etapas_id FOREIGN KEY (id_etapa_pertenencia) REFERENCES public.dic_etapas(id);


--
-- Name: dic_acciones fk_dic_acciones_id_servicios; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_acciones
    ADD CONSTRAINT fk_dic_acciones_id_servicios FOREIGN KEY (id_servicios) REFERENCES public.dic_servicios(id);


--
-- Name: dic_carreras fk_dic_carreras_id_facultad_dic_facultades_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_carreras
    ADD CONSTRAINT fk_dic_carreras_id_facultad_dic_facultades_id FOREIGN KEY (id_facultad) REFERENCES public.dic_facultades(id);


--
-- Name: dic_denominaciones fk_dic_denominaciones_id_especialidad_dic_especialidades_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_denominaciones
    ADD CONSTRAINT fk_dic_denominaciones_id_especialidad_dic_especialidades_id FOREIGN KEY (id_especialidad) REFERENCES public.dic_especialidades(id);


--
-- Name: dic_disciplinas fk_dic_disciplinas_id_subarea_dic_subareas_ocde_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_disciplinas
    ADD CONSTRAINT fk_dic_disciplinas_id_subarea_dic_subareas_ocde_id FOREIGN KEY (id_subarea) REFERENCES public.dic_subareas_ocde(id);


--
-- Name: dic_especialidades fk_dic_especialidades_id_carrera_dic_carreras_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_especialidades
    ADD CONSTRAINT fk_dic_especialidades_id_carrera_dic_carreras_id FOREIGN KEY (id_carrera) REFERENCES public.dic_carreras(id);


--
-- Name: tbl_correcciones_jurados fk_dic_etapas; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_correcciones_jurados
    ADD CONSTRAINT fk_dic_etapas FOREIGN KEY (id_etapa) REFERENCES public.dic_etapas(id);


--
-- Name: dic_facultades fk_dic_facultades_id_area_dic_areas_ocde_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_facultades
    ADD CONSTRAINT fk_dic_facultades_id_area_dic_areas_ocde_id FOREIGN KEY (id_area) REFERENCES public.dic_areas_ocde(id);


--
-- Name: tbl_tramitesdet fk_dic_orden_jurado; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramitesdet
    ADD CONSTRAINT fk_dic_orden_jurado FOREIGN KEY (id_orden) REFERENCES public.dic_orden_jurado(id);


--
-- Name: dic_subareas_ocde fk_dic_subareas_ocde_id_area_dic_areas_ocde_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_subareas_ocde
    ADD CONSTRAINT fk_dic_subareas_ocde_id_area_dic_areas_ocde_id FOREIGN KEY (id_area) REFERENCES public.dic_areas_ocde(id);


--
-- Name: dic_visto_bueno fk_dic_visto_bueno_id_etapa_dic_etapas_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.dic_visto_bueno
    ADD CONSTRAINT fk_dic_visto_bueno_id_etapa_dic_etapas_id FOREIGN KEY (id_etapa) REFERENCES public.dic_etapas(id);


--
-- Name: tbl_coordinador_carrera fk_facultad; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coordinador_carrera
    ADD CONSTRAINT fk_facultad FOREIGN KEY (id_facultad) REFERENCES public.dic_facultades(id);


--
-- Name: tbl_grado_docente fk_grado_academico; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_grado_docente
    ADD CONSTRAINT fk_grado_academico FOREIGN KEY (id_grado_academico) REFERENCES public.dic_grados_academicos(id);


--
-- Name: tbl_asignacion_jurado fk_historial_docente; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_asignacion_jurado
    ADD CONSTRAINT fk_historial_docente FOREIGN KEY (docente_id) REFERENCES public.tbl_docentes(id);


--
-- Name: tbl_asignacion_jurado fk_historial_etapa; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_asignacion_jurado
    ADD CONSTRAINT fk_historial_etapa FOREIGN KEY (id_etapa) REFERENCES public.dic_etapas(id);


--
-- Name: tbl_asignacion_jurado fk_historial_orden; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_asignacion_jurado
    ADD CONSTRAINT fk_historial_orden FOREIGN KEY (id_orden) REFERENCES public.dic_orden_jurado(id);


--
-- Name: tbl_asignacion_jurado fk_historial_tipo_evento; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_asignacion_jurado
    ADD CONSTRAINT fk_historial_tipo_evento FOREIGN KEY (id_tipo_evento) REFERENCES public.dic_tipoevento_jurado(id);


--
-- Name: tbl_coordinadores_historial fk_historial_to_acciones; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coordinadores_historial
    ADD CONSTRAINT fk_historial_to_acciones FOREIGN KEY (id_accion) REFERENCES public.dic_acciones(id);


--
-- Name: tbl_coordinadores_historial fk_historial_to_carreras; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coordinadores_historial
    ADD CONSTRAINT fk_historial_to_carreras FOREIGN KEY (id_carrera) REFERENCES public.dic_carreras(id);


--
-- Name: tbl_coordinadores_historial fk_historial_to_facultades; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coordinadores_historial
    ADD CONSTRAINT fk_historial_to_facultades FOREIGN KEY (id_facultad) REFERENCES public.dic_facultades(id);


--
-- Name: tbl_coordinadores_historial fk_historial_to_nivel_coordinador; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coordinadores_historial
    ADD CONSTRAINT fk_historial_to_nivel_coordinador FOREIGN KEY (id_nivel_coordinador) REFERENCES public.dic_nivel_coordinador(id);


--
-- Name: tbl_asignacion_jurado fk_historial_tramite; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_asignacion_jurado
    ADD CONSTRAINT fk_historial_tramite FOREIGN KEY (tramite_id) REFERENCES public.tbl_tramites(id);


--
-- Name: tbl_asignacion_jurado fk_historial_usuario; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_asignacion_jurado
    ADD CONSTRAINT fk_historial_usuario FOREIGN KEY (id_usuario_asignador) REFERENCES public.tbl_usuarios(id);


--
-- Name: log_acciones fk_log_acciones_id_accion_dic_acciones_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.log_acciones
    ADD CONSTRAINT fk_log_acciones_id_accion_dic_acciones_id FOREIGN KEY (id_accion) REFERENCES public.dic_acciones(id);


--
-- Name: log_acciones fk_log_acciones_id_etapa_dic_etapas_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.log_acciones
    ADD CONSTRAINT fk_log_acciones_id_etapa_dic_etapas_id FOREIGN KEY (id_etapa) REFERENCES public.dic_etapas(id);


--
-- Name: log_acciones fk_log_acciones_id_tramite_tbl_tramites_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.log_acciones
    ADD CONSTRAINT fk_log_acciones_id_tramite_tbl_tramites_id FOREIGN KEY (id_tramite) REFERENCES public.tbl_tramites(id);


--
-- Name: log_acciones fk_log_acciones_id_usuario_tbl_usuarios_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.log_acciones
    ADD CONSTRAINT fk_log_acciones_id_usuario_tbl_usuarios_id FOREIGN KEY (id_usuario) REFERENCES public.tbl_usuarios(id);


--
-- Name: tbl_admins fk_nivel_admin; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_admins
    ADD CONSTRAINT fk_nivel_admin FOREIGN KEY (nivel_admin) REFERENCES public.dic_nivel_admin(id);


--
-- Name: tbl_coordinador_carrera fk_nivel_coordinador; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coordinador_carrera
    ADD CONSTRAINT fk_nivel_coordinador FOREIGN KEY (nivel_coordinador) REFERENCES public.dic_nivel_coordinador(id);


--
-- Name: tbl_admins_historial fk_tbl_admins_historial_id_admin_tbl_admins_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_admins_historial
    ADD CONSTRAINT fk_tbl_admins_historial_id_admin_tbl_admins_id FOREIGN KEY (id_admin) REFERENCES public.tbl_admins(id);


--
-- Name: tbl_admins fk_tbl_admins_id_usuario_tbl_usuarios_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_admins
    ADD CONSTRAINT fk_tbl_admins_id_usuario_tbl_usuarios_id FOREIGN KEY (id_usuario) REFERENCES public.tbl_usuarios(id);


--
-- Name: tbl_archivos_tramites fk_tbl_archivos_tramites_id_etapa_dic_etapas_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_archivos_tramites
    ADD CONSTRAINT fk_tbl_archivos_tramites_id_etapa_dic_etapas_id FOREIGN KEY (id_etapa) REFERENCES public.dic_etapas(id);


--
-- Name: tbl_archivos_tramites fk_tbl_archivos_tramites_id_tipo_archivo_dic_tipo_archivo_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_archivos_tramites
    ADD CONSTRAINT fk_tbl_archivos_tramites_id_tipo_archivo_dic_tipo_archivo_id FOREIGN KEY (id_tipo_archivo) REFERENCES public.dic_tipo_archivo(id);


--
-- Name: tbl_archivos_tramites fk_tbl_archivos_tramites_id_tramite_tbl_tramites_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_archivos_tramites
    ADD CONSTRAINT fk_tbl_archivos_tramites_id_tramite_tbl_tramites_id FOREIGN KEY (id_tramite) REFERENCES public.tbl_tramites(id);


--
-- Name: tbl_archivos_tramites fk_tbl_archivos_tramites_id_tramites_metadatos_tbl_tramites_; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_archivos_tramites
    ADD CONSTRAINT fk_tbl_archivos_tramites_id_tramites_metadatos_tbl_tramites_ FOREIGN KEY (id_tramites_metadatos) REFERENCES public.tbl_tramites_metadatos(id);


--
-- Name: tbl_coasesores_historial fk_tbl_coasesores_historial_id_coasesor_tbl_coasesores_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coasesores_historial
    ADD CONSTRAINT fk_tbl_coasesores_historial_id_coasesor_tbl_coasesores_id FOREIGN KEY (id_coasesor) REFERENCES public.tbl_coasesores(id);


--
-- Name: tbl_coasesores_historial fk_tbl_coasesores_historial_id_usuario_verificador_tbl_usuar; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coasesores_historial
    ADD CONSTRAINT fk_tbl_coasesores_historial_id_usuario_verificador_tbl_usuar FOREIGN KEY (id_usuario_verificador) REFERENCES public.tbl_usuarios(id);


--
-- Name: tbl_coasesores fk_tbl_coasesores_id_investigador_tbl_perfil_investigador_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coasesores
    ADD CONSTRAINT fk_tbl_coasesores_id_investigador_tbl_perfil_investigador_id FOREIGN KEY (id_investigador) REFERENCES public.tbl_perfil_investigador(id);


--
-- Name: tbl_coordinadores_historial fk_tbl_coordinadores_historial_id_coordinador_tbl_coordinado; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coordinadores_historial
    ADD CONSTRAINT fk_tbl_coordinadores_historial_id_coordinador_tbl_coordinado FOREIGN KEY (id_coordinador) REFERENCES public.tbl_coordinadores(id);


--
-- Name: tbl_coordinadores fk_tbl_coordinadores_id_usuario_tbl_usuarios_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_coordinadores
    ADD CONSTRAINT fk_tbl_coordinadores_id_usuario_tbl_usuarios_id FOREIGN KEY (id_usuario) REFERENCES public.tbl_usuarios(id);


--
-- Name: tbl_docentes fk_tbl_docentes_id_categoria_dic_categoria_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_docentes
    ADD CONSTRAINT fk_tbl_docentes_id_categoria_dic_categoria_id FOREIGN KEY (id_categoria) REFERENCES public.dic_categoria(id);


--
-- Name: tbl_docentes fk_tbl_docentes_id_especialidad_dic_especialidades_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_docentes
    ADD CONSTRAINT fk_tbl_docentes_id_especialidad_dic_especialidades_id FOREIGN KEY (id_especialidad) REFERENCES public.dic_especialidades(id);


--
-- Name: tbl_docentes fk_tbl_docentes_id_usuario_tbl_usuarios_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_docentes
    ADD CONSTRAINT fk_tbl_docentes_id_usuario_tbl_usuarios_id FOREIGN KEY (id_usuario) REFERENCES public.tbl_usuarios(id);


--
-- Name: tbl_docentes_lineas_historial fk_tbl_docentes_lineas_historial_id_docente_tbl_docentes_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_docentes_lineas_historial
    ADD CONSTRAINT fk_tbl_docentes_lineas_historial_id_docente_tbl_docentes_id FOREIGN KEY (id_docente) REFERENCES public.tbl_docentes(id);


--
-- Name: tbl_docentes_lineas_historial fk_tbl_docentes_lineas_historial_id_sublinea_vri_tbl_subline; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_docentes_lineas_historial
    ADD CONSTRAINT fk_tbl_docentes_lineas_historial_id_sublinea_vri_tbl_subline FOREIGN KEY (id_sublinea_vri) REFERENCES public.tbl_sublineas_vri(id);


--
-- Name: tbl_docentes_lineas fk_tbl_docentes_lineas_id_docente_tbl_docentes_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_docentes_lineas
    ADD CONSTRAINT fk_tbl_docentes_lineas_id_docente_tbl_docentes_id FOREIGN KEY (id_docente) REFERENCES public.tbl_docentes(id);


--
-- Name: tbl_docentes_lineas fk_tbl_docentes_lineas_id_sublinea_vri_tbl_sublineas_vri_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_docentes_lineas
    ADD CONSTRAINT fk_tbl_docentes_lineas_id_sublinea_vri_tbl_sublineas_vri_id FOREIGN KEY (id_sublinea_vri) REFERENCES public.tbl_sublineas_vri(id);


--
-- Name: tbl_estructura_academica fk_tbl_estructura_academica_id_especialidad_dic_especialidad; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_estructura_academica
    ADD CONSTRAINT fk_tbl_estructura_academica_id_especialidad_dic_especialidad FOREIGN KEY (id_especialidad) REFERENCES public.dic_especialidades(id);


--
-- Name: tbl_estructura_academica fk_tbl_estructura_academica_id_sede_dic_sedes_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_estructura_academica
    ADD CONSTRAINT fk_tbl_estructura_academica_id_sede_dic_sedes_id FOREIGN KEY (id_sede) REFERENCES public.dic_sedes(id);


--
-- Name: tbl_integrantes fk_tbl_integrantes_id_tesista_tbl_tesistas_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_integrantes
    ADD CONSTRAINT fk_tbl_integrantes_id_tesista_tbl_tesistas_id FOREIGN KEY (id_tesista) REFERENCES public.tbl_tesistas(id);


--
-- Name: tbl_integrantes fk_tbl_integrantes_id_tramite_tbl_tramites_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_integrantes
    ADD CONSTRAINT fk_tbl_integrantes_id_tramite_tbl_tramites_id FOREIGN KEY (id_tramite) REFERENCES public.tbl_tramites(id);


--
-- Name: tbl_observaciones fk_tbl_observaciones_id_etapa_dic_etapas_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_observaciones
    ADD CONSTRAINT fk_tbl_observaciones_id_etapa_dic_etapas_id FOREIGN KEY (id_etapa) REFERENCES public.dic_etapas(id);


--
-- Name: tbl_observaciones fk_tbl_observaciones_id_rol_tbl_usuarios_servicios_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_observaciones
    ADD CONSTRAINT fk_tbl_observaciones_id_rol_tbl_usuarios_servicios_id FOREIGN KEY (id_rol) REFERENCES public.tbl_usuarios_servicios(id);


--
-- Name: tbl_observaciones fk_tbl_observaciones_id_tramite_tbl_tramites_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_observaciones
    ADD CONSTRAINT fk_tbl_observaciones_id_tramite_tbl_tramites_id FOREIGN KEY (id_tramite) REFERENCES public.tbl_tramites(id);


--
-- Name: tbl_observaciones fk_tbl_observaciones_id_usuario_tbl_usuarios_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_observaciones
    ADD CONSTRAINT fk_tbl_observaciones_id_usuario_tbl_usuarios_id FOREIGN KEY (id_usuario) REFERENCES public.tbl_usuarios(id);


--
-- Name: tbl_perfil_investigador fk_tbl_perfil_investigador_id_usuario_tbl_usuarios_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_perfil_investigador
    ADD CONSTRAINT fk_tbl_perfil_investigador_id_usuario_tbl_usuarios_id FOREIGN KEY (id_usuario) REFERENCES public.tbl_usuarios(id);


--
-- Name: tbl_sublineas_vri fk_tbl_sublineas_vri_id_carrera_dic_carreras_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_sublineas_vri
    ADD CONSTRAINT fk_tbl_sublineas_vri_id_carrera_dic_carreras_id FOREIGN KEY (id_carrera) REFERENCES public.dic_carreras(id);


--
-- Name: tbl_sublineas_vri fk_tbl_sublineas_vri_id_disciplina_dic_disciplinas_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_sublineas_vri
    ADD CONSTRAINT fk_tbl_sublineas_vri_id_disciplina_dic_disciplinas_id FOREIGN KEY (id_disciplina) REFERENCES public.dic_disciplinas(id);


--
-- Name: tbl_sublineas_vri fk_tbl_sublineas_vri_id_linea_universidad_dic_lineas_univers; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_sublineas_vri
    ADD CONSTRAINT fk_tbl_sublineas_vri_id_linea_universidad_dic_lineas_univers FOREIGN KEY (id_linea_universidad) REFERENCES public.dic_lineas_universidad(id);


--
-- Name: tbl_tesistas fk_tbl_tesistas_id_estructura_academica_tbl_estructura_acade; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tesistas
    ADD CONSTRAINT fk_tbl_tesistas_id_estructura_academica_tbl_estructura_acade FOREIGN KEY (id_estructura_academica) REFERENCES public.tbl_estructura_academica(id);


--
-- Name: tbl_tesistas fk_tbl_tesistas_id_usuario_tbl_usuarios_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tesistas
    ADD CONSTRAINT fk_tbl_tesistas_id_usuario_tbl_usuarios_id FOREIGN KEY (id_usuario) REFERENCES public.tbl_usuarios(id);


--
-- Name: tbl_tramites_historial fk_tbl_tramites_historial_id_etapa_dic_etapas_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramites_historial
    ADD CONSTRAINT fk_tbl_tramites_historial_id_etapa_dic_etapas_id FOREIGN KEY (id_etapa) REFERENCES public.dic_etapas(id);


--
-- Name: tbl_tramites_historial fk_tbl_tramites_historial_id_tramite_tbl_tramites_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramites_historial
    ADD CONSTRAINT fk_tbl_tramites_historial_id_tramite_tbl_tramites_id FOREIGN KEY (id_tramite) REFERENCES public.tbl_tramites(id);


--
-- Name: tbl_tramites fk_tbl_tramites_id_denominacion_dic_denominaciones_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramites
    ADD CONSTRAINT fk_tbl_tramites_id_denominacion_dic_denominaciones_id FOREIGN KEY (id_denominacion) REFERENCES public.dic_denominaciones(id);


--
-- Name: tbl_tramites fk_tbl_tramites_id_etapa_dic_etapas_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramites
    ADD CONSTRAINT fk_tbl_tramites_id_etapa_dic_etapas_id FOREIGN KEY (id_etapa) REFERENCES public.dic_etapas(id);


--
-- Name: tbl_tramites fk_tbl_tramites_id_modalidad_dic_modalidades_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramites
    ADD CONSTRAINT fk_tbl_tramites_id_modalidad_dic_modalidades_id FOREIGN KEY (id_modalidad) REFERENCES public.dic_modalidades(id);


--
-- Name: tbl_tramites fk_tbl_tramites_id_sublinea_vri_tbl_sublineas_vri_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramites
    ADD CONSTRAINT fk_tbl_tramites_id_sublinea_vri_tbl_sublineas_vri_id FOREIGN KEY (id_sublinea_vri) REFERENCES public.tbl_sublineas_vri(id);


--
-- Name: tbl_tramites fk_tbl_tramites_id_tipo_trabajo_dic_tipo_trabajos_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramites
    ADD CONSTRAINT fk_tbl_tramites_id_tipo_trabajo_dic_tipo_trabajos_id FOREIGN KEY (id_tipo_trabajo) REFERENCES public.dic_tipo_trabajos(id);


--
-- Name: tbl_tramites_metadatos fk_tbl_tramites_metadatos_id_etapa_dic_etapas_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramites_metadatos
    ADD CONSTRAINT fk_tbl_tramites_metadatos_id_etapa_dic_etapas_id FOREIGN KEY (id_etapa) REFERENCES public.dic_etapas(id);


--
-- Name: tbl_tramites_metadatos fk_tbl_tramites_metadatos_id_tramite_tbl_tramites_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramites_metadatos
    ADD CONSTRAINT fk_tbl_tramites_metadatos_id_tramite_tbl_tramites_id FOREIGN KEY (id_tramite) REFERENCES public.tbl_tramites(id);


--
-- Name: tbl_tramitesdet fk_tbl_tramitesdet_id_docente_tbl_docentes_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramitesdet
    ADD CONSTRAINT fk_tbl_tramitesdet_id_docente_tbl_docentes_id FOREIGN KEY (id_docente) REFERENCES public.tbl_docentes(id);


--
-- Name: tbl_tramitesdet fk_tbl_tramitesdet_id_etapa_dic_etapas_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramitesdet
    ADD CONSTRAINT fk_tbl_tramitesdet_id_etapa_dic_etapas_id FOREIGN KEY (id_etapa) REFERENCES public.dic_etapas(id);


--
-- Name: tbl_tramitesdet fk_tbl_tramitesdet_id_tramite_tbl_tramites_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramitesdet
    ADD CONSTRAINT fk_tbl_tramitesdet_id_tramite_tbl_tramites_id FOREIGN KEY (id_tramite) REFERENCES public.tbl_tramites(id);


--
-- Name: tbl_tramitesdet fk_tbl_tramitesdet_id_visto_bueno_dic_visto_bueno_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramitesdet
    ADD CONSTRAINT fk_tbl_tramitesdet_id_visto_bueno_dic_visto_bueno_id FOREIGN KEY (id_visto_bueno) REFERENCES public.dic_visto_bueno(id);


--
-- Name: tbl_tramitesdoc fk_tbl_tramitesdoc_id_etapa_dic_etapas_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramitesdoc
    ADD CONSTRAINT fk_tbl_tramitesdoc_id_etapa_dic_etapas_id FOREIGN KEY (id_etapa) REFERENCES public.dic_etapas(id);


--
-- Name: tbl_tramitesdoc fk_tbl_tramitesdoc_id_tramite_tbl_tramites_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramitesdoc
    ADD CONSTRAINT fk_tbl_tramitesdoc_id_tramite_tbl_tramites_id FOREIGN KEY (id_tramite) REFERENCES public.tbl_tramites(id);


--
-- Name: tbl_tramitesdoc fk_tbl_tramitesdoc_id_tramites_metadatos_tbl_tramites_metada; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_tramitesdoc
    ADD CONSTRAINT fk_tbl_tramitesdoc_id_tramites_metadatos_tbl_tramites_metada FOREIGN KEY (id_tramites_metadatos) REFERENCES public.tbl_tramites_metadatos(id);


--
-- Name: tbl_usuarios_servicios fk_tbl_usuarios_servicios_id_servicio_dic_servicios_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_usuarios_servicios
    ADD CONSTRAINT fk_tbl_usuarios_servicios_id_servicio_dic_servicios_id FOREIGN KEY (id_servicio) REFERENCES public.dic_servicios(id);


--
-- Name: tbl_usuarios_servicios fk_tbl_usuarios_servicios_id_usuario_tbl_usuarios_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_usuarios_servicios
    ADD CONSTRAINT fk_tbl_usuarios_servicios_id_usuario_tbl_usuarios_id FOREIGN KEY (id_usuario) REFERENCES public.tbl_usuarios(id);


--
-- Name: tbl_dictamenes_info fk_tramite; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_dictamenes_info
    ADD CONSTRAINT fk_tramite FOREIGN KEY (id_tramite) REFERENCES public.tbl_tramites(id);


--
-- Name: tbl_docente_categoria_historial tbl_docente_categoria_historial_id_docente_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_docente_categoria_historial
    ADD CONSTRAINT tbl_docente_categoria_historial_id_docente_fkey FOREIGN KEY (id_docente) REFERENCES public.tbl_docentes(id);


--
-- Name: tbl_estudios tbl_estudios_id_grado_academico_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_estudios
    ADD CONSTRAINT tbl_estudios_id_grado_academico_fkey FOREIGN KEY (id_grado_academico) REFERENCES public.dic_grados_academicos(id);


--
-- Name: tbl_estudios tbl_estudios_id_tipo_obtencion_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_estudios
    ADD CONSTRAINT tbl_estudios_id_tipo_obtencion_fkey FOREIGN KEY (id_tipo_obtencion) REFERENCES public.dic_obtencion_studios(id);


--
-- Name: tbl_estudios tbl_estudios_id_universidad_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_estudios
    ADD CONSTRAINT tbl_estudios_id_universidad_fkey FOREIGN KEY (id_universidad) REFERENCES public.dic_universidades(id);


--
-- Name: tbl_estudios tbl_estudios_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_estudios
    ADD CONSTRAINT tbl_estudios_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.tbl_usuarios(id);


--
-- Name: tbl_grado_docente tbl_grado_docente_id_docente_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.tbl_grado_docente
    ADD CONSTRAINT tbl_grado_docente_id_docente_fkey FOREIGN KEY (id_docente) REFERENCES public.tbl_docentes(id);


--
-- PostgreSQL database dump complete
--

\unrestrict wsod1mFO2jW2ZaehKs7NPNADM5COeEPGrV0Nx5F2wyxEzkhnROYcEggwTayMA5z

