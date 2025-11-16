#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste completo: cadastro de item e verificação na lista
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

def testar_cadastro_e_lista():
    """Testa o cadastro de um novo item e verifica se aparece na lista"""
    try:
        from app import create_app
        from app.extensoes import db
        from app.secretaria.inventario.inventario_model import ItemInventario
        from datetime import datetime
        
        app = create_app()
        
        with app.app_context():
            print("🧪 TESTE COMPLETO: CADASTRO + LISTA")
            print("=" * 50)
            
            # 1. Verificar estado atual do banco
            total_antes = ItemInventario.query.count()
            print(f"1. Itens no banco antes do teste: {total_antes}")
            
            # 2. Cadastrar um novo item de teste
            print(f"\n2. Cadastrando novo item de teste...")
            
            novo_item = ItemInventario(
                codigo="TESTE001",
                nome="Item de Teste Cadastro",
                categoria="Equipamentos de Informática",
                descricao="Item criado para testar o cadastro e exibição",
                valor_aquisicao=150.00,
                data_aquisicao=datetime.now().date(),
                estado_conservacao="Novo",
                localizacao="Sala de Teste",
                responsavel="Sistema de Teste",
                observacoes="Teste de cadastro automático",
                ativo=True
            )
            
            db.session.add(novo_item)
            db.session.commit()
            
            print(f"   ✅ Item cadastrado: {novo_item.codigo} - {novo_item.nome}")
            print(f"   📊 Status ativo: {novo_item.ativo}")
            
            # 3. Verificar se foi salvo
            total_depois = ItemInventario.query.count()
            print(f"\n3. Itens no banco depois do cadastro: {total_depois}")
            
            if total_depois > total_antes:
                print(f"   ✅ Item foi salvo no banco!")
            else:
                print(f"   ❌ ERRO: Item não foi salvo!")
                return False
            
            # 4. Simular a consulta da rota (apenas itens ativos)
            print(f"\n4. Simulando consulta da rota (apenas ativos)...")
            
            query = ItemInventario.query
            query = query.filter(ItemInventario.ativo == True)
            itens_ativos = query.order_by(ItemInventario.codigo.asc()).all()
            
            print(f"   📋 Total de itens ativos: {len(itens_ativos)}")
            
            # Procurar o item cadastrado
            item_encontrado = None
            for item in itens_ativos:
                if item.codigo == "TESTE001":
                    item_encontrado = item
                    break
            
            if item_encontrado:
                print(f"   ✅ Item TESTE001 encontrado na consulta!")
                print(f"      Nome: {item_encontrado.nome}")
                print(f"      Ativo: {item_encontrado.ativo}")
            else:
                print(f"   ❌ Item TESTE001 NÃO encontrado na consulta!")
                
                # Debug: verificar se está no banco mas inativo
                item_banco = ItemInventario.query.filter_by(codigo="TESTE001").first()
                if item_banco:
                    print(f"   🔍 Item existe no banco mas:")
                    print(f"      Ativo: {item_banco.ativo} (tipo: {type(item_banco.ativo)})")
                else:
                    print(f"   🔍 Item não existe no banco!")
            
            # 5. Mostrar todos os itens para debug
            print(f"\n5. Lista completa de itens ativos:")
            for i, item in enumerate(itens_ativos[:10], 1):
                print(f"   {i}. {item.codigo}: {item.nome}")
            
            # 6. Verificar se há problemas com o campo 'ativo'
            print(f"\n6. Verificação de tipos de dados:")
            todos_itens = ItemInventario.query.limit(5).all()
            for item in todos_itens:
                print(f"   {item.codigo}: ativo={item.ativo} (tipo: {type(item.ativo)})")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    resultado = testar_cadastro_e_lista()
    
    if resultado:
        print("\n" + "=" * 50)
        print("✅ TESTE CONCLUÍDO")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ TESTE FALHOU")
        print("=" * 50)