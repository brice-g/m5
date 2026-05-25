# Spécification Technique : Évolution de l'API FastIA

Ce document fait office de contrat d'interface pour l'équipe de développement. Il spécifie l'implémentation des nouveaux endpoints et l'évolution de l'API `/predict` existante pour y intégrer les dimensions d'enrichissement.

---

## 1. Liste Globale des Codes HTTP Utilisés
L'ensemble de l'API se conforme strictement aux standards REST suivants :
* **`200 OK`** : Succès de la requête. La réponse contient le payload attendu.
* **`422 Unprocessable Entity`** : Échec de la validation structurelle (Pydantic). Corps manquant, texte trop long ou variables invalides.
* **`503 Service Unavailable`** : Défaillance critique d'un composant d'infrastructure (Modèle IA introuvable sur le disque, corruption système). Le client doit retenter plus tard.

---

## 2. Endpoints Existants Mis à Jour

### POST `/predict`
* **Description** : Analyse, classifie, enrichit et applique les règles de routage prioritaires sur un flux entrant (Email, Web, Chat).
* **Schéma Entrée** : `PredictRequest`
* **Schéma Sortie** : `PredictResponse`

#### Exemples de Payloads

**Requête (HTTP POST /predict)** :
```json
{
  "body": "Bonjour, l'application crash systématiquement au démarrage depuis ce matin. C'est inadmissible, je suis bloqué !",
  "canal": "chat"
}
```
Réponse Réussie (200 OK) :
```json
{
  "categorie": "technique_bug",
  "priorite": "haute",
  "reponse_suggeree": "template_incident_technique",
  "langue": "fr",
  "langue_confidence": 1.00,
  "sentiment": "negatif",
  "sentiment_score": 0.94,
  "routed_priority": "high_negative"
}
```
## 3. Nouveaux Endpoints d'Enrichissement et Météo des Modèles
### POST /enrich

* **Description** : Point d'accès unitaire permettant d'exécuter la cascade d'inférence (FastText + DistilCamembert) de manière brute sur un texte sans passer par le workflow de classification et d'écriture en base de données. Idéal pour tester la robustesse des modèles de façon isolée.

* **Schéma Entrée** : EnrichRequest

* **Schéma Sortie** : EnrichResponse

Requête (HTTP POST /enrich) :
```json
{
  "text": "This software update is absolutely amazing."
}
```
Réponse Réussie (200 OK) :
```json
{
  "langue": "en",
  "langue_confidence": 0.99,
  "sentiment": "positif",
  "sentiment_score": 0.91,
  "processed_at": "2026-05-24T15:45:00Z"
}
```
### GET /models

* **Description** : Renvoie l'inventaire complet des modèles actuellement chargés en mémoire RAM de l'instance d'API FastIA avec leurs versions associées.

* **Schéma Entrée** : Aucun (Paramètres d'URL vides)

* **Schéma Sortie** : List[ModelInfo]

Réponse Réussie (200 OK) :
```json
[
  {
    "name": "fasttext-lid-176",
    "version": "1.0.0",
    "task": "language_detection",
    "status": "active"
  },
  {
    "name": "distilcamembert-base-fr-sentiment",
    "version": "2.1.4",
    "task": "sentiment_analysis",
    "status": "active"
  }
]
```
### GET /models/{task}/metrics

* **Description** : Expose de manière transparente les résultats de précision issus du dernier protocole d'évaluation (Brief 1) pour une tâche donnée. Permet au CRM ou à un outil de monitoring d'auditer l'état de l'art du système.

* **Paramètre d'URL** : task (valeurs autorisées : language, sentiment)

* **Schéma Entrée** : Aucun

* **Schéma Sortie** : ModelMetricsResponse

* **Exemple de Requête** : GET /models/language/metrics

Réponse Réussie (200 OK) :
```json
{
  "task": "language",
  "metric_name": "Accuracy",
  "metric_value": 1.00,
  "benchmark_date": "2026-05-24T10:12:00Z",
  "dataset_used": "langue_eval_200.jsonl"
}
```
## 4. Gestion des Erreurs et Diagnostics
### Exemple de Réponse 422 Unprocessable Entity

Levé automatiquement par FastAPI si une règle de validation structurelle ou de taille de texte est transgressée.
```json
{
  "detail": [
    {
      "loc": ["body", "text"],
      "msg": "ensure this value has at most 2000 characters",
      "type": "value_error.any_str.max_length",
      "ctx": {"limit_value": 2000}
    }
  ]
}
```
### Exemple de Réponse 503 Service Unavailable

L'API intercepte tout dysfonctionnement matériel majeur (ex: fichier .bin de FastText manquant sur le disque) pour remonter une alerte propre plutôt qu'un crash non contrôlé de l'application.
```json
{
  "error": "ModelInferenceEngineError",
  "message": "Le sous-système d'analyse de sentiment (DistilCamembert) ne répond pas. Inférence interrompue.",
  "timestamp": "2026-05-24T15:47:12Z"
}
```