"""
Script para criar a tabela agenda_pastoral no PostgreSQL do Render
"""

import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def criar_tabela_agenda_pastoral():
    """Cria a tabela agenda_pastoral no PostgreSQL do Render"""
    
    print("Importando aplicacao...")
    
    try:
        from app import create_app
        from app.extensoes import db
        from app.agenda_pastoral.agenda_pastoral_model import AgendaPastoral
    except Exception as e:
        print(f"Erro ao importar: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("Criando aplicacao Flask...")
    app = create_app()
    
    with app.app_context():
        try:
            print("\nCriando tabela agenda_pastoral...")
            
            # Criar apenas a tabela agenda_pastoral
            AgendaPastoral.__table__.create(db.engine, checkfirst=True)
            
            print("Tabela agenda_pastoral criada com sucesso!")
            
            # Verificar a estrutura
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            if 'agenda_pastoral' in inspector.get_table_names():
                colunas = inspector.get_columns('agenda_pastoral')
                print(f"\nColunas criadas ({len(colunas)}):")
                for col in colunas:
                    print(f"   - {col['name']}: {col['type']}")
            else:
                print("\nERRO: Tabela nao foi criada!")
            
        except Exception as e:
            print(f"\nERRO ao criar tabela: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    print("=" * 60)
    print("CRIAR TABELA AGENDA PASTORAL NO RENDER")
    print("=" * 60)
    criar_tabela_agenda_pastoral()
    print("=" * 60)
