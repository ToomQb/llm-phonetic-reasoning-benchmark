import pandas as pd
from phonemizer import phonemize
from collections import defaultdict
import random
import gc
import json 

class GenerateurAutomatique:
    def __init__(self, lexique_path):
        self.lexique_path = lexique_path
        self.MIN_FREQ_LIVRE = 0.5
        self.MIN_LEN_MOT = 2
        self.lexicon_ph = defaultdict(list)
        self.table_lemmes = {}
        self.mots_a_traiter_prets = [] 

    def _phonetiser(self, words):
        phons = phonemize(words, language="fr-fr", backend="espeak", strip=True, with_stress=False)
        if isinstance(phons, str): phons = [phons]
        return [p.replace(" ", "").replace("ː", "") for p in phons]

    def charger_lexique(self, nb_lettres_cible=7):
        print("--- Initialisation du Lexique ---")
        df = pd.read_csv(self.lexique_path, sep="\t")
        df = df[df["ortho"].notna()].copy()
        df["ortho"] = df["ortho"].str.lower()
        df["lemme"] = df["lemme"].str.lower()

        self.table_lemmes = dict(zip(df["ortho"], df["lemme"]))
        
        mask_composants = (df["freqlivres"] > self.MIN_FREQ_LIVRE) & (df["ortho"].str.len() >= self.MIN_LEN_MOT)
        df_comp = df[mask_composants].groupby("ortho").agg({'freqfilms2': 'max', 'lemme': 'first'}).reset_index()

        print(f"Phonétisation des composants ({len(df_comp)} mots)...")
        phons_comp = self._phonetiser(df_comp["ortho"].tolist())

        for w, p, f, l in zip(df_comp["ortho"], phons_comp, df_comp["freqfilms2"], df_comp["lemme"]):
            if p: self.lexicon_ph[p].append({'mot': w, 'score': f, 'lemme': l})

        cibles = df[df["ortho"].str.len() == nb_lettres_cible]["ortho"].unique().tolist()
        random.shuffle(cibles)
        
        print(f"Phonétisation des {len(cibles)} cibles...")
        phons_cibles = self._phonetiser(cibles)
        self.mots_a_traiter_prets = list(zip(cibles, phons_cibles))
        
        del df, df_comp
        gc.collect()

    def chercher(self, mot_cible, cible_ph, score_max_qualite=80.0, max_solutions=3):
        lemme_cible = self.table_lemmes.get(mot_cible, mot_cible)
        resultats = []
        compteur_essais = [0]

        # On modifie le backtrack pour passer 'chemin_ph' (les phonèmes trouvés)
        def backtrack(reste, chemin, chemin_ph, scores):
            if len(resultats) >= max_solutions: return
            compteur_essais[0] += 1
            if compteur_essais[0] > 1000: return 

            if not reste:
                if len(chemin) >= 2:
                    score_moyen = sum(scores) / len(scores)
                    if score_moyen < score_max_qualite:
                        # On stocke les mots ET leurs phonèmes
                        resultats.append({
                            "composants": chemin,
                            "composants_phonetique": chemin_ph
                        })
                return
            
            if len(chemin) >= 4: return

            for i in range(1, len(reste) + 1):
                son = reste[:i]
                if son in self.lexicon_ph:
                    options = sorted(self.lexicon_ph[son], key=lambda x: x['score'], reverse=True)[:3]
                    for item in options:
                        if item['mot'] != mot_cible and item['lemme'] != lemme_cible:
                            backtrack(
                                reste[i:], 
                                chemin + [item['mot']], 
                                chemin_ph + [son], # On garde la trace du son
                                scores + [item['score']]
                            )

        backtrack(cible_ph, [], [], [])
        return resultats

if __name__ == "__main__":
    SCORE_LIMITE = 80.0
    MAX_SOL_PAR_MOT = 5
    NB_LETTRES = 7
    
    gen = GenerateurAutomatique("Lexique383.tsv")
    gen.charger_lexique(nb_lettres_cible=NB_LETTRES)
    
    print(f"Début de la génération...")
    
    donnees_finales = []

    for i, (mot, phoneme) in enumerate(gen.mots_a_traiter_prets):
        sols = gen.chercher(mot, phoneme, score_max_qualite=SCORE_LIMITE, max_solutions=MAX_SOL_PAR_MOT)
        
        if sols:
            # Création de l'objet pour ce mot
            entree = {
                "mot_cible": mot.upper(),
                "phonetique": phoneme,
                "solutions": sols
            }
            donnees_finales.append(entree)

        if i % 100 == 0:
            print(f"Progression : {i}/{len(gen.mots_a_traiter_prets)}...")
            gc.collect()

    # Écriture du fichier JSON final
    with open("charades.json", "w", encoding="utf-8") as f:
        json.dump(donnees_finales, f, ensure_ascii=False, indent=4)

    print(f"\nTerminé ! {len(donnees_finales)} mots avec solutions enregistrés dans 'charades.json'.")