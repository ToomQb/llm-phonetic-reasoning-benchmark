from datetime import datetime
from . import db

class Dataset(db.Model):
    """Modèle pour stocker les datasets"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    total_samples = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
   
    # Relation
    samples = db.relationship('DatasetSample', backref='dataset', lazy=True, cascade='all, delete-orphan')

class DatasetSample(db.Model):
    """Modèle pour stocker les échantillons individuels des datasets"""
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
   
    # Données de l'échantillon
    sample_id = db.Column(db.String(100), nullable=False) # ID unique dans le dataset
    question = db.Column(db.Text, nullable=False)
    context = db.Column(db.Text)
    answer = db.Column(db.String(500))
    full_solution = db.Column(db.Text)
   
    # Métadonnées
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)