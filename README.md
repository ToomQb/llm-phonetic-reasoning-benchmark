# P-CHARM :  Phonetic CHArade Reasoning Model for LLMs

> Can LLMs reason about sounds, not just words?

P-CHARM is a research project investigating the **phonetic reasoning 
capabilities of Large Language Models** through the case study of 
French phonetic charades — structured puzzles requiring explicit 
sound-level decomposition and recomposition.

Présentation du projet : https://youtu.be/HLZKZhoPZ6M

Rapport de recherche complet : https://www.overleaf.com/read/fhbsxfhmhhfd#80b575

---

## Contexte et motivation

Malgré leurs performances impressionnantes sur des tâches de raisonnement logique et textuel, les LLMs présentent des faiblesses importantes lorsqu'un raisonnement phonétique explicite est requis. Les charades constituent un cadre expérimental particulièrement adapté pour étudier ce phénomène : elles nécessitent de décomposer un mot cible en segments phonétiques, d'associer chaque segment à un indice sémantique, puis de recomposer le mot original.

À notre connaissance, **aucun travail antérieur n'avait spécifiquement étudié les performances des LLMs sur des puzzles phonétiques structurés**, ni proposé de méthodes pour améliorer ce type de raisonnement.

---

## Contributions

- **Dataset original** de charades phonétiques en français, construit via une pipeline combinatoire semi-automatique basée sur des représentations IPA
- **Protocole d'évaluation** basé sur la similarité phonétique (représentations de traits phonologiques via PanPhon + distance de Levenshtein)
- **Analyse empirique** des stratégies de prompting (base vs. guidé) sur plusieurs modèles Gemini
- **Application web** pour générer et évaluer des charades interactivement

---

## Résultats clés

Les expérimentations ont été menées sur **Gemini 2.5 Flash** et **Gemini 2.5 Flash Lite**.

| Stratégie | Score phonétique moyen | Distance de Levenshtein moyenne |
|---|---|---|
| Base prompting | 3.46 | 7.83 |
| Guided prompting (Few-Shot + CoT) | **0.75** | **2.67** |

> Un score de 0 est optimal. Le guided prompting réduit le score 
> phonétique de **78%** et la distance de Levenshtein de **66%**.

**Observations qualitatives :**
- Le base prompting génère fréquemment des mots inexistants ou morphologiquement invalides
- Le guided prompting contraint le modèle vers des items lexicaux valides et un raisonnement plus explicite
- Les performances restent sensibles à la complexité phonétique du mot cible (ex. *hippopotame* vs *enfant*)

---

## Méthodologie

### Tâche
Génération de charades phonétiques : le modèle doit décomposer un mot cible en segments phonétiques et associer chaque segment à un indice sémantique cohérent.

### Stratégies de prompting comparées
- **Base prompting** : génération directe sans guidance
- **Guided prompting** : combinaison few-shot + chain-of-thought encourageant un raisonnement phonétique explicite étape par étape

### Construction du dataset
Pipeline semi-automatique :
1. Sélection du mot cible depuis un dictionnaire lexical
2. Conversion en représentation phonétique IPA
3. Segmentation en sous-unités phonétiques valides
4. Recherche de mots correspondant phonologiquement à chaque segment

---

## Stack technique

- **LLMs** : Gemini 2.5 Flash, Gemini 2.5 Flash Lite (via API Google)
- **Phonétique** : PanPhon (traits phonologiques), distance de Levenshtein
- **Application** : Flask, LangChain, SQLite
- **Évaluation** : métriques phonétiques custom, analyse qualitative

---

## Structure du projet Charade-llm-app

```text
.
├── app.py                  # Application Flask principale
├── generate_charade.py     # Logique de génération des charades
├── config.py               # Configuration (clé API, paramètres LLM)
├── charades.db             # Base de données SQLite (auto-générée)
├── templates/
│   └── index.html          # Interface web
├── static/
│   ├── css/
│   └── js/
└── README.md
└── .env
└── requirements.txt
```

## Installation

### Environment setup

```bash
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows
```
> NB : Créer un fichier `.env` pour mettre les clés d'API de Google et le nom du modèle à utiliser
```conf
# .env file
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
MODEL_NAME=gemini-2.5-flash
```

### Installer les dépendances

```bash
pip install -r requirements.txt
```

*(si `requirements.txt` n’existe pas)* :

```bash
pip install flask langchain langchain-google-genai python-dotenv panphon
```

## Lancer l’application

```bash
python app.py
```

Ouvrir le navigateur à l’adresse : **[http://localhost:5000](http://localhost:5000)**


## Base de données

* La base SQLite (`charades.db`) est créée automatiquement au lancement
* Table principale : `charades`
* Contient :

  * paramètres de génération
  * réponse brute du LLM
  * charade structurée
  * temps d’exécution
  * note et feedback utilisateur

## API disponibles

| Route           | Méthode | Description           |
| --------------- | ------- | --------------------- |
| `/`             | GET     | Interface principale  |
| `/generate`     | POST    | Générer une charade   |
| `/history`      | GET     | Historique paginé     |
| `/charade/<id>` | GET     | Détails d’une charade |
| `/rate/<id>`    | POST    | Noter une charade     |
| `/delete/<id>`  | DELETE  | Supprimer une charade |
| `/stats`        | GET     | Statistiques globales |

## Exemple de requête `/generate`

```json
{
  "difficulty": "medium",
  "prompt_type": "engineered",
  "num_segments": 3,
  "target_word": "ordinateur"
}
```

## Pour les utilisateurs Windows
Si vous obtenez l'erreur avec Windows : `UnicodeDecodeError: 'charmap' codec can't decode byte 0x90 in position 970: character maps to <undefined>`, c'est un problème de la librairie PanPhon sur Windows, dont l'encoding par défaut est `cp1252`, or il faut lire le fichier en `utf-8`
```python
# File ".venv\Lib\site-packages\panphon\featuretable.py", line 84,
# Read the file name with the phonemes and their feature specification
  with files("panphon").joinpath(fn).open(encoding="utf-8") as f: # Should add the encoding="utf-8" parameter HERE 
      df = pd.read_csv(f)  
```

---

## Perspectives

- Fine-tuning de LLMs sur le dataset pour un raisonnement phonétique plus robuste
- Extension à d'autres langues et systèmes phonologiques
- Évaluation de la généralisation à d'autres puzzles phonétiques (devinettes, jeux de mots, rimes)
