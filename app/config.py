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
        PREFERRED_URL_SCHEME = 'https'
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
    
    # Configurações de sessão - OTIMIZADO PARA RENDER
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_REFRESH_EACH_REQUEST = True
    SESSION_COOKIE_NAME = 'obpc_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_PATH = '/'
    
    # Configurações específicas por ambiente
    if DATABASE_URL:
        # PRODUÇÃO (Render) - Configuração conservadora que funciona
        SESSION_COOKIE_SECURE = True  # HTTPS obrigatório
        SESSION_COOKIE_SAMESITE = 'Lax'  # Lax funciona melhor que None no Render
        PREFERRED_URL_SCHEME = 'https'
        SESSION_COOKIE_DOMAIN = None  # Deixar o navegador definir
    else:
        # DESENVOLVIMENTO (Local)
        SESSION_COOKIE_SECURE = False
        SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Flask-Login - Cookie "Lembrar de mim"
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_PATH = '/'
    if DATABASE_URL:
        REMEMBER_COOKIE_SECURE = True
        REMEMBER_COOKIE_SAMESITE = 'Lax'
    else:
        REMEMBER_COOKIE_SECURE = False
        REMEMBER_COOKIE_SAMESITE = 'Lax'
