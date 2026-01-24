import json
from typing import Dict, Optional
from config import Config

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# =====================================================
# UTILITIES
# =====================================================

def extract_json_from_text(answer_text: str) -> dict:
    """Extract JSON from model output."""
    # Nettoyer les balises markdown
    answer_text = answer_text.replace('```json', '').replace('```', '').strip()
    
    start = answer_text.find("{")
    end = answer_text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return {}

    try:
        return json.loads(answer_text[start:end + 1])
    except json.JSONDecodeError:
        return {}


# =====================================================
# PROMPTS
# =====================================================

PROMPT_CHARADE_SIMPLE = """Génère une charade en français {target_word_instruction} et donne les réponses avec."""

PROMPT_EXTRACT_CHARADE_JSON = """Pour la charade donnée, extrait les informations ci-dessous au format JSON.

Voici la charade : 
{charade}

Retourne UNIQUEMENT un JSON avec cette structure exacte:
{{
  "id": "charade_XXX",
  "language": "fr",
  "difficulty": "difficulty",
  "target_word": "le mot final",
  "target_phonemes": ["phonème1", "phonème2"],
  "target_ipa": "/transcription IPA complète/",
  "clue_definition": "Définition du mot final",
  "segments": [
    {{
      "position": 1,
      "clue": "Mon premier est...",
      "answer_word": "mot réponse",
      "answer_ipa": "/ipa/",
      "phonemes": ["phonème"]
    }}
  ],
  "full_riddle_text": "Mon premier... Mon second... Mon tout..."
}}

Important:
- Ne change pas la définition donnée pour chaque mot dans la charade.
- Pour les segments.answer_ipa donne la phonétique de chaque mot à deviner (si ce n'est pas donné dans la charade d'en haut.), mais ne décompose pas le mot final en petits morceaux.
- Ne recrée pas la charade juste extrait les informations utiles pour le JSON.

"""


PROMPT_CHARADE_ENGINEERED = """Génère une charade en français {target_word_instruction}.

**ÉTAPES À SUIVRE (Chain of Thought) :**

1. **Choisir le mot final ("Mon tout")**
   - Écris une phrase simple pour décrire ce mot, qui sera "Mon tout".

2. **Transcrire le mot final en phonétique**
   - Utilise l'alphabet phonétique international (API) pour le mot final.
   - Exemple : Biscuit → /bis.kɥi/

3. **Découper le mot en morceaux phonétiques de mots existants dans le dictionnaire**
   - Divise le mot final en **2, 3 ou 4 morceaux phonétiques**.
   - Assure toi que chaque morceaux de phonétique que tu décides de prendre et de former, c'est un mot mais pas du bruit ou une lettre.
   - Chaque morceau doit être **prononçable individuellement**, peut combiner plusieurs sons, mais **tous les sons du mot final doivent être utilisés**.
   - Évite de deviner juste une lettre isolée.

4. **Trouver un mot réel pour chaque morceau**
   - Pour chaque morceau phonétique, trouve un **mot réel ou facilement compréhensible** dont la prononciation correspond approximativement au morceau.
   - Chaque mot doit avoir une **description claire et simple**.
   - Exemple : /bis/ → Bise (vent léger), /kɥi/ → Qui (pronom interrogatif)

5. **Construire la charade**
   - Formule la charade en listant chaque morceau :
     - Mon premier est ...
     - Mon second est ...
     - Mon troisième est ...
     - Mon tout est ...

**Exemple de génération(Few-shot learning) :**

Exemple de charade 1 :
- Etape 1 : 
    - Mot final choisi: Charade 
    - Définition du mot choisi: Mon tout est une devinette.
- Etape 2: 
    - Transcription du mot final 'Charade' en phonétique = \ʃa.ʁad\
- Etape 3: 
    - Diviser la phonétique du mot final 'Charade' en 3 morceaux : \ʃa\, \ʁa\ et \d\
- Etape 4: 
    - \ʃa\ = Chat (Mon premier est un animal de compagnie)
    - \ʁa\ = Rat (Mon second est un mammifère rongeur omnivore, qui vit généralement dans les égouts ou en laboratoire)
    - \d\ ≈ \dø\ = Deux (Mon troisième est le chiffre qui suit un)
- Etape 5:
    - Mon premier est un animal de compagnie. (Chat)
    - Mon second est un mammifère rongeur omnivore, qui vit généralement dans les égouts ou en laboratoire. (Rat)
    - Mon troisième est le chiffre qui suit un. (Deux)
    - Mon tout est une devinette. (Charade)

---
Exemple de charade 2 :
- Etape 1 : 
    - Mot final choisi: Cléopâtre 
    - Définition du mot choisi: Jules César aime bien mon tout.
- Etape 2: 
    - Transcription du mot final 'Cléopâtre' en phonétique = \kle.ɔ.patʁ\
- Etape 3: 
    - Diviser la phonétique du mot final 'Cléopâtre' en 3 morceaux : \kle\, \ɔ\ et \patʁ\
- Etape 4: 
    - \kle\ = Clé (Mon premier ouvre les portes)
    - \ɔ\ ≈ \o\ = Eau (Mon second se boit)
    - \patʁ\ = Pâtre (Mon troisième garde les troupeaux de bœufs, de vaches, de chèvres)
- Etape 5:
    - Mon premier ouvre les portes. (Clé)
    - Mon second se boit. (Eau)
    - Mon troisième garde les troupeaux de bœufs, de vaches, de chèvres. (Pâtre)
    - Jules César aime bien mon tout. (Cléopâtre)

Génère la charade avec ses réponses."""

