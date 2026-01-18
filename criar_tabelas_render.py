"""
Script para criar TODAS as tabelas no PostgreSQL do Render
Execute este script PRIMEIRO se for uma instalação nova
"""

import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def criar_tabelas_render():
    """Cria todas as tabelas no banco PostgreSQL do Render"""
    
    print("Importando dependencias...")
    
    try:
        from app import create_app
        from app.extensoes import db
    except Exception as e:
        print(f"Erro ao importar: {e}")
        return
    
    print("Criando aplicacao Flask...")
    app = create_app()
    
    with app.app_context():
        try:
            print("\nCriando todas as tabelas no banco de dados...")
            
            # Criar todas as tabelas
            db.create_all()
            
            print("Tabelas criadas com sucesso!")
            
            # Listar tabelas criadas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tabelas = inspector.get_table_names()
            
            print(f"\nTotal de tabelas criadas: {len(tabelas)}")
            print("\nTabelas:")
            for tabela in sorted(tabelas):
                print(f"   - {tabela}")
            
            print("\nPROXIMO PASSO:")
            print("Agora execute: python atualizar_membros_render.py")
            print("Para adicionar as colunas extras na tabela membros")
            
        except Exception as e:
            print(f"\nErro ao criar tabelas: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    print("=" * 60)
    print("CRIAR TABELAS NO RENDER")
    print("=" * 60)
    criar_tabelas_render()
    print("=" * 60)
