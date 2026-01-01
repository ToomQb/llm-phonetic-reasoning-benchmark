import re
from typing import List, Dict

class LogicalAnalyzer:
    """Analyse logique symbolique du raisonnement"""
   
    def __init__(self):
        # Patterns de contradictions
        self.negation_words = ['ne pas', 'non', 'jamais', 'aucun', 'sans']
        self.quantifiers = {
            'universal': ['tous', 'tout', 'chaque', 'toujours'],
            'existential': ['certains', 'quelques', 'parfois', 'au moins un']
        }
   
    def analyze(self, text: str) -> dict:
        """Analyse complète du texte"""
        return {
            'has_contradiction': self._detect_contradictions(text),
            'has_circular_reasoning': self._detect_circular_reasoning(text),
            'has_invalid_quantifier': self._detect_quantifier_errors(text),
            'contradictions_found': self._find_contradictions(text),
            'circular_patterns': self._find_circular_patterns(text),
            'logical_errors': self._find_logical_errors(text)
        }
   
    def _detect_contradictions(self, text: str) -> bool:
        """Détecte les contradictions directes"""
        sentences = text.split('.')
       
        for i, sent1 in enumerate(sentences):
            for sent2 in sentences[i+1:]:
                if self._are_contradictory(sent1, sent2):
                    return True
        return False
   
    def _are_contradictory(self, sent1: str, sent2: str) -> bool:
        """Vérifie si deux phrases sont contradictoires"""
        s1 = sent1.lower().strip()
        s2 = sent2.lower().strip()
       
        # Chercher négation + affirmation du même concept
        for neg_word in self.negation_words:
            if neg_word in s1 and neg_word not in s2:
                # Extraire le concept
                concept = s1.replace(neg_word, '').strip()
                if len(concept) > 10 and concept in s2:
                    return True
       
        return False
   
    def _detect_circular_reasoning(self, text: str) -> bool:
        """Détecte le raisonnement circulaire"""
        # Pattern: "A parce que B" puis "B parce que A"
        causal_pattern = r'(.+?)\s+(?:parce que|car|donc)\s+(.+?)[\.\,]'
        matches = re.findall(causal_pattern, text.lower())
       
        if len(matches) < 2:
            return False
       
        # Vérifier les cycles
        for i, (a1, b1) in enumerate(matches):
            for (a2, b2) in matches[i+1:]:
                # Si A→B puis B→A
                if self._similar(a1, b2) and self._similar(b1, a2):
                    return True
       
        return False
   
    def _detect_quantifier_errors(self, text: str) -> bool:
        """Détecte les erreurs de quantificateurs"""
        text_lower = text.lower()
       
        # "Tous X sont Y" + "Certains X ne sont pas Y"
        has_universal = any(q in text_lower for q in self.quantifiers['universal'])
        has_existential = any(q in text_lower for q in self.quantifiers['existential'])
        has_negation = any(neg in text_lower for neg in self.negation_words)
       
        # Si quantificateur universel + existentiel négatif → possible contradiction
        return has_universal and has_existential and has_negation
   
    def _find_contradictions(self, text: str) -> List[Dict]:
        """Liste les contradictions trouvées"""
        contradictions = []
        sentences = text.split('.')
       
        for i, sent1 in enumerate(sentences):
            for j, sent2 in enumerate(sentences[i+1:], i+1):
                if self._are_contradictory(sent1, sent2):
                    contradictions.append({
                        'sentence1': sent1.strip(),
                        'sentence2': sent2.strip(),
                        'type': 'negation_conflict'
                    })
       
        return contradictions
   
    def _find_circular_patterns(self, text: str) -> List[Dict]:
        """Liste les patterns circulaires"""
        patterns = []
        causal_pattern = r'(.+?)\s+(?:parce que|car|donc)\s+(.+?)[\.\,]'
        matches = re.findall(causal_pattern, text.lower())
       
        for i, (a1, b1) in enumerate(matches):
            for j, (a2, b2) in enumerate(matches[i+1:], i+1):
                if self._similar(a1, b2) and self._similar(b1, a2):
                    patterns.append({
                        'step1': f"{a1} → {b1}",
                        'step2': f"{a2} → {b2}",
                        'type': 'circular_causality'
                    })
       
        return patterns
   
    def _find_logical_errors(self, text: str) -> List[Dict]:
        """Liste d'autres erreurs logiques"""
        errors = []
       
        # Fausse dichotomie
        if re.search(r'(?:soit|ou bien).+(?:soit|ou)\s', text.lower()):
            errors.append({'type': 'potential_false_dichotomy', 'text': 'Either/or pattern detected'})
       
        return errors
   
    def _similar(self, text1: str, text2: str, threshold=0.6) -> bool:
        """Vérifie si deux textes sont similaires"""
        words1 = set(text1.split())
        words2 = set(text2.split())
       
        if not words1 or not words2:
            return False
       
        intersection = words1.intersection(words2)
        union = words1.union(words2)
       
        similarity = len(intersection) / len(union)
        return similarity >= threshold
    

logical_analyzer = LogicalAnalyzer()