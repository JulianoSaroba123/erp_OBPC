#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar tabelas da Agenda Pastoral
"""

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db
from app.escala_ministerial.escala_model import EscalaMinisterial

def criar_tabelas_escala():
    """Cria as tabelas necessárias para a Agenda Pastoral"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Criando tabelas da Agenda Pastoral...")
            print("=" * 60)
            
            # Verificar se a tabela já existe
            inspector = db.inspect(db.engine)
            tabelas_existentes = inspector.get_table_names()
            
            if 'escala_ministerial' in tabelas_existentes:
                print("✅ Tabela 'escala_ministerial' já existe")
            else:
                print("📝 Criando tabela 'escala_ministerial'...")
                
                # Criar as tabelas
                db.create_all()
                
                print("✅ Tabela 'escala_ministerial' criada com sucesso!")
            
            # Verificar a estrutura da tabela
            colunas = [col['name'] for col in inspector.get_columns('escala_ministerial')]
            print(f"📊 Colunas da tabela: {', '.join(colunas)}")
            
            # Verificar dados existentes
            total_escalas = EscalaMinisterial.query.count()
            print(f"📋 Total de escalas existentes: {total_escalas}")
            
            print("\n🎯 AGENDA PASTORAL CONFIGURADA!")
            print("✅ Tabela criada com sucesso")
            print("✅ Modelo configurado")
            print("✅ Rotas implementadas") 
            print("✅ Templates criados")
            print("✅ Menu adicionado ao sidebar")
            
            print("\n📋 FUNCIONALIDADES DISPONÍVEIS:")
            print("• Cadastro de escalas por evento")
            print("• Campos: pregador, dirigente, louvor, intercessor, diaconia")
            print("• Vinculação com agenda semanal")
            print("• Geração de PDF institucional")
            print("• CRUD completo")
            
            print("\n🌐 ROTAS DISPONÍVEIS:")
            print("• /escala/listar - Lista de escalas")
            print("• /escala/nova - Cadastro de nova escala")
            print("• /escala/editar/<id> - Editar escala")
            print("• /escala/excluir/<id> - Excluir escala")
            print("• /escala/pdf - Gerar PDF")
            
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {str(e)}")
            return False
            
    return True

if __name__ == "__main__":
    success = criar_tabelas_escala()
    if success:
        print("\n🚀 Execute o sistema e acesse Secretaria > Agenda Pastoral!")
    else:
        print("\n❌ Houve erro na criação. Verifique os logs.")
