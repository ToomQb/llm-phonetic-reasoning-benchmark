import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', "votre_cle_api_google_ici")
    MODEL_NAME = os.getenv('MODEL_NAME', 'gemini-2.5-flash-lite') # gemini-2.5-flash-lite, gemini-3-flash-preview
