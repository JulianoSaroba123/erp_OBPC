#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para criar/recriar todas as tabelas do banco
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db

# Importar todos os modelos para garantir que sejam reconhecidos
from app.usuario.usuario_model import Usuario
from app.membros.membros_model import Membro
from app.obreiros.obreiros_model import Obreiro
from app.departamentos.departamentos_model import Departamento
from app.financeiro.financeiro_model import Lancamento, ConciliacaoHistorico
from app.eventos.eventos_model import Evento
from app.configuracoes.configuracoes_model import Configuracao
from app.secretaria.atas.atas_model import Ata
from app.secretaria.inventario.inventario_model import ItemInventario
from app.secretaria.oficios.oficios_model import Oficio
from app.secretaria.participacao.participacao_model import ParticipacaoEvento
from app.midia.midia_model import ItemMidia
from app.escala_ministerial.escala_model import EscalaMinisterial

def criar_tabelas():
    """Cria todas as tabelas do banco"""
    
    print("🔨 CRIANDO TABELAS DO BANCO...")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Excluir todas as tabelas existentes
            db.drop_all()
            print("🗑️ Tabelas antigas removidas")
            
            # Criar todas as tabelas
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
            
            # Verificar tabelas criadas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tabelas = inspector.get_table_names()
            
            print(f"📋 Tabelas criadas ({len(tabelas)}):")
            for tabela in sorted(tabelas):
                print(f"   - {tabela}")
                
            # Criar alguns dados de teste para inventário
            print("\n🎯 CRIANDO DADOS DE TESTE...")
            
            # Item de teste com código 05
            item_05 = ItemInventario(
                codigo="05",
                nome="Mesa de Escritório",
                categoria="Móveis e Utensílios",
                descricao="Mesa de escritório em madeira",
                valor_aquisicao=350.00,
                estado_conservacao="Bom",
                localizacao="Secretaria",
                responsavel="Pastor",
                observacoes="Item de teste",
                ativo=True
            )
            
            # Outros itens de teste
            item_01 = ItemInventario(
                codigo="01",
                nome="Computador Desktop",
                categoria="Equipamentos de Informática",
                descricao="Computador para secretaria",
                valor_aquisicao=1200.00,
                estado_conservacao="Excelente",
                localizacao="Secretaria",
                responsavel="Secretário",
                ativo=True
            )
            
            item_02 = ItemInventario(
                codigo="02",
                nome="Microfone Sem Fio",
                categoria="Equipamentos de Som e Imagem",
                descricao="Microfone para cultos",
                valor_aquisicao=250.00,
                estado_conservacao="Bom",
                localizacao="Altar",
                responsavel="Ministério de Louvor",
                ativo=True
            )
            
            # Adicionar ao banco
            db.session.add_all([item_01, item_02, item_05])
            db.session.commit()
            
            print("✅ Dados de teste criados!")
            print(f"   - Item 01: {item_01.nome}")
            print(f"   - Item 02: {item_02.nome}")
            print(f"   - Item 05: {item_05.nome}")
            
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {e}")
            db.session.rollback()
    
    print("\n" + "=" * 50)
    print("🔨 CRIAÇÃO DE TABELAS CONCLUÍDA")

if __name__ == "__main__":
    criar_tabelas()