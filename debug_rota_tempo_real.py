#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug da rota em tempo real - interceptar a execução
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

def patch_inventario_route():
    """Patch na rota do inventário para adicionar logs"""
    
    try:
        from app import create_app
        from app.extensoes import db
        from app.secretaria.inventario.inventario_model import ItemInventario
        from app.secretaria.inventario.inventario_routes import inventario_bp
        from flask import request, render_template, flash
        
        # Backup da função original
        from app.secretaria.inventario.inventario_routes import lista_itens as original_lista_itens
        
        def debug_lista_itens():
            """Versão com debug da função lista_itens"""
            print("🔍 DEBUG ROTA: Iniciando lista_itens()")
            
            try:
                # Filtros
                busca = request.args.get('busca', '').strip()
                categoria = request.args.get('categoria', '').strip()
                estado = request.args.get('estado', '').strip()
                ativo = request.args.get('ativo', '').strip()
                
                print(f"   📊 Parâmetros recebidos:")
                print(f"      busca: '{busca}'")
                print(f"      categoria: '{categoria}'")
                print(f"      estado: '{estado}'")
                print(f"      ativo: '{ativo}'")
                
                # Query base
                query = ItemInventario.query
                print(f"   🗃️ Query inicial criada")
                
                # Aplicar filtros
                if busca:
                    query = query.filter(
                        (ItemInventario.nome.ilike(f'%{busca}%')) |
                        (ItemInventario.codigo.ilike(f'%{busca}%')) |
                        (ItemInventario.descricao.ilike(f'%{busca}%')) |
                        (ItemInventario.responsavel.ilike(f'%{busca}%'))
                    )
                    print(f"   🔍 Filtro de busca aplicado: '{busca}'")
                
                if categoria and categoria != 'Todas':
                    query = query.filter(ItemInventario.categoria == categoria)
                    print(f"   📂 Filtro de categoria aplicado: '{categoria}'")
                
                if estado and estado != 'Todos':
                    query = query.filter(ItemInventario.estado_conservacao == estado)
                    print(f"   📊 Filtro de estado aplicado: '{estado}'")
                
                if ativo == 'true':
                    query = query.filter(ItemInventario.ativo == True)
                    print(f"   ✅ Filtro ativo = True aplicado")
                elif ativo == 'false':
                    query = query.filter(ItemInventario.ativo == False)
                    print(f"   ❌ Filtro ativo = False aplicado")
                else:
                    # Por padrão, mostrar apenas itens ativos
                    query = query.filter(ItemInventario.ativo == True)
                    print(f"   ✅ Filtro PADRÃO ativo = True aplicado")
                
                # Ordenação
                print(f"   📋 Executando query...")
                itens = query.order_by(ItemInventario.codigo.asc()).all()
                print(f"   📊 Query executada: {len(itens)} itens encontrados")
                
                if len(itens) > 0:
                    print(f"   📝 Primeiros 3 itens:")
                    for i, item in enumerate(itens[:3], 1):
                        print(f"      {i}. {item.codigo}: {item.nome} (Ativo: {item.ativo})")
                else:
                    print(f"   ⚠️ NENHUM ITEM ENCONTRADO!")
                    
                    # Debug adicional
                    total_banco = ItemInventario.query.count()
                    ativos_banco = ItemInventario.query.filter_by(ativo=True).count()
                    print(f"   🔍 Total no banco: {total_banco}")
                    print(f"   🔍 Ativos no banco: {ativos_banco}")
                
                # Calcular valor total
                valor_total = 0
                for item in itens:
                    if item.valor_aquisicao:
                        valor_total += float(item.valor_aquisicao)
                
                print(f"   💰 Valor total calculado: R$ {valor_total:,.2f}")
                
                # Obter todas as categorias para o filtro
                categorias = db.session.query(ItemInventario.categoria).distinct().all()
                categorias = [cat[0] for cat in categorias if cat[0]]
                print(f"   📂 Categorias encontradas: {len(categorias)}")
                
                # Estados de conservação
                estados = ['Novo', 'Bom', 'Regular', 'Ruim', 'Péssimo']
                print(f"   📊 Estados definidos: {len(estados)}")
                
                print(f"   📄 Renderizando template...")
                
                resultado = render_template('inventario/lista_itens.html', 
                                     itens=itens, 
                                     categorias=categorias,
                                     estados=estados,
                                     busca=busca,
                                     categoria_selecionada=categoria,
                                     estado_selecionado=estado,
                                     ativo_selecionado=ativo,
                                     valor_total=valor_total)
                
                print(f"   ✅ Template renderizado com sucesso!")
                print(f"   📏 Tamanho do HTML: {len(resultado)} caracteres")
                
                return resultado
                
            except Exception as e:
                print(f"   ❌ ERRO CAPTURADO NA ROTA: {str(e)}")
                import traceback
                traceback.print_exc()
                
                flash(f'Erro ao carregar inventário: {str(e)}', 'danger')
                resultado = render_template('inventario/lista_itens.html', itens=[], valor_total=0)
                print(f"   🔄 Retornando template de erro (lista vazia)")
                return resultado
        
        # Substituir a função na rota
        inventario_bp.view_functions['lista_itens'] = debug_lista_itens
        print("✅ Rota patcheada com sucesso! Debug ativo.")
        
    except Exception as e:
        print(f"❌ Erro ao fazer patch: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔧 Aplicando patch de debug na rota do inventário...")
    
    # Aplicar patch
    patch_inventario_route()
    
    # Iniciar servidor Flask com debug
    print("🚀 Iniciando Flask com debug ativo...")
    print("   Acesse: http://127.0.0.1:5000/secretaria/inventario")
    print("   Faça login com: admin@obpc.com / 123456")
    print("   Verifique o console para os logs de debug!")
    
    from app import create_app
    app = create_app()
    app.run(debug=True, port=5001)  # Porta diferente para não conflitar