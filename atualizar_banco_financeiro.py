#!/usr/bin/env python3
"""
Script para atualizar o banco de dados com a nova coluna 'comprovante'
na tabela de lançamentos financeiros
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db

def atualizar_tabela_lancamentos():
    """Adiciona a coluna comprovante à tabela de lançamentos"""
    
    print("=== ATUALIZANDO BANCO DE DADOS - MÓDULO FINANCEIRO ===")
    print()
    
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar se a coluna já existe
            from sqlalchemy import text
            
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('lancamentos')]
            
            print("✅ COLUNAS ATUAIS NA TABELA 'lancamentos':")
            for col in columns:
                print(f"   - {col}")
            
            if 'comprovante' not in columns:
                print()
                print("⚠️  COLUNA 'comprovante' NÃO ENCONTRADA")
                print("🔄 ADICIONANDO NOVA COLUNA...")
                
                # Adicionar coluna comprovante
                sql = "ALTER TABLE lancamentos ADD COLUMN comprovante VARCHAR(300);"
                db.session.execute(text(sql))
                db.session.commit()
                
                print("✅ COLUNA 'comprovante' ADICIONADA COM SUCESSO!")
            else:
                print()
                print("✅ COLUNA 'comprovante' JÁ EXISTE!")
            
            print()
            print("✅ VERIFICAÇÕES FINAIS:")
            
            # Verificar novamente
            inspector = db.inspect(db.engine)
            columns_after = [col['name'] for col in inspector.get_columns('lancamentos')]
            
            if 'comprovante' in columns_after:
                print("   ✅ Coluna 'comprovante' confirmada")
            else:
                print("   ❌ Erro: Coluna 'comprovante' não encontrada")
                return False
            
            # Testar insert/select
            from app.financeiro.financeiro_model import Lancamento
            total_lancamentos = Lancamento.query.count()
            print(f"   ✅ Total de lançamentos: {total_lancamentos}")
            
            print()
            print("🎉 BANCO DE DADOS ATUALIZADO COM SUCESSO!")
            print("   📂 Nova funcionalidade: Upload de comprovantes")
            print("   🔗 Formatos aceitos: JPG, PNG, PDF")
            print("   📁 Pasta de upload: app/static/uploads/comprovantes/")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERRO AO ATUALIZAR BANCO: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    sucesso = atualizar_tabela_lancamentos()
    if sucesso:
        print("\n🎯 PRÓXIMOS PASSOS:")
        print("   1. Reinicie o servidor Flask")
        print("   2. Acesse: http://127.0.0.1:5000/financeiro")
        print("   3. Teste o upload de comprovantes")
    else:
        print("\n⚠️  VERIFIQUE OS ERROS ACIMA E TENTE NOVAMENTE")