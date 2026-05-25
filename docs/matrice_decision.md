# Matrice de Décision — Choix technologique FastIA

Ce document présente l'arbitrage final pour les composants d'enrichissement de la pipeline FastIA, en comparant les performances techniques, la robustesse aux attaques et l'impact environnemental.

---

## 1. Comparatif : Détection de Langue

| Critère | Langdetect (Baseline) | FastText (LID) | XLM-RoBERTa (Transformer) |
| :--- | :---: | :---: | :---: |
| **Précision (Accuracy)** | 98% | **100%** | 100% |
| **Latence (ms/doc)** | ~6.73 ms | **~0.03 ms** | >150 ms |
| **Mémoire (RAM)** | ~60.5 MB | **< 1 MB** | > 1.2 GB |
| **Robustesse Homoglyphes** | Très Faible | **Moyenne** | Forte |
| **Impact Carbone** | Moyen | **Très Faible** | Élevé |

---

## 2. Comparatif : Analyse de Sentiment (Français)

| Critère | DistilCamembert | BERT Multilingual |
| :--- | :---: | :---: |
| **Précision (F1-Score)** | **0.89** | 0.52 |
| **Rapidité** | **Modérée** | Lente |
| **Taille Modèle** | **~260 MB** | ~700 MB |

---

## 3. Recommandations Finales

### Composant Langue : **FastText** (`lid.176.bin`)
* **Justification** : C'est le gagnant indiscutable du benchmark. Il est **220 fois plus rapide** que langdetect avec une précision quasi-parfaite. Son empreinte mémoire quasi-nulle permet un déploiement sur des instances très légères (éco-conception).
* **Risque** : Sensibilité résiduelle au bruit extrême, compensée par le "Sanitizer" préconisé dans le *Threat Model*.

### Composant Sentiment : **DistilCamembert**
* **Justification** : Le meilleur compromis pour le français. Il offre les performances d'un Transformer tout en étant distillé (plus léger et rapide que BERT). Il capture mieux les nuances (négations, sarcasmes légers) que les approches par mots-clés.
* **Risque** : Consommation CPU/GPU à surveiller lors des pics de charge.

---

## 4. Score de Décision Pondéré (Aide à l'arbitrage)

| Modèle | Performance (40%) | Robustesse (30%) | Éco-conception (30%) | **Note Finale /10** |
| :--- | :---: | :---: | :---: | :---: |
| **FastText** | 10 | 7 | 10 | **9.1** |
| **Langdetect** | 8 | 2 | 7 | **5.9** |
| **DistilCamembert**| 9 | 8 | 6 | **7.8** |

---

