# Threat Model : Robustesse et Sécurité de la Pipeline FastIA

Ce document récapitule l'analyse des menaces (Threat Modeling) réalisée lors du Module 4. Il identifie les vecteurs d'attaque testés sur les modèles de détection de langue et de sentiment, ainsi que les mesures de remédiation préconisées.

---

## 1. Taxonomie des familles de menaces appliquées

Conformément au framework **MITRE ATLAS** et aux standards du **NIST**, nous avons identifié quatre familles de menaces critiques pour la pipeline FastIA :

### A. Attaques par Homoglyphes (Visual Mimicry)
* **Description** : Substitution de caractères latins par des caractères Unicode visuellement identiques (ex: 'a' latin remplacé par 'а' cyrillique).
* **Vecteur** : Canaux Chat et Web (utilisateurs malveillants).
* **Impact** : Provoque des erreurs de détection de langue majeures dans `langdetect`. FastText est plus résilient mais pas totalement immunisé.

### B. Bruit Typographique (Adversarial Noise)
* **Description** : Suppression délibérée d'espaces, inversions de lettres ou fautes de frappe excessives pour tromper la détection de sentiment.
* **Impact** : Les modèles de sentiment (Transformers) perdent en précision si le texte n'est pas "nettoyé", car les jetons (tokens) ne sont plus reconnus.

### C. Injection de Mots-Clés (Keyword Stuffing / Bias Triggering)
* **Description** : Insertion de termes à forte polarité (ex: "EXCELLENT", "MAGNIFIQUE") dans une plainte pour forcer un score de sentiment positif.
* **Impact** : Risque de mauvaise priorisation des tickets clients (une plainte urgente peut être classée comme "satisfaction").

### D. Évasion par le Mélange (Code-Switching)
* **Description** : Mélange de plusieurs langues dans un même message (ex: 50% FR, 50% EN).
* **Impact** : Le classifieur de langue peut renvoyer un résultat aléatoire ou avec un score de confiance très bas, perturbant le routage des emails.

---

## 2. Synthèse de l'Évaluation de Robustesse

| Menace | Modèle ciblé | Robustesse observée | Gravité (Impact métier) |
| :--- | :--- | :--- | :--- |
| **Homoglyphes** | Langue | Faible (Langdetect) / Moyenne (FastText) | **Élevée** (Corruption des données) |
| **Bruit Typo** | Sentiment | Moyenne (DistilCamembert) | **Faible** (Imprécision) |
| **Injection** | Sentiment | Faible (Tous modèles) | **Moyenne** (Biais opérationnel) |
| **Code-switching** | Langue | Moyenne | **Faible** (Besoin de seuils) |

---

## 3. Stratégies de Mitigation (Remédiations)

Pour sécuriser la mise en production de l'enrichissement FastIA, les mesures suivantes sont intégrées à la matrice de décision :

1.  **Implémentation d'un "Sanitizer"** : Mise en place d'une étape de normalisation Unicode (NFKC) et de suppression des caractères non-imprimables avant l'inférence.
2.  **Seuils de Confiance (Confidence Thresholds)** : Rejet automatique des prédictions dont le score est inférieur à 0.70.
3.  **Fallback Humain** : En cas de détection incertaine ou d'anomalie structurelle détectée, le message est envoyé en file d'attente manuelle sans étiquetage automatique.
4.  **Monitoring des Out-Of-Distribution (OOD)** : Suivi des logs pour identifier les pics de messages non reconnus par les modèles.

---

## 4. Conclusion

La robustesse n'est pas seulement une affaire de modèle, mais de pipeline. L'utilisation de **FastText** réduit nativement la vulnérabilité aux attaques de bas niveau, mais une couche de **pré-traitement (sanitization)** reste indispensable pour garantir l'intégrité de l'enrichissement face à des utilisateurs adversariaux.
