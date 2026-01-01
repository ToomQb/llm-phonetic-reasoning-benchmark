import os
# from dotenv import load_dotenv

# load_dotenv()  # Charge les variables d'environnement si .env existe

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a7c9f2d1e8b04c6fa9d3b5e21c74a6f0b8e19d4f5a6c2e3d9b0f8a1c7e6d5'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///dirllm.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or "##YOUR_GEMINI_API_KEY_HERE##"
    GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"