#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste específico da busca por código '05'
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

def testar_busca_05():
    """Testa busca específica por código '05'"""
    try:
        from app import create_app
        from app.secretaria.inventario.inventario_model import ItemInventario
        
        app = create_app()
        
        with app.app_context():
            print("🔍 TESTE BUSCA POR CÓDIGO '05'")
            print("=" * 40)
            
            # Simular exatamente o que a rota faz quando busca por "05"
            busca = "05"
            categoria = ""
            estado = ""
            ativo = ""
            
            print(f"🎯 Parâmetros de busca:")
            print(f"   - busca: '{busca}'")
            print(f"   - categoria: '{categoria}'")
            print(f"   - estado: '{estado}'")
            print(f"   - ativo: '{ativo}'")
            
            # Query base exata da rota
            query = ItemInventario.query
            
            # Aplicar filtro de busca
            if busca:
                query = query.filter(
                    (ItemInventario.nome.ilike(f'%{busca}%')) |
                    (ItemInventario.codigo.ilike(f'%{busca}%')) |
                    (ItemInventario.descricao.ilike(f'%{busca}%')) |
                    (ItemInventario.responsavel.ilike(f'%{busca}%'))
                )
                print(f"✅ Filtro de busca aplicado: '%{busca}%'")
            
            # Aplicar filtro de categoria
            if categoria and categoria != 'Todas':
                query = query.filter(ItemInventario.categoria == categoria)
                print(f"✅ Filtro de categoria aplicado: {categoria}")
            
            # Aplicar filtro de estado
            if estado and estado != 'Todos':
                query = query.filter(ItemInventario.estado_conservacao == estado)
                print(f"✅ Filtro de estado aplicado: {estado}")
            
            # Aplicar filtro de ativo (lógica exata da rota)
            if ativo == 'true':
                query = query.filter(ItemInventario.ativo == True)
                print("✅ Filtro ativo=true aplicado")
            elif ativo == 'false':
                query = query.filter(ItemInventario.ativo == False)
                print("✅ Filtro ativo=false aplicado")
            else:
                # Por padrão, mostrar apenas itens ativos
                query = query.filter(ItemInventario.ativo == True)
                print("✅ Filtro padrão (apenas ativos) aplicado")
            
            # Executar query com ordenação
            itens = query.order_by(ItemInventario.codigo.asc()).all()
            
            print(f"\n📊 RESULTADO DA BUSCA:")
            print(f"   - Itens encontrados: {len(itens)}")
            
            if len(itens) > 0:
                print(f"\n📋 ITENS ENCONTRADOS:")
                for i, item in enumerate(itens, 1):
                    valor = f"R$ {item.valor_aquisicao:,.2f}" if item.valor_aquisicao else "Sem valor"
                    print(f"{i:2d}. Código: '{item.codigo}' | Nome: {item.nome}")
                    print(f"     Categoria: {item.categoria} | Estado: {item.estado_conservacao}")
                    print(f"     Valor: {valor} | Ativo: {item.ativo}")
                    print(f"     Localização: {item.localizacao}")
                    print(f"     Responsável: {item.responsavel}")
                    print("")
                
                # Calcular valor total
                valor_total = sum(float(item.valor_aquisicao) for item in itens if item.valor_aquisicao)
                print(f"💰 Valor total dos itens encontrados: R$ {valor_total:,.2f}")
                
                return True
            else:
                print("❌ NENHUM ITEM ENCONTRADO!")
                
                # Debug: verificar se item 05 existe
                print("\n🔍 DEBUG - Verificando se item '05' existe...")
                item_05 = ItemInventario.query.filter_by(codigo="05").first()
                if item_05:
                    print(f"✅ Item '05' existe no banco!")
                    print(f"   - Ativo: {item_05.ativo}")
                    print(f"   - Nome: {item_05.nome}")
                    print(f"   - Código: '{item_05.codigo}'")
                else:
                    print("❌ Item '05' não existe no banco!")
                
                return False
                
    except Exception as e:
        print(f"\n❌ Erro no teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = testar_busca_05()
    print("\n" + "=" * 40)
    if sucesso:
        print("🎉 BUSCA POR '05' FUNCIONANDO!")
    else:
        print("❌ PROBLEMA NA BUSCA POR '05'!")
    print("=" * 40)