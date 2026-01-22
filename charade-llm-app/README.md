# 🎭 Charade Generator – Flask & LLM

Si vous obtenez l'erreur Avec Windows : `UnicodeDecodeError: 'charmap' codec can't decode byte 0x90 in position 970: character maps to <undefined>`, c'est un problème de la librairie PanPhon sur Windows, dont l'encoding par défaut est `cp1252`, or il faut lire le fichier en `utf-8`
```python
# File ".venv\Lib\site-packages\panphon\featuretable.py", line 84,
# Read the file name with the phonemes and their feature specification
  with files("panphon").joinpath(fn).open(encoding="utf-8") as f: # Should add the encoding="utf-8" parameter HERE 
      df = pd.read_csv(f)  
``` 


Application web Flask permettant de **générer, stocker, consulter et évaluer des charades** générées automatiquement à l’aide d’un **modèle de langage (LLM)** via **LangChain et Google Generative AI**.

Le projet inclut :

* Une interface web interactive
* Une génération de charades configurable
* Une base de données SQLite pour l’historique
* Des statistiques et un système de notation utilisateur

---

## 🚀 Fonctionnalités

* ✅ Génération de charades selon :

  * le **niveau de difficulté**
  * le **type de prompt** (simple ou prompt engineering)
  * le **nombre de segments**
  * un **mot cible optionnel**
* 💾 Sauvegarde automatique en base de données (SQLite)
* 📜 Historique paginé des charades
* 🔍 Consultation détaillée d’une charade
* ⭐ Système de notation (1 à 5) avec feedback
* 📊 Statistiques globales et par type de prompt
* 🗑️ Suppression de charades

---

## 🧠 Technologies utilisées

* **Python 3.9+**
* **Flask**
* **SQLite**
* **LangChain**
* **Google Generative AI (Gemini)**
* **HTML / CSS / JavaScript**
* **Jinja2**

---

## 📁 Structure du projet

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
```

---

## 🔑 Configuration de la clé API (IMPORTANT)

Chaque utilisateur doit **configurer sa propre clé API** dans le fichier `config.py`.



## 📦 Installation

### 1️⃣ Cloner le projet

```bash
git clone <url-du-repo>
cd charade-generator
```

### 2️⃣ Créer un environnement virtuel

```bash
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows
```

### 3️⃣ Installer les dépendances

```bash
pip install -r requirements.txt
```

*(si `requirements.txt` n’existe pas)* :

```bash
pip install flask langchain langchain-google-genai python-dotenv
```

---

## ▶️ Lancer l’application

```bash
python app.py
```

Puis ouvre ton navigateur à l’adresse :

👉 **[http://localhost:5000](http://localhost:5000)**

---

## 🗄️ Base de données

* La base SQLite (`charades.db`) est créée automatiquement au lancement
* Table principale : `charades`
* Contient :

  * paramètres de génération
  * réponse brute du LLM
  * charade structurée
  * temps d’exécution
  * note et feedback utilisateur

---

## 📊 API disponibles

| Route           | Méthode | Description           |
| --------------- | ------- | --------------------- |
| `/`             | GET     | Interface principale  |
| `/generate`     | POST    | Générer une charade   |
| `/history`      | GET     | Historique paginé     |
| `/charade/<id>` | GET     | Détails d’une charade |
| `/rate/<id>`    | POST    | Noter une charade     |
| `/delete/<id>`  | DELETE  | Supprimer une charade |
| `/stats`        | GET     | Statistiques globales |

---

## 🧪 Exemple de requête `/generate`

```json
{
  "difficulty": "medium",
  "prompt_type": "engineered",
  "num_segments": 3,
  "target_word": "ordinateur"
}
```
