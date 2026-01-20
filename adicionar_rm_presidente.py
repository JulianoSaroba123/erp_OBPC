#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para adicionar campos RM e Validade RM ao Presidente
Sistema OBPC - Igreja O Brasil para Cristo
"""

import os
import sys

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db
from sqlalchemy import text

def adicionar_campos_rm():
    """Adiciona os campos rm_presidente e validade_rm_presidente à tabela configuracoes"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("=" * 70)
            print("ADICIONANDO CAMPOS RM DO PRESIDENTE")
            print("=" * 70)
            
            # Verificar se os campos já existem
            inspector = db.inspect(db.engine)
            colunas_existentes = [col['name'] for col in inspector.get_columns('configuracoes')]
            
            print(f"\n✓ Colunas existentes na tabela configuracoes: {len(colunas_existentes)}")
            
            campos_adicionados = []
            
            # Adicionar campo rm_presidente se não existir
            if 'rm_presidente' not in colunas_existentes:
                print("\n► Adicionando campo 'rm_presidente'...")
                db.session.execute(text(
                    "ALTER TABLE configuracoes ADD COLUMN rm_presidente VARCHAR(20)"
                ))
                campos_adicionados.append('rm_presidente')
                print("  ✓ Campo 'rm_presidente' adicionado com sucesso!")
            else:
                print("\n⚠ Campo 'rm_presidente' já existe.")
            
            # Adicionar campo validade_rm_presidente se não existir
            if 'validade_rm_presidente' not in colunas_existentes:
                print("\n► Adicionando campo 'validade_rm_presidente'...")
                db.session.execute(text(
                    "ALTER TABLE configuracoes ADD COLUMN validade_rm_presidente DATE"
                ))
                campos_adicionados.append('validade_rm_presidente')
                print("  ✓ Campo 'validade_rm_presidente' adicionado com sucesso!")
            else:
                print("\n⚠ Campo 'validade_rm_presidente' já existe.")
            
            # Commit das alterações
            if campos_adicionados:
                db.session.commit()
                print(f"\n✓ {len(campos_adicionados)} campo(s) adicionado(s) com sucesso!")
                print(f"  Campos: {', '.join(campos_adicionados)}")
            else:
                print("\n✓ Todos os campos já existem. Nenhuma alteração necessária.")
            
            # Verificar novamente as colunas
            inspector = db.inspect(db.engine)
            colunas_atualizadas = [col['name'] for col in inspector.get_columns('configuracoes')]
            
            print("\n" + "=" * 70)
            print("RESUMO DA ATUALIZAÇÃO")
            print("=" * 70)
            print(f"✓ Total de colunas na tabela: {len(colunas_atualizadas)}")
            print(f"✓ Campo 'rm_presidente': {'SIM' if 'rm_presidente' in colunas_atualizadas else 'NÃO'}")
            print(f"✓ Campo 'validade_rm_presidente': {'SIM' if 'validade_rm_presidente' in colunas_atualizadas else 'NÃO'}")
            print("=" * 70)
            
            print("\n✓ Migração concluída com sucesso!")
            print("\nPróximos passos:")
            print("1. Acesse as Configurações do sistema")
            print("2. Preencha o RM do Presidente (Pastor Dirigente)")
            print("3. Informe a data de validade do RM")
            print("4. O RM aparecerá automaticamente nas atas, ofícios e inventários")
            
        except Exception as e:
            print(f"\n❌ ERRO ao adicionar campos: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == '__main__':
    print("\n🔧 Iniciando migração do banco de dados...")
    print("📋 Adicionando campos RM do Presidente\n")
    
    sucesso = adicionar_campos_rm()
    
    if sucesso:
        print("\n✅ Script executado com sucesso!")
    else:
        print("\n❌ Script finalizado com erros!")
        sys.exit(1)
