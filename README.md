# P-CHARM :  Ahonetic charade generation
Lien de la démonstration du projet : https://youtu.be/HLZKZhoPZ6M

## Structure du projet

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