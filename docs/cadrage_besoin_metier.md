# Reformulation du besoin

Enrichir automatiquement les requêtes entrantes (Web, Email, Chat) avec la langue d'origine détectée afin de router prioritairement les demandes non-francophones (notamment EN et ES) vers l'équipe support spécialisée.

## Personas concernés

* **Producteurs :** Clients (PME et B2B) utilisant les formulaires web, les emails ou le chat.
* **Transformateur :** Pipeline de données FastIA (module d'enrichissement).
* **Consommateurs :** Équipe support spécialisée (traitement des tickets), système de routage de la plateforme client.
* **Décideurs :** Directeur métier et Product Manager (pilotage des flux et redimensionnement des équipes).

## Critères de succès

* Détecter la langue d'un texte avec une précision (accuracy) $\ge$ 95% sur un échantillon de validation FR/EN/ES de 200 lignes extraites de la production.

## Hypothèses à vérifier

* Le volume de demandes non-francophones représente réellement 33% du volume global.
* Cette proportion est principalement portée par les canaux asynchrones.

## Non-objectifs

* Il n'est pas question de traduire automatiquement le contenu des demandes.
* Nous ne modifierons pas le modèle prédictif principal actuel.

## Risques éthiques préliminaires

* **Biais de catégorisation :** Déduire l'origine géographique ou la nationalité d'un utilisateur sur la base de la langue détectée.
* **Réglementation (AI Act) :** Bien qu'il s'agisse d'un système à risque minime, il convient de ne pas utiliser cette donnée linguistique pour profiler ou discriminer les utilisateurs quant à la qualité du service rendu.