"""
Script DIRETO para adicionar coluna departamento_id - FORÇA a criação
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensoes import db

def adicionar_coluna():
    """Adiciona a coluna departamento_id FORÇADAMENTE"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Adicionando coluna departamento_id na tabela usuarios...")
            print(f"📊 Banco conectado: {db.engine.url}")
            
            # Executar SQL diretamente
            sql = "ALTER TABLE usuarios ADD COLUMN departamento_id INTEGER;"
            
            db.session.execute(db.text(sql))
            db.session.commit()
            
            print("✅ Coluna departamento_id adicionada com sucesso!")
            
            # Verificar
            result = db.session.execute(db.text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='usuarios' AND column_name='departamento_id';"
            ))
            if result.fetchone():
                print("✅ Verificação OK - Coluna existe!")
            else:
                print("⚠️ Coluna não foi criada!")
            
        except Exception as e:
            error_msg = str(e)
            
            # Se erro for "coluna já existe", está OK
            if "already exists" in error_msg or "já existe" in error_msg:
                print("✅ Coluna departamento_id JÁ EXISTE!")
            else:
                print(f"❌ Erro: {error_msg}")
                db.session.rollback()

if __name__ == '__main__':
    adicionar_coluna()
