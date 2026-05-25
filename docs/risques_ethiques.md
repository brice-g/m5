# Note Réglementaire et Éthique — Projet FastIA

## 1. Cartographie des risques éthiques
L'audit du dataset brut (96 exemples) réalisé lors des phases d'exploration a permis d'identifier trois catégories de risques majeurs :

* **Fuite de Données Personnelles (PII) :** L'audit qualitatif a révélé la présence d'informations directement identifiables dans les champs textuels (`input` et `reponse_suggeree`), notamment des adresses email, des numéros de téléphone et des noms de famille. L'utilisation de ces données sans traitement expose les utilisateurs à des risques de violation de la vie privée.
* **Biais de Représentation et de Décision :** L'analyse des distributions a montré des déséquilibres significatifs. Par exemple, certaines catégories comme "Information générale" sont sous-représentées dans les niveaux de priorité "Haute". Un modèle entraîné sur ces données risquerait de reproduire une discrimination algorithmique en ne traitant jamais ces demandes comme urgentes.
* **Risques liés à la détection automatique (Nouveauté) :** L'introduction de briques de traitement automatique (langue et sentiment) comporte deux biais critiques :
    * *Catégorisation indirecte par langue :* Associer systématiquement une langue minoritaire ou étrangère à un routage spécifique peut créer des silos d'exclusion si l'équipe internationale dispose de moins de ressources, ou si le modèle présente un taux d'erreur plus élevé sur ces langues.
    * *Biais socio-économique (Analyse de sentiment) :* Les modèles d'analyse de sentiment peuvent sur-interpréter la colère ou la frustration en fonction de marqueurs syntaxiques, culturels ou régionaux (ex: fautes d'orthographe, usage de majuscules). Cela risque de pénaliser ou de déprioriser les utilisateurs maîtrisant moins les codes écrits standards ou exprimant leur urgence différemment.

## 2. Référentiel réglementaire applicable

### RGPD (Règlement Général sur la Protection des Données)
Le projet FastIA traite des données de support client, ce qui impose le respect des principes suivants :
* **Minimisation :** Nous ne conservons que les variables `input`, `categorie`, `priorite` et `reponse_suggeree`. Les métadonnées inutiles sont écartées.
* **Protection de la vie privée dès la conception (Privacy by Design) :** L'intégration d'une étape de nettoyage automatisée des PII est une réponse directe à cette obligation.
* **Droit à l'oubli :** La structuration du dataset doit permettre l'identification et la suppression des données d'un individu sur demande.

### AI Act (Règlement européen sur l'IA)
* **Catégorisation :** En tant que système d'aide à la gestion de la relation client, FastIA est classé comme un système d'IA à **risque limité**. Il est toutefois soumis à des obligations de transparence (l'utilisateur doit savoir qu'il interagit avec une IA).
* **Qualité des données :** L'AI Act exige que les datasets d'entraînement soient "pertinents, représentatifs et exempts d'erreurs dans la mesure du possible". Notre démarche d'audit et de nettoyage s'inscrit dans cette conformité.

## 3. Choix effectués dans la pipeline et justifications

| Étape de la Pipeline | Action | Justification Réglementaire |
| :--- | :--- | :--- |
| **Nettoyage Regex** | Suppression automatique des emails, téléphones et adresses IP. | **RGPD :** Anonymisation technique pour protéger l'identité des clients. |
| **Déduplication** | Suppression des entrées identiques ou normalisées. | **AI Act :** Amélioration de la robustesse et de la fiabilité du système. |
| **Enrichissement Sémantique** | Calibration des seuils de confiance (`langue_confidence` et `sentiment_score`) et binarisation de la priorité. | **Éthique & Équité :** Évite les décisions arbitraires basées sur des prédictions NLP incertaines ou discriminantes. |
| **Audit des Biais** | Analyse de la matrice de confusion Catégorie / Priorité / Langue. | **Éthique :** Identification proactive des zones où le modèle pourrait être biaisé envers une population. |
| **Normalisation** | Suppression des caractères spéciaux. | **Technique :** Réduction du bruit pour une meilleure équité de traitement. |

## 4. Risques résiduels
Bien que la pipeline de préparation réduise considérablement les risques, certains points de vigilance demeurent :

1.  **PII non structurées :** Certaines informations sensibles peuvent échapper aux filtres Regex. Une surveillance humaine par échantillonnage reste nécessaire.
2.  **Déséquilibre persistant :** La suppression des doublons ou le nettoyage ne règlent pas le manque de données pour certaines catégories. Le risque de performance dégradée sur les "classes minoritaires" reste présent.
3.  **Invisibilisation par le sentiment :** Un client exprimant une réclamation grave de manière très polie ou factuelle peut être classé en "Priorité Standard" (faux négatif), retardant son traitement par rapport à un utilisateur plus véhément.
