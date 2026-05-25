import pandas as pd
import json
import random
from typing import List, Dict
from transformers import pipeline
from loguru import logger

# --- Imports de tes modules locaux ---
from .load import load_jsonl
from .validate import validate
from .anonymize import anonymize_data

class DataAugmentor:
    def __init__(self, model_id="meta-llama/Llama-3.2-1B"):
        self.stats = {
            "Gabarits_Haute": 0, 
            "Paraphrase_Urgence": 0, 
            "Paraphrase_Long": 0
        }
        self.rejets = {"parsing_json": 0, "validation": 0, "revue": 0}
        
        print(f"Chargement du modèle {model_id}...")
        self.llm = pipeline("text-generation", model=model_id, device_map="auto")

    def _get_few_shot_prompt(self, mode: str, text: str) -> str:
        consigne_commune = (
            "Tu es un assistant IA expert. Ta tâche est de réécrire le texte fourni. "
            "Tu dois OBLIGATOIREMENT répondre avec un objet JSON strict. N'ajoute AUCUN texte avant ou après le JSON."
        )
        
        if mode == "urgence":
            examples = (
                'Entrée: "Je voudrais les tarifs."\n'
                'Sortie:\n{"input": "URGENT : J\'ai besoin des tarifs immédiatement pour un client en attente.", "reponse_suggeree": "Voici nos tarifs. Je traite votre demande en priorité."}\n'
            )
            instruction = f'Rend ce message TRÈS URGENT : "{text}"'
        else:
            examples = (
                'Entrée: "Merci de m\'envoyer le catalogue."\n'
                'Sortie:\n{"input": "Bonjour, je me permets de vous solliciter car je souhaiterais recevoir votre catalogue complet ainsi que les conditions de vente détaillées.", "reponse_suggeree": "C\'est avec plaisir. Vous trouverez le catalogue et nos CGV en pièce jointe de ce mail."}\n'
            )
            instruction = f'Développe ce message (env. 180 caractères) : "{text}"'

        return f"{consigne_commune}\n\n{examples}\n{instruction}\nSortie:\n{{"

    def generate_with_templates(self, count: int) -> List[Dict]:
        new_data = []
        noms = ["[NOM]", "un client", "la direction"]
        sujets = ["le catalogue", "la fiche technique", "le rapport"]
        
        for _ in range(count):
            nom = random.choice(noms)
            sujet = random.choice(sujets)
            text = f"Besoin de {sujet} pour {nom} avant mon RDV de {random.randint(14, 17)}h, c'est urgent."
            
            new_data.append({
                "input": text,
                "categorie": "Information générale",
                "priorite": "haute",
                "reponse_suggeree": f"Voici {sujet} demandé. Je reste disponible pour votre RDV.",
                "source": "synthetic"
            })
        self.stats["Gabarits_Haute"] += count
        return new_data

    def paraphrase_llm(self, df: pd.DataFrame, target_count: int, mode: str) -> List[Dict]:
        new_data = []
        base_samples = df.sample(min(target_count, len(df))).to_dict('records')
        
        for item in base_samples:
            prompt = self._get_few_shot_prompt(mode, item['input'])
            
            outputs = self.llm(
                prompt, 
                max_new_tokens=150, 
                temperature=0.9, 
                top_p=0.95, 
                do_sample=True,
                return_full_text=False
            )
            
            raw_output = "{" + outputs[0]['generated_text'].strip()
            
            try:
                raw_output = raw_output.replace("```json", "").replace("```", "").strip()
                generated_json = json.loads(raw_output)
                
                new_data.append({
                    "input": generated_json.get("input", ""),
                    "categorie": item['categorie'],
                    "priorite": "haute" if mode == "urgence" else item['priorite'],
                    "reponse_suggeree": generated_json.get("reponse_suggeree", ""),
                    "source": "synthetic"
                })
            except json.JSONDecodeError:
                logger.warning(f"Échec parsing JSON. Chaîne obtenue : {raw_output}")
                self.rejets["parsing_json"] += 1
                continue
            
        key = "Paraphrase_Urgence" if mode == "urgence" else "Paraphrase_Long"
        self.stats[key] += len(new_data)
        return new_data

    def run(self, original_df: pd.DataFrame) -> pd.DataFrame:
        raw_synthetic = []
        
        print("\n[1/4] Génération des données synthétiques...")
        raw_synthetic += self.generate_with_templates(20)
        raw_synthetic += self.paraphrase_llm(original_df, 24, "urgence")
        info_df = original_df[original_df['categorie'] == "Information générale"]
        raw_synthetic += self.paraphrase_llm(info_df, 10, "long")
        
        synth_df = pd.DataFrame(raw_synthetic)
        
        print("[2/4] Application des sécurités d'anonymisation...")
        synth_df = anonymize_data(synth_df)
        
        print("[3/4] Validation du schéma Brief 2...")
        valid_synth_df = validate(synth_df)
        # valid_synth_df = synth_df # Remplacer par l'appel réel à validate
        self.rejets['validation'] = len(synth_df) - len(valid_synth_df)
        
        # --- ÉTAPE 4 : REVUE MANUELLE ---
        print("\n[4/4] Préparation de la revue manuelle...")
        sample_size = max(1, int(len(valid_synth_df) * 0.10))
        revue_df = valid_synth_df.sample(sample_size)
        
        csv_path = "revue_echantillon.csv"
        revue_df.to_csv(csv_path, index=False, encoding="utf-8")
        
        print(f"\n" + "!"*50)
        print(f" ACTION REQUISE : REVUE DE QUALITÉ")
        print(f" Un échantillon de {sample_size} lignes a été généré.")
        print(f" Fichier à consulter : {csv_path}")
        print(f"!"*50 + "\n")
        
        # Blocage de l'exécution en attente de l'utilisateur
        while True:
            reponse = input("As-tu vérifié le fichier CSV ? Valides-tu l'intégration de ce lot entier ? (y/n) : ").lower().strip()
            
            if reponse == 'y':
                print("\n✅ Lot validé. Intégration en cours...")
                original_df['source'] = 'original'
                final_df = pd.concat([original_df, valid_synth_df], ignore_index=True)
                break
                
            elif reponse == 'n':
                print("\n❌ Lot refusé. Les données synthétiques sont écartées.")
                self.rejets['revue'] = len(valid_synth_df) # On comptabilise tout le lot comme rejeté
                final_df = original_df.copy()
                if 'source' not in final_df.columns:
                    final_df['source'] = 'original'
                break
                
            else:
                print("⚠️ Réponse non reconnue. Merci de taper 'y' pour Oui ou 'n' pour Non.")
        
        self.print_report()
        return final_df

    def print_report(self):
        print("\n" + "="*40)
        print("RAPPORT D'AUGMENTATION")
        print("="*40)
        print("--- GÉNERÉS ---")
        for k, v in self.stats.items():
            print(f"- {k.replace('_', ' ')} : {v}")
            
        print("\n--- REJETS ---")
        print(f"- Erreurs de format LLM (JSON) : {self.rejets['parsing_json']}")
        print(f"- Rejetés par la validation Brief 2 : {self.rejets['validation']}")
        print(f"- Rejetés lors de la revue manuelle : {self.rejets['revue']}")
        
        total_genere = sum(self.stats.values()) - self.rejets['parsing_json'] - self.rejets['validation']
        
        if self.rejets['revue'] > 0:
            print(f"\n=> TOTAL SYNTHÉTIQUE INTÉGRÉ : 0 (Lot refusé)")
        else:
            print(f"\n=> TOTAL SYNTHÉTIQUE INTÉGRÉ : {total_genere}")
        print("="*40)

# --- Point d'entrée de ton script ---
if __name__ == "__main__":
    df_initial = load_jsonl("data/processed/dataset_fastia_clean_v1.jsonl")
    augmentor = DataAugmentor()
    df_enrichi = augmentor.run(df_initial)
    df_enrichi.to_json("data/processed/dataset_augmente.jsonl", orient="records", lines=True, force_ascii=False)