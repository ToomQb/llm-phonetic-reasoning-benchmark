from datetime import datetime
import json
from . import db
from .evaluation import Evaluation

class IllusionType(db.Model):
    """Typologie formelle des illusions de raisonnement"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    example = db.Column(db.Text)
    category = db.Column(db.String(50)) # logical, causal, argumentative
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
   
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'example': self.example,
            'category': self.category
        }

class HumanAnnotation(db.Model):
    """Annotations humaines pour validation du judge"""
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'), nullable=False)
    annotator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
   
    # Annotation humaine
    is_illusory = db.Column(db.Boolean, nullable=False)
    illusion_types = db.Column(db.Text) # JSON list
    explanation = db.Column(db.Text)
    confidence = db.Column(db.Float)
   
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    annotation_time_seconds = db.Column(db.Integer)
   
    def get_illusion_types(self):
        if self.illusion_types:
            return json.loads(self.illusion_types)
        return []
   
    def set_illusion_types(self, types_list):
        self.illusion_types = json.dumps(types_list)