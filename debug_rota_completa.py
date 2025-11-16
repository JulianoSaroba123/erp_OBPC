#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug da rota de inventário - verificar se dados estão chegando no template
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

def debug_rota_inventario():
    """Debug completo da rota de inventário"""
    try:
        from app import create_app
        from app.extensoes import db
        from app.secretaria.inventario.inventario_model import ItemInventario
        
        app = create_app()
        
        with app.app_context():
            print("🔍 DEBUG DA ROTA DE INVENTÁRIO")
            print("=" * 50)
            
            # Simular a função da rota lista_itens
            print("1. Simulando filtros...")
            
            busca = ""
            categoria = ""
            estado = ""
            ativo = ""
            
            # Query base
            query = ItemInventario.query
            
            # Aplicar filtros conforme a rota
            if busca:
                query = query.filter(
                    (ItemInventario.nome.ilike(f'%{busca}%')) |
                    (ItemInventario.codigo.ilike(f'%{busca}%')) |
                    (ItemInventario.descricao.ilike(f'%{busca}%')) |
                    (ItemInventario.responsavel.ilike(f'%{busca}%'))
                )
            
            if categoria and categoria != 'Todas':
                query = query.filter(ItemInventario.categoria == categoria)
            
            if estado and estado != 'Todos':
                query = query.filter(ItemInventario.estado_conservacao == estado)
            
            if ativo == 'true':
                query = query.filter(ItemInventario.ativo == True)
            elif ativo == 'false':
                query = query.filter(ItemInventario.ativo == False)
            else:
                # Por padrão, mostrar apenas itens ativos
                query = query.filter(ItemInventario.ativo == True)
            
            print(f"   Filtros aplicados: busca='{busca}', categoria='{categoria}', estado='{estado}', ativo='{ativo}'")
            
            # Executar query
            itens = query.order_by(ItemInventario.codigo.asc()).all()
            
            print(f"2. Resultados da query: {len(itens)} itens")
            
            if len(itens) > 0:
                print(f"   ✅ Itens encontrados!")
                print(f"   📋 Primeiros 5 itens:")
                for i, item in enumerate(itens[:5], 1):
                    print(f"      {i}. {item.codigo}: {item.nome} (Ativo: {item.ativo})")
            else:
                print(f"   ❌ NENHUM ITEM ENCONTRADO!")
                
                # Debug: verificar total de itens no banco
                total_banco = ItemInventario.query.count()
                total_ativos = ItemInventario.query.filter_by(ativo=True).count()
                total_inativos = ItemInventario.query.filter_by(ativo=False).count()
                
                print(f"   🔍 Debug do banco:")
                print(f"      - Total no banco: {total_banco}")
                print(f"      - Ativos: {total_ativos}")
                print(f"      - Inativos: {total_inativos}")
            
            # Calcular valor total
            valor_total = 0
            for item in itens:
                if item.valor_aquisicao:
                    valor_total += float(item.valor_aquisicao)
            
            print(f"3. Valor total: R$ {valor_total:,.2f}")
            
            # Obter categorias
            categorias = db.session.query(ItemInventario.categoria).distinct().all()
            categorias = [cat[0] for cat in categorias if cat[0]]
            
            print(f"4. Categorias disponíveis: {categorias}")
            
            # Estados
            estados = ['Novo', 'Bom', 'Regular', 'Ruim', 'Péssimo']
            
            print(f"5. Estados disponíveis: {estados}")
            
            # Simular dados que vão para o template
            template_data = {
                'itens': itens,
                'categorias': categorias,
                'estados': estados,
                'busca': busca,
                'categoria_selecionada': categoria,
                'estado_selecionado': estado,
                'ativo_selecionado': ativo,
                'valor_total': valor_total
            }
            
            print(f"\n6. Dados que vão para o template:")
            print(f"   - itens: {len(template_data['itens'])} itens")
            print(f"   - categorias: {len(template_data['categorias'])} categorias")
            print(f"   - estados: {len(template_data['estados'])} estados")
            print(f"   - valor_total: R$ {template_data['valor_total']:,.2f}")
            
            # Verificar se template vai mostrar lista ou mensagem vazia
            if template_data['itens']:
                print(f"\n✅ TEMPLATE DEVE MOSTRAR LISTA DE {len(template_data['itens'])} ITENS")
            else:
                print(f"\n❌ TEMPLATE VAI MOSTRAR 'NENHUM ITEM NO INVENTÁRIO'")
            
            return template_data
            
    except Exception as e:
        print(f"\n❌ Erro no debug: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    resultado = debug_rota_inventario()
    print("\n" + "=" * 50)
    if resultado and resultado['itens']:
        print("🎉 ROTA DEVE FUNCIONAR - DADOS ESTÃO CORRETOS!")
    else:
        print("❌ PROBLEMA NA ROTA - DADOS NÃO ESTÃO SENDO RETORNADOS!")
    print("=" * 50)