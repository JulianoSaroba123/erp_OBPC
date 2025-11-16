"""
Script para atualizar tabela de membros com colunas faltantes
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensoes import db

app = create_app()

def atualizar_tabela_membros():
    """Atualiza a tabela membros com as colunas necessárias"""
    with app.app_context():
        print("🔧 ATUALIZANDO TABELA MEMBROS...")
        
        try:
            # Lista de colunas para adicionar
            colunas_novas = [
                "ALTER TABLE membros ADD COLUMN tipo VARCHAR(20) DEFAULT 'Membro'",
                "ALTER TABLE membros ADD COLUMN status VARCHAR(20) DEFAULT 'Ativo'", 
                "ALTER TABLE membros ADD COLUMN observacoes TEXT",
                "ALTER TABLE membros ADD COLUMN data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP"
            ]
            
            for sql in colunas_novas:
                try:
                    db.session.execute(db.text(sql))
                    print(f"✅ {sql}")
                except Exception as e:
                    if "duplicate column name" in str(e) or "already exists" in str(e):
                        print(f"⚠️  Coluna já existe: {sql}")
                    else:
                        print(f"❌ Erro: {sql} - {e}")
            
            db.session.commit()
            print("\n✅ TABELA MEMBROS ATUALIZADA!")
            
        except Exception as e:
            print(f"❌ Erro geral: {e}")
            db.session.rollback()

if __name__ == "__main__":
    atualizar_tabela_membros()