# =====================================================
# MAIN API
# =====================================================

def generate_charade(
    difficulty: str = "easy",
    use_prompt_engineering: bool = False,
    num_segments: int = 3,
    target_word: Optional[str] = None,
    **kwargs
) -> Dict:
    """
    Génère une charade avec Gemini via LangChain.
    
    Args:
        difficulty: Niveau de difficulté (easy, medium, hard)
        use_prompt_engineering: Si True, utilise Few-shot + Chain of Thought
        num_segments: Nombre de segments souhaités (2-4)
        target_word: Mot cible optionnel pour la charade
        **kwargs: Paramètres supplémentaires (temperature, etc.)
    
    Returns:
        Dict contenant la charade générée ou une erreur
    """
    
    # Construire les instructions pour le mot cible
    if target_word:
        target_word_instruction = f"avec le mot '{target_word}'."
    else:
        target_word_instruction = f"avec un mot aléatoire."
    
    # Choisir le prompt et la température
    temperature = kwargs.get('temperature', 0.7)
    if use_prompt_engineering:
        instruction = PROMPT_CHARADE_ENGINEERED.format(
            target_word_instruction=target_word_instruction
        )
        prompt_type = "engineered"
    else:
        instruction = PROMPT_CHARADE_SIMPLE.format(
            target_word_instruction=target_word_instruction
        )
        prompt_type = "simple"
    
    # Créer le LLM
    llm = ChatGoogleGenerativeAI(
        model=Config.MODEL_NAME,
        google_api_key=Config.GEMINI_API_KEY,
        temperature=temperature
    )
    
    try:
        import time
        start_time = time.time()
        
        # Etape 1 : Générer la charade
        generate_charade_context = instruction
        generate_charade_prompt = ChatPromptTemplate.from_template("""{generate_charade_context}""")
        generate_charade_chain = generate_charade_prompt | llm | StrOutputParser()
        charade_text = generate_charade_chain.invoke({
            "generate_charade_context": generate_charade_context
        })

        print("charade_text", charade_text)
        # Etape 2: Transformer au format JSON attendu
        extract_json_context = PROMPT_EXTRACT_CHARADE_JSON.format(charade=charade_text)
        extract_json_prompt = ChatPromptTemplate.from_template("""{extract_json_context}""")
        extract_json_chain = extract_json_prompt | llm | StrOutputParser()
        answer_text = extract_json_chain.invoke({
            "extract_json_context": extract_json_context
        })
        
        execution_time = time.time() - start_time
        
        charade = extract_json_from_text(answer_text)
        
        # Compute the score
        print("Charade", charade)
        target_ipa = charade["target_ipa"].replace("/", "")
        generated_ipa = ".".join([segment["answer_ipa"].replace("/", "") for segment in charade["segments"]])
        print("target_ipa", target_ipa)
        print("generated_ipa", generated_ipa)

        feature_edit_distance = -1
        levenshtein_distance = -1
        try:
            from panphon.distance import Distance
            dist = Distance()
            feature_edit_distance = dist.feature_edit_distance(target_ipa, generated_ipa)
            levenshtein_distance = dist.levenshtein_distance(target_ipa, generated_ipa)

            print("feature_edit_distance", feature_edit_distance)
            print("levenshtein_distance", levenshtein_distance)

        except Exception as ex:
            print("PanPhon Library Error : ", ex)

        charade["feature_edit_distance"] = float(feature_edit_distance)
        charade["levenshtein_distance"] = float(levenshtein_distance)
        charade["generated_ipa"] = f"/{generated_ipa}/"


        return {
            "success": True,
            "charade": charade,
            "raw_response": answer_text,
            "execution_time": execution_time,
            "prompt_type": prompt_type
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "prompt_type": prompt_type
        }
