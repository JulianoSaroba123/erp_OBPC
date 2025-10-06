import os

class Config:
    SECRET_KEY = "chave-secreta-obpc"  # troque por uma chave real
    SQLALCHEMY_DATABASE_URI = "sqlite:///igreja.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
