import json
import torch
import mlflow
from collections import Counter
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer
)
from peft import LoraConfig, get_peft_model, TaskType

print("Imports OK")

# Détection automatique du device disponible
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

print(f"Device utilisé : {device}")

# Chargement du dataset
with open("dataset_fastia_module1.jsonl", "r", encoding="utf-8") as f:
    raw_data = [json.loads(line) for line in f]

print(f"Nombre d'exemples : {len(raw_data)}")
print("\nExemple :")
print(json.dumps(raw_data[0], ensure_ascii=False, indent=2))

### A COMPLÉTER ###
# Objectif : analyser la distribution des priorités
#
# 1. Construire la liste de toutes les priorités
priorites = [ex['output']['priorite'] for ex in raw_data]

# 2. Compter le nombre d'exemples par priorité
distribution_priorites = Counter(priorites)

# 3. Afficher le résultat
print("\nDistribution des priorités :")
for priorite, count in distribution_priorites.items():
    print(f"- {priorite} : {count}")

### A COMPLÉTER ###
# Objectif : analyser la longueur des demandes en entrée
#
# 1. Calculer la longueur en caractères de chaque champ 'input'
longueurs = [len(ex['input']) for ex in raw_data]

# 2. Calculer la longueur minimale, maximale et moyenne
longueur_minimale = min(longueurs)
longueur_maximale = max(longueurs)
longueur_moyenne = sum(longueurs) / len(longueurs)

# 3. Afficher les résultats
#
# Question : pourquoi la longueur des inputs est-elle importante
# pour le choix de MAX_LENGTH lors de la tokenisation ?
# Répondez dans un commentaire.

print(f"Longueur minimale  : {min(longueurs)} caractères")
print(f"Longueur maximale  : {max(longueurs)} caractères")
print(f"Longueur moyenne   : {longueur_moyenne:.0f} caractères")

# Votre réponse :
#   Si MAX_LENGTH est défini trop petit, le modèle ne verra pas la fin des phrases présentent dans 'input',
#   perdant ainsi des informations essentielles pour la classification ou la réponse.
#   Si MAX_LENGTH est défini trop grand, cela peut entraîner une utilisation inefficace de la mémoire et du temps de calcul,
#   surtout si la majorité des inputs sont courts. Il est donc important de choisir un MAX_LENGTH qui couvre la majorité des inputs sans être excessivement grand.


def build_prompt(exemple):
    """
    Transforme un exemple du dataset en prompt d'instruction.

    Args:
        exemple (dict): un exemple avec les clés 'input' et 'output'

    Returns:
        str: le prompt formaté
    """
    instruction = (
        "Tu es un assistant FastIA. "
        "Analyse la demande suivante et réponds uniquement en JSON valide "
        "avec les champs : categorie, priorite, reponse_suggeree.\n\n"
        f"Demande : {exemple['input']}"
    )
    reponse = json.dumps(exemple["output"], ensure_ascii=False)

    return f"<s>[INST] {instruction} [/INST] {reponse} </s>"


# Test sur le premier exemple
print(build_prompt(raw_data[0]))

### A COMPLÉTER ###
# Objectif : appliquer build_prompt à tous les exemples du dataset
#
# 1. Créer une liste 'prompts' contenant le prompt formaté de chaque exemple
# 2. Afficher la longueur de cette liste
# 3. Afficher le prompt du 5ème exemple pour vérification

prompts = [build_prompt(ex) for ex in raw_data]

print(f"Nombre de prompts : {len(prompts)}")
print("\nExemple (index 4) :")
print(prompts[4])


## 4. Tokenisation et split train/test
MODEL_ID = "meta-llama/Llama-3.2-1B"

TOKEN_ACCES = 'votre_token_huggingface_ici'  # Remplacez par votre token d'accès HuggingFace

# Chargement du tokenizer
# Un token d'accès HuggingFace est nécessaire pour ce modèle.
# Connectez-vous sur huggingface.co et acceptez les conditions d'utilisation Meta.
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, token=TOKEN_ACCES)
tokenizer.pad_token = tokenizer.eos_token

print(f"Taille du vocabulaire : {tokenizer.vocab_size} tokens")
print(f"Token de padding : {tokenizer.pad_token}")


MAX_LENGTH = 512

def tokenize(prompt):
    """
    Tokenise un prompt et prépare les labels pour l'entraînement.

    Args:
        prompt (str): le prompt formaté

    Returns:
        dict: input_ids, attention_mask, labels
    """
    result = tokenizer(
        prompt,
        truncation=True,
        max_length=MAX_LENGTH,
        padding="max_length"
    )
    result["labels"] = result["input_ids"].copy()
    return result


# Test sur un exemple
exemple_tokenise = tokenize(prompts[0])
print(f"Longueur tokenisée : {len(exemple_tokenise['input_ids'])} tokens")


### A COMPLÉTER ###
# Objectif : construire les jeux d'entraînement et de test
#
# 1. Créer un Dataset HuggingFace à partir de la liste 'prompts'
#    Indice : Dataset.from_dict({"text": prompts})
#
# 2. Tokeniser tous les exemples avec .map()
#    Indice : dataset.map(lambda x: tokenize(x["text"]))
#
# 3. Diviser en train (80%) et test (20%) avec .train_test_split()
#
# 4. Afficher la taille des deux jeux
#
# Question : pourquoi conserver un jeu de test séparé du jeu d'entraînement ?
# Répondez dans un commentaire.

