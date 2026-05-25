## 1. Pourquoi l'approche non-destructive ? 
Supprimer les doublons cross-canal fausserait l'analyse métier. Savoir qu'un utilisateur a utilisé le chat 2h après un e-mail est un signal d'urgence et d'insatisfaction client capital. Conserver la ligne avec dedup_status = "cross_channel_duplicate" permet à la fois d'isoler l'échantillon pour l'entraînement IA (éviter le surapprentissage sur les mêmes phrases) tout en gardant l'historique complet pour l'analytique produit.

## 2. La limite du Chat Anonyme : 
Si un log de chat ne contient pas d'adresse e-mail dans le champ sender, l'algorithme refuse intelligemment la déduplication croisée pour éviter d'assimiler tous les visiteurs anonymes à une seule entité.

## 3. Optimisation des requêtes SQL : 
Dans la fonction ingest, plutôt que de charger les millions de lignes de la table demandes, la sélection restreint l'historique à la fenêtre temporelle exacte du lot entrant (min_date et max_date +/- 48h), rendant l'exécution extrêmement stable face au passage à l'échelle.