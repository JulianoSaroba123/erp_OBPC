#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para buscar especificamente o código 05
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db

def buscar_codigo_05():
    """Busca especificamente o código 05"""
    
    print("🔍 BUSCANDO CÓDIGO 05...")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            from app.secretaria.inventario.inventario_model import ItemInventario
            
            # Buscar todos os códigos
            todos_itens = ItemInventario.query.all()
            print(f"📋 Total de itens: {len(todos_itens)}")
            
            print("\n🏷️ TODOS OS CÓDIGOS:")
            for item in todos_itens:
                print(f"   - Código: '{item.codigo}' | Nome: {item.nome}")
            
            # Buscar especificamente código "05"
            item_05_string = ItemInventario.query.filter_by(codigo="05").first()
            item_05_numero = ItemInventario.query.filter_by(codigo=5).first()
            
            print(f"\n🔍 BUSCA POR CÓDIGO '05' (string): {item_05_string}")
            print(f"🔍 BUSCA POR CÓDIGO 5 (número): {item_05_numero}")
            
            # Buscar com LIKE
            item_05_like = ItemInventario.query.filter(ItemInventario.codigo.like('%05%')).all()
            print(f"🔍 BUSCA COM LIKE '%05%': {len(item_05_like)} resultados")
            for item in item_05_like:
                print(f"   - {item.codigo}: {item.nome}")
            
            # Verificar se há filtros ativos ou status
            itens_ativos = ItemInventario.query.filter_by(ativo=True).all()
            print(f"\n✅ Itens ativos: {len(itens_ativos)}")
            
            itens_inativos = ItemInventario.query.filter_by(ativo=False).all()
            print(f"❌ Itens inativos: {len(itens_inativos)}")
            
            # Criar item com código 05 se não existir
            if not item_05_string and not item_05_numero:
                print("\n🎯 CRIANDO ITEM COM CÓDIGO 05...")
                
                item_05 = ItemInventario(
                    codigo="05",
                    nome="Item Teste Código 05",
                    categoria="Móveis e Utensílios",
                    descricao="Item criado especificamente para teste do código 05",
                    valor_aquisicao=100.00,
                    estado_conservacao="Bom",
                    localizacao="Teste",
                    responsavel="Sistema",
                    observacoes="Criado automaticamente para teste",
                    ativo=True
                )
                
                db.session.add(item_05)
                db.session.commit()
                
                print(f"✅ Item criado: {item_05.codigo} - {item_05.nome}")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🔍 BUSCA CONCLUÍDA")

if __name__ == "__main__":
    buscar_codigo_05()