import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or "chave-secreta-obpc-2025-igreja-brasil-para-cristo"
    
    # Usar PostgreSQL em produção, SQLite em desenvolvimento
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL:
        # Render fornece postgres:// mas SQLAlchemy precisa de postgresql://
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'pool_timeout': 30,
            'pool_recycle': 1800,
            'pool_pre_ping': True,
        }
    else:
        # Desenvolvimento local com SQLite
        SQLALCHEMY_DATABASE_URI = "sqlite:///igreja.db"
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_timeout': 20,
            'pool_recycle': -1,
            'pool_pre_ping': True,
            'connect_args': {
                'timeout': 30,
                'check_same_thread': False
            }
        }
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de sessão
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)  # Sessão dura 24 horas
    SESSION_COOKIE_SECURE = False  # True apenas em HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Proteção XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # Proteção CSRF
    
    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=7)  # "Lembrar de mim" por 7 dias
