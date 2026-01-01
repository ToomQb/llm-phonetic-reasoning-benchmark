from flask import Flask
from models import db 
from services import gemini_judge, consistency_checker, logical_analyzer
from .auth import auth_bp
from .main import main_bp
from .admin import admin_bp
from .datasets import datasets_bp
from .annotations import annotations_bp
from .scientific import scientific_bp
from .consistency import consistency_bp
from .logical import logical_bp
from .api import api_bp

def init_routes(app: Flask):
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(datasets_bp)
    app.register_blueprint(annotations_bp)
    app.register_blueprint(scientific_bp)
    app.register_blueprint(consistency_bp)
    app.register_blueprint(logical_bp)
    app.register_blueprint(api_bp)

    # Rendre les services globaux accessibles
    app.gemini_judge = gemini_judge
    app.consistency_checker = consistency_checker
    app.logical_analyzer = logical_analyzer