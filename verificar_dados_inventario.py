#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Verificação dos Dados do Inventário
===================================
Verifica se existem dados no banco e o status dos filtros.
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

def verificar_dados_inventario():
    """Verifica dados do inventário no banco"""
    try:
        from app import create_app
        from app.secretaria.inventario.inventario_model import ItemInventario
        from app.extensoes import db
        
        app = create_app()
        
        with app.app_context():
            print("🔍 VERIFICAÇÃO DOS DADOS DO INVENTÁRIO")
            print("=" * 50)
            
            # Verificar total de itens na base
            total_itens = ItemInventario.query.count()
            print(f"📦 Total de itens na base de dados: {total_itens}")
            
            # Verificar itens ativos
            itens_ativos = ItemInventario.query.filter_by(ativo=True).count()
            print(f"✅ Itens ativos: {itens_ativos}")
            
            # Verificar itens inativos
            itens_inativos = ItemInventario.query.filter_by(ativo=False).count()
            print(f"❌ Itens inativos: {itens_inativos}")
            
            # Listar alguns itens para verificar
            print(f"\n📋 PRIMEIROS 5 ITENS:")
            itens = ItemInventario.query.limit(5).all()
            for item in itens:
                status = "ATIVO" if item.ativo else "INATIVO"
                valor = f"R$ {item.valor_aquisicao:,.2f}" if item.valor_aquisicao else "Sem valor"
                print(f"- {item.codigo}: {item.nome} | {valor} | {status}")
            
            # Verificar valores
            print(f"\n💰 ANÁLISE DE VALORES:")
            itens_com_valor = ItemInventario.query.filter(ItemInventario.valor_aquisicao.isnot(None)).filter(ItemInventario.valor_aquisicao > 0).count()
            print(f"💵 Itens com valor > 0: {itens_com_valor}")
            
            # Calcular valor total (todos os itens)
            valor_total_todos = 0
            todos_itens = ItemInventario.query.all()
            for item in todos_itens:
                if item.valor_aquisicao:
                    valor_total_todos += float(item.valor_aquisicao)
            print(f"💲 Valor total (todos): R$ {valor_total_todos:,.2f}")
            
            # Calcular valor total (apenas ativos)
            valor_total_ativos = 0
            itens_ativos_list = ItemInventario.query.filter_by(ativo=True).all()
            for item in itens_ativos_list:
                if item.valor_aquisicao:
                    valor_total_ativos += float(item.valor_aquisicao)
            print(f"✅ Valor total (ativos): R$ {valor_total_ativos:,.2f}")
            
            # Verificar categorias
            print(f"\n📂 CATEGORIAS DISPONÍVEIS:")
            categorias = db.session.query(ItemInventario.categoria).distinct().all()
            for cat in categorias:
                if cat[0]:
                    count = ItemInventario.query.filter_by(categoria=cat[0]).count()
                    print(f"- {cat[0]}: {count} itens")
            
            if total_itens == 0:
                print(f"\n⚠️  PROBLEMA: Nenhum item encontrado no banco!")
                print("   Pode ser necessário recriar os dados de exemplo.")
                return False
            elif itens_ativos == 0:
                print(f"\n⚠️  PROBLEMA: Nenhum item ativo encontrado!")
                print("   Todos os itens podem estar marcados como inativos.")
                return False
            else:
                print(f"\n✅ Dados encontrados no banco de dados")
                return True
                
    except Exception as e:
        print(f"\n❌ Erro ao verificar dados: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verificar_dados_inventario()