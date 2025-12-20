"""
Script para adicionar coluna departamento_id na tabela usuarios
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensoes import db

def adicionar_coluna_departamento():
    """Adiciona a coluna departamento_id na tabela usuarios"""
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar se a coluna já existe
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('usuarios')]
            
            if 'departamento_id' in columns:
                print("✅ Coluna 'departamento_id' já existe na tabela usuarios!")
                return
            
            # Adicionar a coluna
            print("📝 Adicionando coluna 'departamento_id' na tabela usuarios...")
            
            # Para SQLite
            if 'sqlite' in str(db.engine.url):
                db.session.execute(db.text('''
                    ALTER TABLE usuarios ADD COLUMN departamento_id INTEGER;
                '''))
                print("✅ Coluna adicionada no SQLite!")
            
            # Para PostgreSQL
            else:
                db.session.execute(db.text('''
                    ALTER TABLE usuarios 
                    ADD COLUMN IF NOT EXISTS departamento_id INTEGER 
                    REFERENCES departamentos(id);
                '''))
                print("✅ Coluna adicionada no PostgreSQL!")
            
            db.session.commit()
            print("\n🎯 ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!")
            print("\nAgora você pode:")
            print("1. Criar usuários com nível 'lider_departamento'")
            print("2. Associar o usuário a um departamento específico")
            print("3. O líder verá apenas o departamento dele")
            
        except Exception as e:
            print(f"❌ Erro ao adicionar coluna: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    adicionar_coluna_departamento()
