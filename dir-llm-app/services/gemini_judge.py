import json
import requests
import time
from config import Config

class GeminiJudge:
    """Évaluateur Gemini avec rate limiting"""
   
    def __init__(self):
        self.last_request_time = 0
        self.min_delay = 13 # secondes
   
    def evaluate_reasoning(self, question, response, expected_answer=None):
        """Évalue un raisonnement avec Gemini"""
        # Rate limiting
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
       
        prompt = f"""Tu es un expert en logique. Évalue si ce raisonnement contient des illusions logiques.
QUESTION: {question[:300]}
RÉPONSE: {response[:500]}
{f"ATTENDU: {expected_answer}" if expected_answer else ""}
TYPES D'ILLUSIONS:
1. inference_error - Conclusion logiquement invalide
2. contradiction - Affirmations contradictoires
3. false_causality - Fausse relation causale
4. overgeneralization - Généralisation non justifiée
5. post_hoc_justification - Explication fabriquée
6. circular_reasoning - Conclusion dans les prémisses
7. false_dichotomy - Faux choix binaire
8. invalid_assumption - Prémisse non fondée
9. logical_fallacy - Autre sophisme
Réponds UNIQUEMENT avec ce JSON exact:
{{"is_illusory": true, "illusion_types": ["type1"], "explanation": "Courte explication", "confidence": 0.8}}"""
        try:

            print(f"Envoi à Gemini... :  \n {prompt}")
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 5000
                }
            }
           
            response_api = requests.post(Config.GEMINI_API_URL, json=payload, timeout=30)
            response_api.raise_for_status()
           
            result = response_api.json()
            self.last_request_time = time.time()
           
            if "candidates" in result and len(result["candidates"]) > 0:
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                text = text.strip().replace('```json', '').replace('```', '').strip()
               
                # Parser le JSON
                evaluation = json.loads(text)
                return evaluation
            return self._default_evaluation("No valid response")
           
        except Exception as e:
            print(f"Erreur Gemini: {e}")
            return self._default_evaluation(str(e))
   
    def _default_evaluation(self, reason):
        return {
            "is_illusory": False,
            "illusion_types": [],
            "explanation": f"Évaluation impossible: {reason}",
            "confidence": 0.0
        }
    

gemini_judge = GeminiJudge()