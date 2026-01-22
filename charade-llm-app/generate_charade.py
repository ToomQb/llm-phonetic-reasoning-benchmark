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

PROMPT_CHARADE_SIMPLE = """Génère une charade phonétique en français de difficulté {difficulty}.

{target_word_instruction}

Retourne UNIQUEMENT un JSON avec cette structure exacte:
{{
  "id": "charade_XXX",
  "language": "fr",
  "difficulty": "{difficulty}",
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

Génère maintenant une charade."""


PROMPT_CHARADE_ENGINEERED = """Tu es un générateur de charades phonétiques. Suis strictement ces instructions pour créer une charade correcte, naturelle et devinable.

{target_word_instruction}

**ÉTAPES À SUIVRE (Chain of Thought) :**

1. **Choisir le mot final ("Mon tout")**
   {step_1_instruction}
   - Difficulté : {difficulty}
   - Écris une phrase simple pour décrire ce mot, qui sera "Mon tout".

2. **Transcrire le mot final en phonétique**
   - Utilise l'alphabet phonétique international (API) pour le mot final.
   - Exemple : Biscuit → /bis.kɥi/

3. **Découper le mot en morceaux phonétiques**
   - Divise le mot final en **2, 3 ou 4 morceaux phonétiques**.
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

**EXEMPLES (Few-shot learning) :**

**Exemple 1 :**
{{
  "id": "charade_001",
  "language": "fr",
  "difficulty": "easy",
  "target_word": "balançoire",
  "target_phonemes": ["ba", "lɑ̃", "swaʁ"],
  "target_ipa": "/ba.lɑ̃.swaʁ/",
  "clue_definition": "Siège suspendu pour s'amuser.",
  "segments": [
    {{
      "position": 1,
      "clue": "Mon premier est le contraire de haut",
      "answer_word": "bas",
      "answer_ipa": "/ba/",
      "phonemes": ["ba"]
    }},
    {{
      "position": 2,
      "clue": "Mon deuxième n'est pas rapide",
      "answer_word": "lent",
      "answer_ipa": "/lɑ̃/",
      "phonemes": ["lɑ̃"]
    }},
    {{
      "position": 3,
      "clue": "Mon troisième est le moment où le soleil se couche",
      "answer_word": "soir",
      "answer_ipa": "/swaʁ/",
      "phonemes": ["swaʁ"]
    }}
  ],
  "full_riddle_text": "Mon premier est le contraire de haut. Mon deuxième n'est pas rapide. Mon troisième est le moment où le soleil se couche. Mon tout est un siège suspendu pour s'amuser."
}}

**Exemple 2 :**
{{
  "id": "charade_002",
  "language": "fr",
  "difficulty": "easy",
  "target_word": "biscuit",
  "target_phonemes": ["bis", "kɥi"],
  "target_ipa": "/bis.kɥi/",
  "clue_definition": "Aliment sucré ou salé que l'on mange souvent au goûter.",
  "segments": [
    {{
      "position": 1,
      "clue": "Mon premier est un vent léger et frais",
      "answer_word": "bise",
      "answer_ipa": "/bis/",
      "phonemes": ["bis"]
    }},
    {{
      "position": 2,
      "clue": "Mon second est un pronom interrogatif pour poser une question sur une personne",
      "answer_word": "qui",
      "answer_ipa": "/kɥi/",
      "phonemes": ["kɥi"]
    }}
  ],
  "full_riddle_text": "Mon premier est un vent léger et frais. Mon second est un pronom interrogatif pour poser une question sur une personne. Mon tout est un aliment sucré ou salé que l'on mange souvent au goûter."
}}

**INSTRUCTIONS FINALES :**
- Génère maintenant UNE NOUVELLE charade différente des exemples
- Respecte EXACTEMENT le format JSON
- Assure-toi que la phonétique est correcte
- Varie le nombre de segments (2 à 4)
- Réponds UNIQUEMENT avec le JSON, sans texte avant ou après
- Difficulté : {difficulty}

Génère la charade :"""


CHARADE_CONTEXT = """
PARAMÈTRES DE GÉNÉRATION :
    Difficulté : {difficulty}
    Nombre de segments souhaités : {num_segments}
    {target_word_context}
"""


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
        target_word_instruction = f"**IMPORTANT : Tu DOIS créer une charade pour le mot '{target_word}'.**"
        step_1_instruction = f"- Utilise OBLIGATOIREMENT le mot : **{target_word}**"
        target_word_context = f"Mot cible imposé : {target_word}"
    else:
        target_word_instruction = ""
        step_1_instruction = "- Sélectionne un mot naturel et courant en français (nom commun ou composé simple), avec **au moins 2 syllabes**."
        target_word_context = "Aucun mot cible imposé (génération libre)"
    
    # Choisir le prompt et la température
    if use_prompt_engineering:
        instruction = PROMPT_CHARADE_ENGINEERED.format(
            difficulty=difficulty,
            target_word_instruction=target_word_instruction,
            step_1_instruction=step_1_instruction
        )
        temperature = kwargs.get('temperature', 0.7)
        prompt_type = "engineered"
    else:
        instruction = PROMPT_CHARADE_SIMPLE.format(
            difficulty=difficulty,
            target_word_instruction=target_word_instruction
        )
        temperature = kwargs.get('temperature', 0.8)
        prompt_type = "simple"
    
    # Construire le contexte
    context = CHARADE_CONTEXT.format(
        difficulty=difficulty,
        num_segments=num_segments,
        target_word_context=target_word_context
    )
    
    # Créer le LLM
    llm = ChatGoogleGenerativeAI(
        model=Config.MODEL_NAME,
        google_api_key=Config.GEMINI_API_KEY,
        temperature=temperature
    )
    
    # Créer le prompt template
    prompt = ChatPromptTemplate.from_template(
        """Instruction :
{instruction}

Voici le contexte à analyser :
{context}"""
    )
    
    # Créer la chaîne
    chain = prompt | llm | StrOutputParser()
    
    try:
        import time
        start_time = time.time()
        
        answer_text = chain.invoke({
            "instruction": instruction,
            "context": context
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
