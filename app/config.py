import os
from datetime import timedelta

class Config:
    SECRET_KEY = "chave-secreta-obpc-2025-igreja-brasil-para-cristo"  # Chave mais robusta
    SQLALCHEMY_DATABASE_URI = "sqlite:///igreja.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de sessão
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)  # Sessão dura 24 horas
    SESSION_COOKIE_SECURE = False  # True apenas em HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Proteção XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # Proteção CSRF
    
    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=7)  # "Lembrar de mim" por 7 dias
