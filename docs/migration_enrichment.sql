-- Migration SQL : Ajout des dimensions d'enrichissement IA à la table 'demandes'

BEGIN;

-- 1. Ajout des nouvelles colonnes
ALTER TABLE demandes 
    ADD COLUMN langue VARCHAR(5) DEFAULT NULL,
    ADD COLUMN langue_confidence FLOAT DEFAULT NULL,
    ADD COLUMN sentiment VARCHAR(10) DEFAULT NULL,
    ADD COLUMN sentiment_score FLOAT DEFAULT NULL,
    ADD COLUMN enriched_at TIMESTAMPTZ DEFAULT NULL,
    ADD COLUMN routed_priority VARCHAR(20) DEFAULT NULL;

-- 2. Ajout des commentaires de table pour la gouvernance de données (Data Catalog)
COMMENT ON COLUMN demandes.langue IS 'Code ISO 639-1 détecté par FastText';
COMMENT ON COLUMN demandes.langue_confidence IS 'Score de confiance du modèle de langue [0, 1]';
COMMENT ON COLUMN demandes.sentiment IS 'Label de sentiment : positif, neutre, negatif';
COMMENT ON COLUMN demandes.sentiment_score IS 'Score de confiance du modèle DistilCamembert';
COMMENT ON COLUMN demandes.enriched_at IS 'Date et heure précises du traitement par les modèles IA';
COMMENT ON COLUMN demandes.routed_priority IS 'File de priorité post-routage (high_intl, high_negative, normal)';

-- 3. Création des index optimisés
CREATE INDEX idx_demandes_langue ON demandes(langue);
CREATE INDEX idx_demandes_routed_priority ON demandes(routed_priority);

COMMIT;