import csv
import requests
from functools import lru_cache
from phonemizer import phonemize
from urllib.parse import quote


# =========================
# NORMALISATION IPA
# =========================
def normalize_phon(phon):
    return (
        phon.replace(".", "")
            .replace("R", "ʁ")
            .replace("ɑ̃", "an")
            .replace("ɔ̃", "on")
            .replace("ɛ̃", "in")
            .replace("œ̃", "un")
            .strip()
    )


# =========================
# CHARGEMENT DU LEXIQUE 3
# =========================
def load_lexique(path):
    phon_to_words = {}

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            word = row["ortho"]
            phon = normalize_phon(row["phon"])

            # filtres linguistiques
            if len(word) < 2:
                continue
            if not word.isalpha():
                continue
            if not phon:
                continue

            phon_to_words.setdefault(phon, []).append(word)

    # on préfère les mots "riches" (balle > bal > bah)
    for phon in phon_to_words:
        phon_to_words[phon].sort(key=len, reverse=True)

    return phon_to_words


# =========================
# MOT → PHONÉTIQUE
# =========================
def word_to_phonetic(word):
    phon = phonemize(
        word,
        language="fr-fr",
        backend="espeak",
        strip=True,
        preserve_punctuation=False,
        with_stress=False,
        njobs=1
    )
    return normalize_phon(phon)


# =========================
# DÉCOMPOSITION PHONÉTIQUE
# =========================
def find_word_sequences(target_phon, phon_to_words, max_solutions=5):

    available_phons = set(phon_to_words.keys())
    max_len = max(len(p) for p in available_phons)

    @lru_cache(None)
    def dfs(remaining):
        if not remaining:
            return [[]]

        results = []
        for i in range(1, min(len(remaining), max_len) + 1):
            prefix = remaining[:i]
            if prefix in available_phons:
                for suffix in dfs(remaining[i:]):
                    results.append([prefix] + suffix)
                    if len(results) >= max_solutions:
                        return results
        return results

    phon_seqs = dfs(target_phon)

    return [
        [phon_to_words[p][0] for p in seq]
        for seq in phon_seqs[:max_solutions]
    ]


# =========================
# DÉFINITION WIKTIONNAIRE
# =========================
def get_definition(word):
    try:
        url = f"https://fr.wiktionary.org/api/rest_v1/page/summary/{quote(word)}"
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return "Définition indisponible"
        return r.json().get("extract", "Définition indisponible")
    except Exception:
        return "Définition indisponible"


# =========================
# PIPELINE PRINCIPAL
# =========================
def phonetic_wordplay(word, lexique_path):
    phon_to_words = load_lexique(lexique_path)
    target_phon = word_to_phonetic(word)

    sequences = find_word_sequences(target_phon, phon_to_words)

    results = []
    for seq in sequences:
        results.append([
            {"mot": w, "definition": get_definition(w)}
            for w in seq
        ])

    return results


# =========================
# TEST
# =========================
if __name__ == "__main__":
    results = phonetic_wordplay("balançoire", "Lexique383.tsv")

    for solution in results:
        print("➜ Solution :")
        for item in solution:
            print(f"  - {item['mot']} : {item['definition']}")
        print()
