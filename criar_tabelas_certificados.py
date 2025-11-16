#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.abspath('.'))

def criar_tabelas():
    """Cria todas as tabelas do sistema, incluindo certificados"""
    
    print("🔄 CRIANDO TABELAS DO SISTEMA")
    print("=" * 50)
    
    try:
        from app import create_app, db
        
        # Criar aplicação
        app = create_app()
        
        with app.app_context():
            print("📦 Criando todas as tabelas...")
            
            # Importar todos os modelos para garantir que sejam registrados
            from app.midia.midia_model import Certificado, CarteiraMembro, AgendaSemanal
            from app.financeiro.financeiro_model import Lancamento
            
            # Criar todas as tabelas
            db.create_all()
            
            print("✅ Tabelas criadas com sucesso!")
            
            # Verificar se a tabela certificados foi criada
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tabelas = inspector.get_table_names()
            
            print(f"\n📋 Tabelas criadas: {len(tabelas)}")
            for tabela in sorted(tabelas):
                print(f"  - {tabela}")
            
            # Verificar estrutura da tabela certificados
            if 'certificados' in tabelas:
                colunas = inspector.get_columns('certificados')
                print(f"\n📊 Estrutura da tabela 'certificados':")
                for col in colunas:
                    print(f"  - {col['name']}: {col['type']}")
                    
                # Verificar se a coluna padrinhos existe
                nomes_colunas = [col['name'] for col in colunas]
                if 'padrinhos' in nomes_colunas:
                    print("✅ Coluna 'padrinhos' incluída!")
                else:
                    print("❌ Coluna 'padrinhos' não encontrada!")
            else:
                print("❌ Tabela 'certificados' não foi criada!")
        
        print("\n🎉 PROCESSO CONCLUÍDO!")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    criar_tabelas()