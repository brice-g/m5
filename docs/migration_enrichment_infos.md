## Stratégie de Base de Données & Maintenance

### A. Justification du design `Nullable=True` (Zéro Downtime & Backward-Compatibility)
Toutes les nouvelles colonnes sont configurées explicitement à `nullable=True` pour trois raisons architecturales majeures :

* **Zéro Verrouillage Lock Bloquant** : Sous PostgreSQL, l'ajout d'une colonne avec une contrainte `NOT NULL` et une valeur par défaut force la réécriture de la table ou un verrouillage lourd (`AccessExclusiveLock`) qui figerait l'ingestion des flux `mbox`/`chat` en production. Le mode *Nullable* s'exécute de manière instantanée.
* **Backward-Compatibility de l'Application** : L'ancien code (du Module 3) qui effectue des insertions (`INSERT INTO demandes (...)`) continuera de fonctionner parfaitement sans lever d'erreur de base de données, même s'il n'a pas encore connaissance des nouveaux champs d'enrichissement.
* **Enrichissement Asynchrone** : Au moment de la création physique d'une demande par un *loader*, les modèles IA n'ont pas encore analysé le texte. Les colonnes doivent être nulles temporairement avant que la pipeline n'y injecte les scores.

### B. Stratégie d'Indexation Sélectionnée
* `idx_demandes_langue` : Indispensable pour accélérer les requêtes de routage linguistique des équipes de support internationales et pour isoler l'historique non-français.
* `idx_demandes_routed_priority` : Cet index additionnel est crucial car le CRM et les API de distribution des tâches interrogeront en boucle la base sur le critère `WHERE routed_priority = 'high_negative'`. Un index de type **B-Tree** standard garantit une latence de lecture sous la milliseconde pour les agents.

### C. Stratégie de Backfill (Traitement de l'Historique)
Pour traiter les milliers de lignes déjà existantes en base de données de manière éco-conçue, la politique adoptée interdit le traitement "au fil de l'eau" (*row-by-row*) :

* **Risque identifié** : Lancer un script qui fait un `UPDATE` ligne par ligne en appelant les modèles va saturer la mémoire, générer d'immenses fichiers de logs de transaction (WAL) sur PostgreSQL, et créer une surcharge CPU inutile.
* **Solution retenue (Batching)** : Développement d'un script de maintenance dédié s'exécutant en heures creuses. Il sélectionnera les demandes par blocs (`BATCH_SIZE = 500`) où `enriched_at IS NULL`, concaténera les requêtes et mettra à jour la base de données en une seule transaction par lot.