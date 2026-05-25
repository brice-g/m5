-- Table: public.demandes

-- DROP TABLE IF EXISTS public.demandes;

CREATE TABLE IF NOT EXISTS public.demandes
(
    id integer NOT NULL DEFAULT nextval('demandes_id_seq'::regclass),
    input_text text COLLATE pg_catalog."default" NOT NULL,
    input_raw text COLLATE pg_catalog."default",
    categorie character varying(50) COLLATE pg_catalog."default" NOT NULL,
    priorite character varying(20) COLLATE pg_catalog."default" NOT NULL,
    reponse_suggeree text COLLATE pg_catalog."default",
    source character varying(30) COLLATE pg_catalog."default" NOT NULL,
    canal character varying(30) COLLATE pg_catalog."default",
    langue character varying(10) COLLATE pg_catalog."default" DEFAULT 'fr'::character varying,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    dataset_version character varying(20) COLLATE pg_catalog."default" NOT NULL,
    received_at timestamp without time zone,
    external_id character varying(255) COLLATE pg_catalog."default",
    canal_metadata jsonb,
    dedup_status character varying(50) COLLATE pg_catalog."default" DEFAULT 'unique'::character varying,
    sender character varying(64) COLLATE pg_catalog."default",
    CONSTRAINT demandes_pkey PRIMARY KEY (id),
    CONSTRAINT uq_canal_external_id UNIQUE (canal, external_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.demandes
    OWNER to postgres;
-- Index: idx_demandes_categorie

-- DROP INDEX IF EXISTS public.idx_demandes_categorie;

CREATE INDEX IF NOT EXISTS idx_demandes_categorie
    ON public.demandes USING btree
    (categorie COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: idx_demandes_source

-- DROP INDEX IF EXISTS public.idx_demandes_source;

CREATE INDEX IF NOT EXISTS idx_demandes_source
    ON public.demandes USING btree
    (source COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: idx_demandes_version

-- DROP INDEX IF EXISTS public.idx_demandes_version;

CREATE INDEX IF NOT EXISTS idx_demandes_version
    ON public.demandes USING btree
    (dataset_version COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;