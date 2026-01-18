"""Script para criar todas as tabelas do banco"""
import sys
sys.path.insert(0, '.')

import os
os.environ['FLASK_ENV'] = 'development'

from app import create_app
from app.extensoes import db

print("Criando tabelas do banco de dados...\n")

app = create_app()

with app.app_context():
    try:
        # Criar todas as tabelas
        db.create_all()
        print("Tabelas criadas com sucesso!\n")
        
        # Listar tabelas criadas
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tabelas = inspector.get_table_names()
        
        print(f"Tabelas criadas ({len(tabelas)}):")
        for tabela in sorted(tabelas):
            print(f"   - {tabela}")
            
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
        import traceback
        traceback.print_exc()
