#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste da interface web do inventário
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

def testar_interface_web():
    """Testa a interface web diretamente"""
    try:
        from app import create_app
        
        app = create_app()
        
        with app.test_client() as client:
            print("🌐 TESTE DA INTERFACE WEB")
            print("=" * 40)
            
            # Teste 1: Página principal do inventário
            print("1. Testando página principal...")
            response = client.get('/secretaria/inventario')
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Página carregou com sucesso!")
                
                # Verificar se contém o item 05
                html_content = response.data.decode('utf-8')
                
                if "Item Teste Código 05" in html_content:
                    print("   ✅ Item '05' encontrado no HTML!")
                else:
                    print("   ❌ Item '05' NÃO encontrado no HTML!")
                
                if "ELE001" in html_content:
                    print("   ✅ Outros itens encontrados no HTML!")
                else:
                    print("   ❌ Nenhum item encontrado no HTML!")
                    
            else:
                print(f"   ❌ Erro ao carregar página: {response.status_code}")
                return False
            
            # Teste 2: Busca por "05"
            print("\n2. Testando busca por '05'...")
            response = client.get('/secretaria/inventario?busca=05')
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Busca executada com sucesso!")
                
                html_content = response.data.decode('utf-8')
                
                if "Item Teste Código 05" in html_content:
                    print("   ✅ Item '05' encontrado na busca!")
                else:
                    print("   ❌ Item '05' NÃO encontrado na busca!")
                    
                # Contar itens na resposta
                import re
                # Procurar por padrões de códigos
                codigos = re.findall(r'<td[^>]*>([^<]+)</td>', html_content)
                itens_encontrados = [c for c in codigos if any(char.isalnum() for char in c)]
                print(f"   📊 Possíveis itens na resposta: {len(itens_encontrados)}")
                
            else:
                print(f"   ❌ Erro na busca: {response.status_code}")
                return False
            
            # Teste 3: Verificar template
            print("\n3. Analisando template...")
            
            # Verificar se há JavaScript ou filtros que possam esconder itens
            if 'style="display: none"' in html_content:
                print("   ⚠️ Encontrado 'display: none' - itens podem estar ocultos!")
            
            if 'filter' in html_content.lower():
                print("   ⚠️ Encontrado JavaScript de filtro - pode estar interferindo!")
            
            # Verificar estrutura da tabela
            if '<table' in html_content and '</table>' in html_content:
                print("   ✅ Estrutura de tabela encontrada!")
                
                # Contar linhas da tabela
                linhas = html_content.count('<tr')
                print(f"   📊 Linhas de tabela: {linhas}")
                
            else:
                print("   ❌ Estrutura de tabela não encontrada!")
                
            return True
                
    except Exception as e:
        print(f"\n❌ Erro no teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = testar_interface_web()
    print("\n" + "=" * 40)
    if sucesso:
        print("🎉 TESTE WEB CONCLUÍDO!")
    else:
        print("❌ FALHA NO TESTE WEB!")
    print("=" * 40)