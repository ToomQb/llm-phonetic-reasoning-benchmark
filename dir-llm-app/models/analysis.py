from datetime import datetime
import json
from . import db
from .evaluation import Evaluation  # Pour relation

class ConsistencyCheck(db.Model):
    """Stockage des vérifications de cohérence multi-réponses"""
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'), nullable=False)
   
    # Données
    num_samples = db.Column(db.Integer, default=5)
    responses = db.Column(db.Text)
    final_answers = db.Column(db.Text)
   
    # Résultats
    is_consistent = db.Column(db.Boolean)
    inconsistency_score = db.Column(db.Float)
    divergent_steps = db.Column(db.Text)
   
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LogicalAnalysis(db.Model):
    """Analyse logique interne sans LLM"""
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'), nullable=False)
   
    # Détections
    has_contradiction = db.Column(db.Boolean, default=False)
    has_circular_reasoning = db.Column(db.Boolean, default=False)
    has_invalid_quantifier = db.Column(db.Boolean, default=False)
   
    # Détails
    contradictions_found = db.Column(db.Text) 
    circular_patterns = db.Column(db.Text) 
    logical_errors = db.Column(db.Text) 
   
    created_at = db.Column(db.DateTime, default=datetime.utcnow)