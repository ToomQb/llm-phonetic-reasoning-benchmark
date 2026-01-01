from datetime import datetime
import json
from . import db

class Evaluation(db.Model):
    """Modèle d'évaluation de raisonnement"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
   
    # Données d'entrée
    question = db.Column(db.Text, nullable=False)
    llm_response = db.Column(db.Text, nullable=False)
    expected_answer = db.Column(db.String(500))
    dataset_name = db.Column(db.String(100))
   
    # Résultats d'évaluation
    is_illusory = db.Column(db.Boolean, default=False)
    illusion_types = db.Column(db.Text)
    explanation = db.Column(db.Text)
    confidence = db.Column(db.Float)
   
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    judge_model = db.Column(db.String(50), default='gemini-2.5-flash')
   
    # Relations
    consistency_checks = db.relationship('ConsistencyCheck', backref='evaluation', lazy=True)
    logical_analyses = db.relationship('LogicalAnalysis', backref='evaluation', lazy=True)
    human_annotations = db.relationship('HumanAnnotation', backref='evaluation', lazy=True)
   
    def get_illusion_types(self):
        """Récupère les types d'illusions comme liste"""
        if self.illusion_types:
            return json.loads(self.illusion_types)
        return []
   
    def set_illusion_types(self, types_list):
        """Définit les types d'illusions depuis une liste"""
        self.illusion_types = json.dumps(types_list)