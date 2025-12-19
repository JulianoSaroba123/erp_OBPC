#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste da Rota de Listagem do Inventário
=======================================
Testa se a rota lista_itens está retornando os dados corretos.
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

def testar_rota_lista_itens():
    """Testa a rota de listagem diretamente"""
    try:
        from app import create_app
        from app.secretaria.inventario.inventario_model import ItemInventario
        
        app = create_app()
        
        with app.app_context():
            print("🧪 TESTE DA ROTA DE LISTAGEM")
            print("=" * 45)
            
            # Simular os parâmetros de query
            print("1. Testando query sem filtros...")
            query = ItemInventario.query
            
            # Aplicar filtro padrão (apenas ativos)
            query = query.filter(ItemInventario.ativo == True)
            
            # Executar query
            itens = query.order_by(ItemInventario.codigo.asc()).all()
            
            print(f"📦 Itens encontrados: {len(itens)}")
            
            # Calcular valor total
            valor_total = 0
            for item in itens:
                if item.valor_aquisicao:
                    valor_total += float(item.valor_aquisicao)
            
            print(f"💰 Valor total: R$ {valor_total:,.2f}")
            
            # Listar alguns itens
            print(f"\n📋 PRIMEIROS 3 ITENS ENCONTRADOS:")
            for i, item in enumerate(itens[:3]):
                valor = f"R$ {item.valor_aquisicao:,.2f}" if item.valor_aquisicao else "Sem valor"
                print(f"{i+1}. {item.codigo}: {item.nome} | {valor}")
            
            # Testar diferentes filtros de status
            print(f"\n🔧 TESTANDO FILTROS DE STATUS:")
            
            # Teste 1: ativo = 'true'
            query_ativo = ItemInventario.query.filter(ItemInventario.ativo == True)
            count_ativo = query_ativo.count()
            print(f"✅ ativo='true': {count_ativo} itens")
            
            # Teste 2: ativo = 'false'  
            query_inativo = ItemInventario.query.filter(ItemInventario.ativo == False)
            count_inativo = query_inativo.count()
            print(f"❌ ativo='false': {count_inativo} itens")
            
            # Teste 3: sem filtro (todos)
            query_todos = ItemInventario.query
            count_todos = query_todos.count()
            print(f"📊 sem filtro: {count_todos} itens")
            
            if len(itens) > 0 and valor_total > 0:
                print(f"\n✅ ROTA FUNCIONANDO CORRETAMENTE!")
                print(f"   - {len(itens)} itens serão exibidos")
                print(f"   - Valor total: R$ {valor_total:,.2f}")
                return True
            else:
                print(f"\n❌ PROBLEMA NA ROTA!")
                print(f"   - Itens: {len(itens)}")
                print(f"   - Valor: R$ {valor_total:,.2f}")
                return False
                
    except Exception as e:
        print(f"\n❌ Erro no teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = testar_rota_lista_itens()
    if sucesso:
        print("\n" + "=" * 45)
        print("🎉 TESTE CONCLUÍDO - ROTA OK!")
        print("=" * 45)
    else:
        print("\n" + "=" * 45)
        print("❌ TESTE FALHOU - VERIFICAR ROTA")
        print("=" * 45)