dataset = Dataset.from_dict({"text": prompts})
dataset_tokenise = dataset.map(lambda x: tokenize(x["text"]), batched=True)
split = dataset_tokenise.train_test_split(test_size=0.2)

train_dataset = split["train"]
test_dataset = split["test"]

print(f"Entraînement : {len(train_dataset)} exemples")
print(f"Test         : {len(test_dataset)} exemples")

# Votre réponse :
# Conserver un jeu de test séparé est indispensable pour :
# 1. Évaluer la généralisation : Vérifier si le modèle a réellement appris à traiter 
#    des demandes, ou s'il a simplement mémorisé (overfitting) les exemples de l'entrainement.
# 2. Détecter l'overfitting : Si la perte (loss) baisse sur l'entrainement mais stagne ou 
#    remonte sur le test, le modèle devient trop spécifique et perd en utilité réelle.
# 3. Mesurer la performance réelle : Obtenir des métriques fiables sur des données 
#    qu'il n'a jamais vues, simulant ainsi son usage en production.


## 5. Chargement du modèle de base

# On charge Llama 3.2 1B sans modifier ses poids. A ce stade, c'est le modèle
# générique pré-entraîné par Meta sur des milliards de tokens.

# L'étape suivante (LoRA) va ajouter des couches adaptateurs légères sur ce modèle
# sans toucher aux poids originaux.

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    device_map="auto",
    token=TOKEN_ACCES
)

total_params = sum(p.numel() for p in model.parameters())
print(f"Paramètres totaux : {total_params:,}")


## 6. Configuration LoRA

# LoRA (Low-Rank Adaptation) est une technique de fine-tuning efficace : plutôt que
# de modifier tous les poids du modèle, on ajoute de petites matrices d'adaptation
# sur certaines couches.

# Résultat : on entraîne seulement environ 1% des paramètres du modèle.

# Paramètres clés :
# - r : rang des matrices — plus élevé = plus de capacité, plus de mémoire
# - lora_alpha : facteur d'échelle — généralement égal à 2 * r
# - target_modules : couches sur lesquelles appliquer LoRA
# - lora_dropout : régularisation pour éviter le sur-apprentissage

lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none"
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

### A COMPLÉTER ###
# Objectif : calculer et afficher le pourcentage de paramètres entraînables
#
# 1. Calculer le nombre de paramètres entraînables (requires_grad == True)
# 2. Calculer le total des paramètres
# 3. Calculer et afficher le pourcentage
#
# Question : quel est l'avantage de n'entraîner qu'une fraction des paramètres
# sur un hardware avec une mémoire limitée ?
# Répondez dans un commentaire.

trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total = sum(p.numel() for p in model.parameters())
pct = (trainable / total) * 100 if total > 0 else 0

print(f"Paramètres entraînables : {trainable:,} ({pct:.2f}% du total)")

# Votre réponse :
# L'avantage principal de n'entraîner qu'une fraction des paramètres (LoRA) est la réduction 
# drastique de la mémoire VRAM nécessaire. 
# En effet, lors de l'entraînement standard, on doit stocker les "états de l'optimiseur" 
# (comme Adam) pour CHAQUE paramètre entraînable. 
# - Entraînement complet : Mémoire colossale car on stocke les gradients pour les milliards de paramètres.
# - LoRA : On ne stocke les gradients et les états de l'optimiseur que pour les 1% de paramètres ajoutés.
# Cela permet de fine-tuner des modèles massifs sur des cartes graphiques grand public (ex: RTX 3060/4060)
# au lieu de serveurs industriels.


## 7. Entraînement

# On lance le run d'entraînement. Chaque run est tracké dans MLflow pour conserver
# une trace des paramètres et des métriques.

# Hyperparamètres à retenir :
# - learning_rate : vitesse d'apprentissage
# - num_train_epochs : nombre de passages sur le dataset complet
# - per_device_train_batch_size : nombre d'exemples traités simultanément

mlflow.set_experiment("fastia-llama-finetuning")

TRAINING_CONFIG = {
    "learning_rate": 2e-4,
    "num_train_epochs": 3,
    "per_device_train_batch_size": 4,
    "run_name": "run1-lr2e4-3epochs"
}

with mlflow.start_run(run_name=TRAINING_CONFIG["run_name"]):

    mlflow.log_params({
        "model_id": MODEL_ID,
        "lora_r": 8,
        "lora_alpha": 16,
        "lora_dropout": 0.05,
        "learning_rate": TRAINING_CONFIG["learning_rate"],
        "num_train_epochs": TRAINING_CONFIG["num_train_epochs"],
        "batch_size": TRAINING_CONFIG["per_device_train_batch_size"],
        "dataset_size": len(raw_data),
        "max_length": MAX_LENGTH
    })

    training_args = TrainingArguments(
        output_dir="./model_run1",
        num_train_epochs=TRAINING_CONFIG["num_train_epochs"],
        per_device_train_batch_size=TRAINING_CONFIG["per_device_train_batch_size"],
        learning_rate=TRAINING_CONFIG["learning_rate"],
        logging_steps=10,
        save_strategy="epoch",
        eval_strategy="epoch",
        fp16=torch.cuda.is_available(),
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        processing_class=tokenizer
    )

    result = trainer.train()

    mlflow.log_metric("train_loss", result.training_loss)
    eval_result = trainer.evaluate()
    mlflow.log_metric("eval_loss", eval_result["eval_loss"])

    print(f"Train loss : {result.training_loss:.4f}")
    print(f"Eval loss  : {eval_result['eval_loss']:.4f}")