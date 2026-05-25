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




# Analyse Éthique Consolidée — Volet Enrichissement Automatique (M4)

L'intégration de modules d'intelligence artificielle pour la détection de langue, l'analyse de sentiment et le routage prioritaire soulève des enjeux éthiques et juridiques majeurs. Ce volet évalue les risques associés et définit les garde-fous techniques et organisationnels obligatoires.

---

## 1. Matrice d'Évaluation des Risques IA

Chaque risque est évalué selon sa **Probabilité (P)** et sa **Gravité (G)** sur une échelle de 1 (Très faible) à 5 (Critique).

| Risque Identifié | Métier / Domaine | P | G | Criticité | Cadre Légal |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **R1. Profilage & Discrimination Géographique** | Détection de langue | 2 | 4 | **8 (Moyenne)** | AI Act (Art. 5) |
| **R2. Décision Automatisée Défavorable** | Analyse de sentiment | 3 | 5 | **15 (Haute)** | RGPD (Art. 22) |
| **R3. Asymétrie de Traitement au Routage** | Routage Prioritaire | 4 | 3 | **12 (Moyenne)** | Charte des Droits |
| **R4. Biais d'Entraînement & Sévérité** | Modèle Sentiment | 4 | 3 | **12 (Moyenne)** | Équité / Qualité |

---

## 2. Analyse Détaillée par Risque et Mesures d'Atténuation

### R1. Détection de langue et risque de profilage indirect
* **Description** : La langue d'expression d'un utilisateur est intimement corrélée à son origine géographique ou nationale. L'utilisation automatique de cette variable pourrait dériver vers un profilage indirect inconscient ou une ségrégation des flux, où les usagers non-francophones subiraient des délais ou des restrictions d'accès au support.
* **Alignement Réglementaire** : L'**article 5 de l'AI Act** interdit formellement les systèmes de notation ou de classification des personnes physiques basés sur des caractéristiques protégées (race, origine, langue) pouvant mener à un traitement défavorable.
* **Mesure d'atténuation** : 
  1. Le code de langue (`langue`) est strictement confiné à un rôle d'**aiguillage technique linguistique** (routage vers un agent maîtrisant la langue).
  2. Interdiction formelle d'utiliser la variable `langue` dans les scores d'octroi de droits, de remboursement, ou de niveau de sévérité contractuelle (SLA).

### R2. Sentiment négatif et décision défavorable automatisée
* **Description** : Si un modèle évalue un message comme extrêmement `"negatif"`, le système pourrait être tenté de rejeter automatiquement la demande, de blacklister l'usager ou de clore un ticket jugé "abusif" ou "agressif" afin de désengorger les files d'attente.
* **Alignement Réglementaire** : L'**article 22 du RGPD** stipule que l'usager a le droit de ne pas faire l'objet d'une décision fondant des effets juridiques ou l'affectant de manière significative de façon *exclusivement automatisée*.
* **Mesure d'atténuation** :
  1. **Interdiction de l'automatisation des sanctions** : Aucun refus de service, blocage de compte ou clôture de dossier ne peut être déclenché directement par le score de `DistilCamembert`.
  2. **Human-in-the-loop (HITL)** : Les scores de sentiment négatif servent uniquement à *prioriser la lecture humaine* par un conseiller compétent, qui reste le seul décideur final de la réponse et de l'action corrective.

### R3. Routage prioritaire : la priorisation des demandes non-FR est-elle discriminatoire ?
* **Description** : Orienter les demandes internationales (`high_intl`) ou les sentiments très négatifs (`high_negative`) dans des files prioritaires ralentit mécaniquement le traitement des requêtes standards issues du flux francophone classique (`normal`).
* **Justification Métier (Principe de Proportionnalité)** : Ce traitement différencié ne constitue pas une discrimination illégitime, mais répond à des objectifs de gestion objectifs et proportionnés :
  * *Pour l'international* : Le pool d'agents multilingues étant restreint, un routage ultra-rapide évite l'explosion du délai d'attente cumulé (les requêtes hors-FR stagnaient auparavant par manque d'aiguillage).
  * *Pour le sentiment négatif* : Prioriser une détresse ou une insatisfaction majeure (ex: panne bloquante, menace de résiliation) relève de la gestion des urgences opérationnelles (concept de "Triage"), au même titre que les urgences médicales. Le flux `normal` conserve une garantie de délai de traitement maximal (SLA de surface).
* **Mesure d'atténuation** : Limitation de l'asymétrie par l'instauration d'un **Timeout de sécurité**. Si un ticket de la file `normal` attend depuis plus de 2 heures, sa priorité est rehaussée automatiquement pour empêcher une famine de traitement provoquée par l'afflux de tickets prioritaires.

### R4. Biais des modèles de sentiment (Décalage de distribution)
* **Description** : Les modèles de sentiment open-source (y compris `DistilCamembert`) sont majoritairement pré-entraînés sur des corpus de commentaires publics (Allociné, Amazon, Google Reviews). Or, le registre linguistique d'un utilisateur écrivant à un support client est radicalement différent :
  * Un utilisateur peut utiliser des mots formels mais exprimer une colère froide (*"Je vous saurais gré de régler ce problème au plus vite"* -> souvent classé à tort comme `neutre` ou `positif` par manque de mots grossiers).
  * Des variantes dialectales, des expressions multiculturelles ou des fautes de syntaxe peuvent biaiser le tokenizer et pénaliser systématiquement certains profils d'utilisateurs en sous-évaluant leur urgence.
* **Mesure d'atténuation** :
  1. Exigence d'un **Seuil de confiance minimal à 0.70**. En dessous, le sentiment est neutralisé (`neutral`) pour éviter les faux diagnostics.
  2. Plan de **Fine-tuning continu** : Constitution d'un jeu de données interne d'évaluation composé de véritables verbatims de notre support client (anonymisés) pour ré-entraîner la couche finale du modèle à nos spécificités lexicales.