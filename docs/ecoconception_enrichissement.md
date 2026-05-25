### 1. Arbitrage Qualité / Ressources : L'avantage des modèles distillés locaux
Pour satisfaire le besoin métier sans faire exploser l'empreinte carbone ou introduire des dépendances coûteuses, les options frugales et locales ont été systématiquement privilégiées à qualité équivalente :
* **Pour la détection de la langue :** Utilisation de `langdetect` / `fasttext` en local sur CPU au lieu d'appels à une API LLM commerciale (ex. GPT-4o mini). La latence s'effondre à **~15 ms par ligne** (énergie divisée par plus de 30) pour une justesse équivalente sur des phrases complètes.
* **Pour l'analyse de sentiment :** Utilisation d'un modèle d'encodeur distillé comme `cmarkea/distilcamembert-base-sentiment` (~80 millions de paramètres) plutôt qu'un LLM génératif local de 8 milliards de paramètres (ex. Llama-3). L'inférence s'exécute directement sur CPU standard sans requérir de GPU dédié, divisant la consommation d'énergie par plus de 10.

### 2. Filtrage en Amont et Idempotence : Le calcul le plus vert est celui qu'on ne fait pas
* **Idempotence stricte :** La pipeline applique un filtre SQL au démarrage (`WHERE langue_confidence IS NULL OR sentiment_score IS NULL`) pour exclure automatiquement de l'analyse l'historique déjà enrichi ou stable.
* **Filtrage par canal (Data Minimization) :** L'analyse empirique montre que le canal `email` (qui représente **82 % du volume global**) est composé à 100 % de messages en français. **Règle d'éco-conception :** l'étape `enrich_language` est configurée pour s'activer *uniquement* sur les canaux `web` et `chat`, économisant instantanément **82 % d'appels superflus**.

### 3. Estimation Énergétique et Carbone (Ré-enrichissement de l'historique)
Pour un traitement complet "one-off" sur un historique de **100 000 lignes** en appliquant la méthodologie du framework *Green Algorithms* (sur 1 cœur CPU standard avec un TDP moyen de 30W) :
* **Temps de calcul modélisé :** ~4,5 min pour la langue (sur Web/Chat) + ~75 min pour le sentiment (sur tout le dataset) = **~80 minutes au total** (1,33 heure).
* **Consommation électrique :** $30\text{ W} \times 1,33\text{ h} = 40\text{ Wh} = \mathbf{0.04\text{ kWh}}$.
* **Émissions Carbone (Mix électrique français $\approx 50\text{g CO}_2\text{e/kWh}$) :** **$\mathbf{2.0\text{ g CO}_2\text{e}}$** (l'équivalent de rouler moins de 15 mètres avec une voiture thermique standard).

**Arbitrage & ROI :** L'opération est **très rentable** sur le plan environnemental pour aligner l'historique des indicateurs métiers dans les tableaux de bord de reporting. Néanmoins, elle ne vaut la peine *que* si les équipes métiers exploitent activement les tendances du passé ; si l'objectif est purement le routage opérationnel en temps réel, cette dépense énergétique (bien que minime) doit être évitée.