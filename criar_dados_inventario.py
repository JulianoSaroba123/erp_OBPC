#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para criar tabela de inventário e dados de teste
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db

def criar_inventario():
    """Cria tabela de inventário e dados de teste"""
    
    print("🔨 CRIANDO TABELA DE INVENTÁRIO...")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Importar o modelo apenas quando necessário
            from app.secretaria.inventario.inventario_model import ItemInventario
            
            # Criar tabelas
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
            
            # Verificar se a tabela inventario existe
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tabelas = inspector.get_table_names()
            
            print(f"📋 Tabelas no banco ({len(tabelas)}):")
            for tabela in sorted(tabelas):
                print(f"   - {tabela}")
            
            if 'inventario' in tabelas:
                print("✅ Tabela inventario encontrada!")
                
                # Verificar se já existem dados
                count = ItemInventario.query.count()
                print(f"📊 Itens existentes: {count}")
                
                if count == 0:
                    print("🎯 CRIANDO DADOS DE TESTE...")
                    
                    # Item de teste com código 05
                    item_05 = ItemInventario(
                        codigo="05",
                        nome="Mesa de Escritório",
                        categoria="Móveis e Utensílios",
                        descricao="Mesa de escritório em madeira MDF",
                        valor_aquisicao=350.00,
                        estado_conservacao="Bom",
                        localizacao="Secretaria",
                        responsavel="Pastor",
                        observacoes="Item de teste criado automaticamente",
                        ativo=True
                    )
                    
                    # Outros itens de teste
                    itens_teste = [
                        ItemInventario(
                            codigo="01",
                            nome="Computador Desktop",
                            categoria="Equipamentos de Informática",
                            descricao="Computador Dell OptiPlex para secretaria",
                            valor_aquisicao=1200.00,
                            estado_conservacao="Excelente",
                            localizacao="Secretaria",
                            responsavel="Secretário",
                            ativo=True
                        ),
                        ItemInventario(
                            codigo="02",
                            nome="Microfone Sem Fio",
                            categoria="Equipamentos de Som e Imagem",
                            descricao="Microfone Shure SM58 sem fio",
                            valor_aquisicao=250.00,
                            estado_conservacao="Bom",
                            localizacao="Altar",
                            responsavel="Ministério de Louvor",
                            ativo=True
                        ),
                        ItemInventario(
                            codigo="03",
                            nome="Cadeiras Plásticas",
                            categoria="Móveis e Utensílios",
                            descricao="Conjunto de 50 cadeiras plásticas",
                            valor_aquisicao=500.00,
                            estado_conservacao="Regular",
                            localizacao="Salão Principal",
                            responsavel="Diácono",
                            ativo=True
                        ),
                        ItemInventario(
                            codigo="04",
                            nome="Violão Clássico",
                            categoria="Instrumentos Musicais",
                            descricao="Violão Yamaha C40 clássico",
                            valor_aquisicao=180.00,
                            estado_conservacao="Bom",
                            localizacao="Sala de Música",
                            responsavel="Ministério de Louvor",
                            ativo=True
                        ),
                        item_05,
                        ItemInventario(
                            codigo="06",
                            nome="Projetor Multimídia",
                            categoria="Equipamentos de Som e Imagem",
                            descricao="Projetor Epson PowerLite",
                            valor_aquisicao=800.00,
                            estado_conservacao="Excelente",
                            localizacao="Salão Principal",
                            responsavel="Ministério de Mídia",
                            ativo=True
                        )
                    ]
                    
                    # Adicionar todos os itens
                    for item in itens_teste:
                        db.session.add(item)
                    
                    db.session.commit()
                    
                    print(f"✅ {len(itens_teste)} itens de teste criados!")
                    for item in itens_teste:
                        print(f"   - {item.codigo}: {item.nome}")
                else:
                    print("ℹ️ Dados já existem, não criando novos")
                    
                    # Mostrar dados existentes
                    itens = ItemInventario.query.all()
                    print("📋 Itens existentes:")
                    for item in itens:
                        print(f"   - {item.codigo}: {item.nome}")
            else:
                print("❌ Tabela inventario NÃO foi criada!")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
    
    print("\n" + "=" * 50)
    print("🔨 PROCESSO CONCLUÍDO")

if __name__ == "__main__":
    criar_inventario()