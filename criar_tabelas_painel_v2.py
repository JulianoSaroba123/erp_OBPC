#!/usr/bin/env python
"""Script para criar as tabelas do painel no banco de dados da aplicação em execução"""

import os
import sys

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Importando app e extensões...")
    from app import create_app
    from app.extensoes import db
    
    print("Criando app...")
    app = create_app()
    
    with app.app_context():
        print("Verificando banco de dados existente...")
        inspector = db.inspect(db.engine)
        tabelas_existentes = inspector.get_table_names()
        print(f"Tabelas existentes: {tabelas_existentes}")
        
        print("\nCriando todas as tabelas...")
        db.create_all()
        print("✓ Comando create_all() executado")
        
        # Verificar se as tabelas foram criadas
        inspector = db.inspect(db.engine)
        tabelas = inspector.get_table_names()
        
        print("\nVerificando tabelas após criação:")
        if 'favorito_painel' in tabelas:
            print("✓ Tabela 'favorito_painel' criada")
            colunas = inspector.get_columns('favorito_painel')
            print(f"  Colunas: {[c['name'] for c in colunas]}")
        else:
            print("✗ Tabela 'favorito_painel' NÃO foi criada")
        
        if 'configuracao_painel' in tabelas:
            print("✓ Tabela 'configuracao_painel' criada")
            colunas = inspector.get_columns('configuracao_painel')
            print(f"  Colunas: {[c['name'] for c in colunas]}")
        else:
            print("✗ Tabela 'configuracao_painel' NÃO foi criada")
        
        if 'usuario' in tabelas:
            print("✓ Tabela 'usuario' existe")
        else:
            print("⚠️  Tabela 'usuario' não existe - você pode precisar rodar o script de inicialização do banco")

except Exception as e:
    print(f"✗ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
