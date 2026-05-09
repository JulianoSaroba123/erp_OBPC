#!/usr/bin/env python
"""Script para criar as tabelas do painel no banco de dados"""

import os
import sys

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Importando app...")
    from app import create_app
    from app.extensoes import db
    
    print("Criando app...")
    app = create_app()
    
    with app.app_context():
        print("Criando tabelas...")
        db.create_all()
        print("✓ Tabelas criadas com sucesso!")
        
        # Verificar se as tabelas foram criadas
        inspector = db.inspect(db.engine)
        tabelas = inspector.get_table_names()
        
        if 'favorito_painel' in tabelas:
            print("✓ Tabela 'favorito_painel' criada")
        else:
            print("✗ Tabela 'favorito_painel' NÃO foi criada")
        
        if 'configuracao_painel' in tabelas:
            print("✓ Tabela 'configuracao_painel' criada")
        else:
            print("✗ Tabela 'configuracao_painel' NÃO foi criada")

except Exception as e:
    print(f"✗ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
