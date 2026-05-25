CREATE TABLE IF NOT EXISTS demandes (
  id              SERIAL PRIMARY KEY,
  input_text      TEXT NOT NULL,
  input_raw       TEXT,
  categorie       VARCHAR(50) NOT NULL,
  priorite        VARCHAR(20) NOT NULL,
  reponse_suggeree TEXT,
  source          VARCHAR(30) NOT NULL,
  canal           VARCHAR(30),
  langue          VARCHAR(10) DEFAULT 'fr',
  created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
  dataset_version VARCHAR(20) NOT NULL,
  -- Contrainte d'unicité pour l'idempotence (ex: sur le texte et la version)
  CONSTRAINT unique_input_version UNIQUE (input_text, dataset_version)
);

CREATE INDEX IF NOT EXISTS idx_demandes_categorie ON demandes(categorie);
CREATE INDEX IF NOT EXISTS idx_demandes_source ON demandes(source);
CREATE INDEX IF NOT EXISTS idx_demandes_version ON demandes(dataset_version);