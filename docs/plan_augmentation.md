# Stratégie d'Augmentation des Données (Objectif : 150 lignes)

## 1. Analyse des cibles d'augmentation
L'objectif est de passer de 96 à environ 150 exemples en corrigeant les déséquilibres majeurs :

* **Rééquilibrage des priorités :** Passer de 29% à environ 40% de priorité haute.
* **Casser la corrélation "Information = Normal" :** Créer des exemples d'Information générale avec une priorité haute.
* **Neutralisation du biais de longueur :** Allonger les textes de la catégorie Information générale.
* **Anonymisation native :** Tous les nouveaux exemples utiliseront des tokens `[NOM]`, `[PRENOM]`, `[TEL]`, `[EMAIL]`, et `[ADRESSE]`.

## 2. Plan opérationnel

| Cible | Volume | Technique | Description & Consignes |
| :--- | :--- | :--- | :--- |
| **Information générale x Haute** | +20 | Gabarits | Créer des demandes d'info urgentes (ex: "Besoin [NOM] du catalogue avant mon RDV de 14h"). |
| **Toutes catégories x Haute** | +24 | Paraphrase (Llama-3.2) | Transformer des messages normaux existants en messages urgents en ajoutant du stress lexical. |
| **Information générale (Long)** | +10 | Paraphrase (Llama-3.2) | Étendre des messages courts existants pour atteindre ~150-200 caractères. |

## 3. Révision (Analyse unitaire des canaux d'ingestion)

La stratégie d'augmentation doit intégrer les caractéristiques sémantiques et techniques propres à chaque canal d'origine (Web, Chat, Email). Les variables catégorie et priorité étant absentes et non définies à ce stade sur ces canaux, la révision se concentre sur les biais de volume et la nature textuelle des flux de communication afin de préparer le dataset au futur exercice de labellisation.

### 3.1. Diagnostic et identification des déséquilibres par canal

L'analyse de l'état actuel des trois canaux d'ingestion met en évidence des caractéristiques distinctes :

-   **Le Canal Web** (Majoritaire - ~42% du flux traité) :
    -   Constat : Il s'agit de la source principale de données. Les messages y sont généralement structurés (issus de formulaires), mais ils risquent d'induire un biais de standardisation si l'on se base uniquement sur eux.

-   **Le Canal Chat** (Intermédiaire - ~33% du flux traité) :

    -   Constat : Ce canal est marqué par un "bruit" sévère. On y observe de nombreuses entrées vides de sens (ex: messages de type "test" ou "bonjour" sans aucun contexte).

-   **Le Canal Email** (Sous-représenté - ~25% du flux traité) :

    -   Constat : C'est le canal le moins volumineux de l'échantillon. Pourtant, l'e-mail apporte une richesse linguistique importante (formules de politesse, contextualisation longue) indispensable pour entraîner le modèle à la compréhension de requêtes complexes.

### 3.2. Plan d'Action : Arbitrage Synthétique vs Données Réelles

Puisqu'on ne peut pas encore cibler de triplets précis, l'arbitrage se fait sur la qualité sémantique intrinsèque du canal par rapport à son coût d'acquisition.

| Canal | Choix Stratégique | Technique envisagée | Justification (Compromis Qualité / Coût / Représentativité) |
|-------|-------------------|---------------------|--------------------------------------------------------------|
| Email | Collecte de Data Réelle | Extraction de backups de boîtes mails partagées anonymisées. | Représentativité & Qualité : L'e-mail est sous-représenté (~25%). Sa structure textuelle (longue, formelle) est difficile à simuler par IA sans créer des patterns trop parfaits. Aller chercher de la donnée réelle est nécessaire pour préserver la complexité de ce canal, le coût d'extraction et de nettoyage étant justifié par le gain de qualité. |
| Chat | Augmentation Synthétique | Génération de flux de conversations typées "messagerie instantanée" (Llama-3.2). | Qualité & Coût : Le chat réel contient trop de bruit (mots isolés, "tests"). Nettoyer et anonymiser des flux de chat réels coûte cher en raison du RGPD sur les flux vifs. Utiliser l'IA synthétique permet de générer des phrases courtes et directes de style "chat" mais utiles, éliminant ainsi le biais de paresse computationnelle. |
| Web | Statu Quo / Aucun changement | Aucune augmentation sur ce canal pour le moment. | Coût : Le formulaire Web est déjà le canal le plus représenté (~42%). Injecter du budget ou du temps pour augmenter ce canal n'amènerait aucune plus-value sémantique avant que l'exercice de catégorisation n'ait eu lieu. |

### 3.3. Justification Globale du Compromis

L'objectif de cette révision est de préparer un terrain d'entraînement sain avant la catégorisation future :

-   Ajustement du biais de pollution : En choisissant l'augmentation synthétique sur le Chat, on force l'apport de texte à forte valeur ajoutée sémantique dans un canal initialement pollué par du bruit.

-   Ajustement du volume : L'apport de données réelles sur le canal Email va rééquilibrer la distribution globale des canaux (viser un tiers chacun) tout en important de la diversité linguistique réelle.

-   Rentabilité (Coût) : On gagne du temps en n'investissant aucune ressource sur le canal Web, déjà autosuffisant en volume à ce stade.