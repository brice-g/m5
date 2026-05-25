# Plan d'Atténuation des Menaces — Sécurisation de la Pipeline FastIA

Ce document formalise la stratégie de défense périmétrique et algorithmique de la pipeline FastIA. Il détaille les contre-mesures appliquées ou planifiées pour neutraliser les vulnérabilités identifiées dans notre *Threat Model*, conformément aux meilleures pratiques de l'**OWASP Top 10 for LLM Applications** et du **MITRE ATLAS**.

---

## 1. Tableau de Synthèse des Défenses

| Menace | Contre-mesure / Défense | Composant Cible | Statut | Priorité |
| :--- | :--- | :--- | :--- | :---: |
| **M1. Évasion par homoglyphes** | Normalisation Unicode (NFKC) & Translittération Cyrillique | `input_sanitizer.py` | **Implémenté** | **Haute** |
| **M2. Injection de prompt** | Analyse heuristique par Regex et levée de drapeau (*flagging*) | `input_sanitizer.py` | **Implémenté** | **Haute** |
| **M3. Empoisonnement du dataset** | Validation stricte des schémas et détection d'anomalies de surface | `Pydantic` / `clean.py` | **Partiel** | Moyenne |
| **M4. Extraction de modèle** | Limiteur de débit (*Rate Limiting*) et audit des signatures d'appels | Passerelle API / Logs | **À implémenter** | Basse |

---

## 2. Fiches Techniques des Contre-Mesures

### M1. Évasion par homoglyphes (Visual Mimicry)
* **Mécanisme technique** : Interception du texte en amont de toute inférence par inspection des noms officiels de la table Unicode. Le module convertit activement les caractères confusables cyrilliques/grecs vers leurs équivalents ASCII latins les plus proches et applique une normalisation de compatibilité `NFKC`.
* **Limites connues** : Ne protège pas contre les attaques par obfuscation purement sémantique (comme l'écriture phonétique ou le *Leet speak* agressif du type `b0nj0ur`) qui requièrent un dictionnaire de reformatage lourd.
* **Effort d'implémentation** : **Déjà fait (Étape 2)** — Validé et couvert à 100% par la suite de tests unitaires Pytest.

### M2. Injection de prompt (Prompt Injection)
* **Mécanisme technique** : Recherche de motifs textuels conflictuels connus (*"ignore"*, *"oublie"*, *"system prompt"*) via des expressions régulières compilées et insensibles à la casse. En cas de correspondance, le système lève un attribut booléen `injection_suspected: true` dans le modèle Pydantic sans interrompre la pipeline, permettant un routage ou un audit dédié.
* **Limites connues** : Les attaques par injection indirecte complexes, les contournements par traduction multilingue synchrone (*jailbreaks* complexes) ou les encodages en Base64 peuvent échapper à des filtres purement heuristiques par expressions régulières.
* **Effort d'implémentation** : **Déjà fait (Étape 2)** — Logique non-bloquante intégrée au cycle de pré-traitement de surface.

### M3. Empoisonnement du dataset (Data Poisoning)
* **Mécanisme technique** : Protection de l'intégrité des données d'entraînement futures par double filtrage. D'une part, la validation de types par Pydantic bloque les payloads corrompus structurellement ; d'autre part, le script `clean.py` applique des seuils d'exclusion (rejet des textes vides, doublons exacts massifs ou chaînes de caractères anormalement répétitives).
* **Limites connues** : Cette défense n'intercepte pas l'empoisonnement sémantique subtil (par exemple, un utilisateur malveillant qui soumettrait de faux avis très polis mais porteurs d'annotations ou d'intentions erronées pour fausser un futur *fine-tuning*).
* **Effort d'implémentation** : **Partiel (M2-M3)** — Les structures de validation Pydantic de base et le nettoyage de surface existent déjà, mais l'analyse d'anomalies statistiques avancée sur le stockage reste à consolider.

### M4. Extraction de modèle (Model Inversion / Exfiltration)
* **Mécanisme technique** : Mise en œuvre d'une couche de limitation des requêtes (*Rate Limiting*) par adresse IP et par clé d'API utilisateur sur l'endpoint `/predict`. Ce mécanisme est couplé à une journalisation centralisée capable d'identifier les variations suspectes à faible entropie (envois massifs de textes quasi-identiques conçus pour cartographier les frontières de décision de `DistilCamembert`).
* **Limites connues** : Inefficace face à une attaque distribuée à grande échelle (Sybil Attack) où l'attaquant orchestre l'extraction via des centaines d'adresses IP distinctes et de comptes configurés pour rester sous les seuils de détection unitaires.
* **Effort d'implémentation** : **À implémenter (Prévu pour le Module 5)** — Nécessite l'intégration d'un middleware dédié au niveau de l'infrastructure de routage HTTP (ex: configuration Reverse Proxy Nginx ou Middleware FastAPI couplé à un stockage Redis pour les compteurs).