import pandas as pd
from phonemizer import phonemize
from collections import defaultdict
import random
import gc  

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

        # Préparation des mots cibles
        cibles = df[df["ortho"].str.len() == nb_lettres_cible]["ortho"].unique().tolist()
        random.shuffle(cibles)
        
        print(f"Phonétisation des {len(cibles)} cibles (prévention crash)...")
        phons_cibles = self._phonetiser(cibles)
        self.mots_a_traiter_prets = list(zip(cibles, phons_cibles))
        
        del df
        del df_comp
        gc.collect()
        print(f"Prêt à analyser {len(self.mots_a_traiter_prets)} mots.")

    def chercher(self, mot_cible, cible_ph, score_max_qualite=80.0, max_solutions=3):
        lemme_cible = self.table_lemmes.get(mot_cible, mot_cible)
        resultats = []
        compteur_essais = [0]

        def backtrack(reste, chemin, scores):
            if len(resultats) >= max_solutions: return
            compteur_essais[0] += 1
            if compteur_essais[0] > 1000: return 

            if not reste:
                if len(chemin) >= 2:
                    score_moyen = sum(scores) / len(scores)
                    if score_moyen < score_max_qualite:
                        resultats.append((chemin, score_moyen))
                return
            
            if len(chemin) >= 4: return

            for i in range(1, len(reste) + 1):
                son = reste[:i]
                if son in self.lexicon_ph:
                    options = sorted(self.lexicon_ph[son], key=lambda x: x['score'], reverse=True)[:3]
                    for item in options:
                        if item['mot'] != mot_cible and item['lemme'] != lemme_cible:
                            backtrack(reste[i:], chemin + [item['mot']], scores + [item['score']])

        backtrack(cible_ph, [], [])
        return resultats

if __name__ == "__main__":
    SCORE_LIMITE = 80.0
    MAX_SOL_PAR_MOT = 10
    NB_LETTRES = 7
    FREQUENCE_NETTOYAGE = 500 
    
    gen = GenerateurAutomatique("Lexique383.tsv")
    gen.charger_lexique(nb_lettres_cible=NB_LETTRES)
    
    print(f"Début de la génération...")

    with open("charades_complet.txt", "w", encoding="utf-8") as f:
        for i, (mot, phoneme) in enumerate(gen.mots_a_traiter_prets):
            sols = gen.chercher(mot, phoneme, score_max_qualite=SCORE_LIMITE, max_solutions=MAX_SOL_PAR_MOT)
            
            if sols:
                f.write(f"MOT {i+1} : {mot.upper()}\n")
                for s in sols:
                    f.write(f"  [{s[1]:.2f}] {' + '.join(s[0])}\n")
                f.write("-" * 25 + "\n")
                f.flush() 

            if i % 100 == 0:
                print(f"Progression : {i}/{len(gen.mots_a_traiter_prets)} traités...")

            # --- NETTOYAGE MÉMOIRE TOUS LES 500 MOTS ---
            if i > 0 and i % FREQUENCE_NETTOYAGE == 0:
                print(f"--- [INFO] Vidage mémoire (Mot {i}) ---")
                gc.collect()

    print("\nTerminé ! Consultez 'charades_complet.txt'.")