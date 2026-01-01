from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from . import db

class User(UserMixin, db.Model):
    """Modèle utilisateur"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
   
    # Relations
    evaluations = db.relationship('Evaluation', backref='user', lazy=True, cascade='all, delete-orphan')
    annotations = db.relationship('HumanAnnotation', backref='annotator', lazy=True)
   
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
   
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def load_user(user_id):
        return User.query.get(int(user_id))