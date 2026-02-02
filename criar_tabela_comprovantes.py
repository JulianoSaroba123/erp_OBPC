#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar tabela de múltiplos comprovantes
Sistema OBPC - Igreja O Brasil para Cristo
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensoes import db

def criar_tabela_comprovantes():
    """Cria a tabela de comprovantes no banco de dados"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("=" * 60)
            print("CRIANDO TABELA DE MÚLTIPLOS COMPROVANTES")
            print("=" * 60)
            
            # Importar o modelo
            from app.financeiro.comprovante_model import Comprovante
            
            # Criar a tabela
            print("\n📋 Criando tabela 'comprovantes'...")
            db.create_all()
            
            print("✅ Tabela criada com sucesso!")
            
            print("\n📊 ESTRUTURA DA TABELA:")
            print("-" * 60)
            print("• id (Integer, PK)")
            print("• lancamento_id (Integer, FK -> lancamentos.id)")
            print("• arquivo (String) - Caminho do arquivo")
            print("• nome_original (String) - Nome original do arquivo")
            print("• tamanho (Integer) - Tamanho em bytes")
            print("• tipo_mime (String) - Tipo MIME do arquivo")
            print("• criado_em (DateTime) - Data de criação")
            print("-" * 60)
            
            print("\n✨ FUNCIONALIDADES IMPLEMENTADAS:")
            print("  ✅ Upload de múltiplos comprovantes por lançamento")
            print("  ✅ Visualização de todos os comprovantes")
            print("  ✅ Exclusão individual de comprovantes")
            print("  ✅ Informações de tamanho e tipo de arquivo")
            print("  ✅ Suporte para imagens (JPG, PNG) e PDFs")
            
            print("\n💡 COMO USAR:")
            print("  1. Acesse Financeiro → Editar Lançamento")
            print("  2. Role até a seção 'Comprovantes'")
            print("  3. Clique em 'Escolher arquivos' e selecione múltiplos")
            print("  4. Clique em 'Adicionar Comprovantes'")
            
            print("\n" + "=" * 60)
            print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ ERRO ao criar tabela: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == "__main__":
    criar_tabela_comprovantes()
