from datetime import datetime

def format_datetime(dt: datetime) -> str:
    """Formate une date en string lisible"""
    return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else 'N/A'

def validate_email(email: str) -> bool:
    """Validation basique d'email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None