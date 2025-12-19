#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug específico: por que a rota retorna lista vazia mesmo com dados no banco?
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

def debug_lista_vazia():
    """Debug para descobrir por que a lista está vazia na interface"""
    try:
        from app import create_app
        from app.extensoes import db
        from app.secretaria.inventario.inventario_model import ItemInventario
        from flask import request
        
        app = create_app()
        
        with app.app_context():
            print("🔍 DEBUG: POR QUE A LISTA ESTÁ VAZIA?")
            print("=" * 50)
            
            # 1. Verificar total de itens no banco
            total_banco = ItemInventario.query.count()
            print(f"1. Total de itens no banco: {total_banco}")
            
            if total_banco == 0:
                print("   ❌ BANCO VAZIO - Isso explica a lista vazia!")
                return
            
            # 2. Verificar itens ativos/inativos
            ativos = ItemInventario.query.filter_by(ativo=True).count()
            inativos = ItemInventario.query.filter_by(ativo=False).count()
            
            print(f"2. Itens ativos: {ativos}")
            print(f"   Itens inativos: {inativos}")
            
            if ativos == 0:
                print("   ❌ NENHUM ITEM ATIVO - A rota mostra apenas ativos por padrão!")
                print("   🔧 SOLUÇÃO: Verificar campo 'ativo' dos itens")
                
                # Mostrar alguns itens inativos
                inativos_items = ItemInventario.query.filter_by(ativo=False).limit(5).all()
                print("\n   📋 Itens inativos encontrados:")
                for item in inativos_items:
                    print(f"      - {item.codigo}: {item.nome} (Ativo: {item.ativo})")
                
                return
            
            # 3. Simular exatamente a lógica da rota
            print(f"\n3. Simulando lógica da rota (filtro padrão: apenas ativos)...")
            
            # Sem parâmetros (como carregamento inicial da página)
            busca = ""
            categoria = ""
            estado = ""
            ativo = ""  # Vazio = padrão da rota
            
            # Query exata da rota
            query = ItemInventario.query
            
            # Filtros da rota
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
            
            # CRÍTICO: Esta é a lógica da rota
            if ativo == 'true':
                query = query.filter(ItemInventario.ativo == True)
            elif ativo == 'false':
                query = query.filter(ItemInventario.ativo == False)
            else:
                # Por padrão, mostrar apenas itens ativos
                query = query.filter(ItemInventario.ativo == True)
            
            print(f"   Aplicando filtro: ativo == True (padrão)")
            
            # Executar query
            itens = query.order_by(ItemInventario.codigo.asc()).all()
            
            print(f"   Resultado: {len(itens)} itens")
            
            if len(itens) == 0:
                print(f"   ❌ PROBLEMA ENCONTRADO!")
                
                # Debug profundo
                print(f"\n4. Debug profundo dos dados:")
                
                todos_itens = ItemInventario.query.all()
                print(f"   Total de itens: {len(todos_itens)}")
                
                print(f"\n   📋 Primeiros 10 itens com status 'ativo':")
                for i, item in enumerate(todos_itens[:10], 1):
                    print(f"      {i}. ID:{item.id} | Código:{item.codigo} | Nome:{item.nome}")
                    print(f"         Ativo: {item.ativo} (tipo: {type(item.ativo)})")
                    if hasattr(item, 'data_cadastro'):
                        print(f"         Data: {item.data_cadastro}")
                    print()
                
                # Verificar tipos de dados
                primeiro_item = todos_itens[0] if todos_itens else None
                if primeiro_item:
                    print(f"   🔍 Verificação de tipos do primeiro item:")
                    print(f"      ativo = {primeiro_item.ativo} (tipo: {type(primeiro_item.ativo)})")
                    print(f"      ativo == True? {primeiro_item.ativo == True}")
                    print(f"      ativo is True? {primeiro_item.ativo is True}")
                    print(f"      bool(ativo)? {bool(primeiro_item.ativo)}")
                
            else:
                print(f"   ✅ {len(itens)} itens encontrados!")
                for i, item in enumerate(itens[:5], 1):
                    print(f"      {i}. {item.codigo}: {item.nome}")
                    
        print(f"\n" + "=" * 50)
        
    except Exception as e:
        print(f"\n❌ Erro no debug: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_lista_vazia()