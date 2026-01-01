import re
from typing import List, Dict, Callable

class SelfConsistencyChecker:
    """Vérifie la cohérence en générant plusieurs réponses"""
   
    def __init__(self, num_samples=5):
        self.num_samples = num_samples
   
    def check_consistency(self, question: str, generate_response_func: Callable, temperature=0.7) -> dict:
        """
        Génère N réponses et détecte les incohérences
       
        Args:
            question: La question à poser
            generate_response_func: Fonction qui génère une réponse (doit accepter question et temperature)
            temperature: Température pour la génération
       
        Returns:
            dict avec is_consistent, responses, final_answers, inconsistency_score
        """
        responses = []
        final_answers = []
       
        # Générer N réponses
        for i in range(self.num_samples):
            try:
                response = generate_response_func(question, temperature=temperature)
                responses.append(response)
               
                # Extraire la réponse finale
                final_answer = self._extract_final_answer(response)
                final_answers.append(final_answer)
            except Exception as e:
                print(f"Erreur génération {i}: {e}")
                responses.append(f"ERROR: {str(e)}")
                final_answers.append("ERROR")
       
        # Analyser la cohérence
        is_consistent, inconsistency_score, divergent_steps = self._analyze_consistency(
            responses, final_answers
        )
       
        return {
            'is_consistent': is_consistent,
            'inconsistency_score': inconsistency_score,
            'responses': responses,
            'final_answers': final_answers,
            'divergent_steps': divergent_steps,
            'num_samples': self.num_samples
        }
   
    def _extract_final_answer(self, response: str) -> str:
        """Extrait la conclusion finale d'une réponse"""
        # Chercher des patterns courants
        patterns = [
            r'(?:donc|ainsi|par conséquent|conclusion)[:\s]+(.+?)(?:\.|$)',
            r'(?:la réponse est|answer is)[:\s]+(.+?)(?:\.|$)',
            r'####\s*(.+?)(?:\.|$)',
        ]
       
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(1).strip()
       
        # Sinon, prendre la dernière phrase
        sentences = response.split('.')
        return sentences[-1].strip() if sentences else response[:100]
   
    def _analyze_consistency(self, responses: List[str], final_answers: List[str]) -> tuple:
        """Analyse la cohérence entre les réponses"""
        # Compter les réponses uniques
        unique_answers = set(final_answers)
       
        # Score d'incohérence = proportion de réponses différentes
        inconsistency_score = (len(unique_answers) - 1) / len(final_answers) if len(final_answers) > 1 else 0
       
        # Seuil de cohérence
        is_consistent = inconsistency_score < 0.3 # 70%+ d'accord
       
        # Identifier les étapes divergentes
        divergent_steps = []
        if len(unique_answers) > 1:
            divergent_steps = list(unique_answers)
       
        return is_consistent, inconsistency_score, divergent_steps



consistency_checker = SelfConsistencyChecker()