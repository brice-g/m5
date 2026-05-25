# Audit Qualitatif et Analyse du Dataset - Projet FastIA

Ce document synthétise les observations clés concernant la qualité, l'éthique et les biais du dataset d'entraînement.

---

## 1. Équilibre du Dataset
Le dataset présente un profil mixte en termes de distribution :

* **Catégories (Équilibrées) :** La répartition est homogène. Les cinq classes oscillent entre 17 et 22 exemples. Il n'y a pas de classe "écrasante", ce qui est excellent pour la classification.
* **Priorités (Déséquilibrées) :** On observe un fort biais en faveur de la priorité `normale` (71%) face à la priorité `haute` (29%).
* **Risque :** Le modèle risque de sous-estimer l'urgence d'une demande client 

## 2. Problèmes de Qualité Identifiés
Malgré une propreté apparente (0 doublon, 0 valeur manquante), plusieurs points de vigilance émergent :

* **Uniformité Suspecte :** La catégorie "Information générale" est celle qui présente le plus fort risque de biais lié à la longueur
Elle possède la médiane la plus basse (environ 75-80 caractères) et sa boîte (l'écart interquartile) ne chevauche quasiment pas celles des autres catégories
Conséquence : le modèle risque de prédire "Information générale" en se basant principalement sur la longueur de la demande plutôt que sur son contenu.

## 3. Données Personnelles et Sensibles (RGPD)
L'audit qualitatif est formel : **11,5% des lignes (11/96)** contiennent des données à caractère personnel (PII).

* **Identité :** "Monsieur Martin", "Madame Dupont".
* **Contact :** Numéros de téléphone et adresses emails.
* **Professionnel :** Noms d'entreprises associés à des fonctions (ex: "Responsable SI chez NovaTech").

**Non-conformité RGPD et IA ACT :** Le dataset n'est pas conforme en l'état. Ces données doivent être anonymisées avant tout entraînement pour éviter que le modèle ne les mémorise et ne les fournisse à d'autres utilisateurs.

## 4. Biais à investiguer (Brief 2)
Deux biais majeurs doivent faire l'objet d'une analyse approfondie :

1.  **Biais de Corrélation Catégorie/Priorité :** La catégorie "Information générale" n'a aucun exemple en priorité haute. Le modèle pourrait apprendre par erreur que *"Information = Toujours normal"*, il faut confirmer ce comportement avec le client.

## 5. Actions Correctives Prioritaires
Pour le passage au Brief 2, les actions suivantes sont indispensables :

* **Anonymisation :** Remplacer systématiquement les noms par des tokens `[NOM]`, les téléphones par `[TEL]` et les emails par `[EMAIL]`, etc.
* **Rééquilibrage :** Augmenter le nombre d'exemples en priorité `haute` (viser un ratio 40/60).
