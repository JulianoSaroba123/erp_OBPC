#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste final - verificar se a correção do template funcionou
"""

import requests
import time

def teste_final_inventario():
    """Teste final do inventário após as correções"""
    
    print("🎯 TESTE FINAL DO INVENTÁRIO")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    try:
        # 1. Login
        print("1. Fazendo login...")
        login_data = {
            'email': 'admin@obpc.com',
            'senha': '123456'
        }
        
        login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=True)
        print(f"   Login: {login_response.status_code}")
        
        # 2. Acessar inventário
        print("2. Acessando inventário...")
        response = session.get(f"{base_url}/secretaria/inventario")
        print(f"   Inventário: {response.status_code}")
        
        if response.status_code == 200:
            html = response.text
            
            # Análise detalhada
            checks = [
                ("Página carregada", response.status_code == 200),
                ("HTML válido", "<html" in html and "</html>" in html),
                ("Não é página de login", "Digite seu e-mail" not in html),
                ("Tabela presente", "<table" in html and "<tbody>" in html),
                ("Código 05 visível", "05" in html),
                ("Item teste visível", "Item Teste Código 05" in html),
                ("Lista vazia (problema)", "Nenhum item no inventário" in html),
                ("Valor total presente", "R$" in html and "20," in html),
                ("Botão cadastrar", "Cadastrar Novo Item" in html or "novo" in html.lower())
            ]
            
            print("\n   📊 Resultados da análise:")
            sucesso_total = 0
            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"      {status} {check_name}")
                if result and check_name != "Lista vazia (problema)":
                    sucesso_total += 1
                elif not result and check_name == "Lista vazia (problema)":
                    sucesso_total += 1
            
            # Salvar HTML final
            with open("debug_teste_final.html", "w", encoding="utf-8") as f:
                f.write(html)
            print(f"\n   💾 HTML final salvo em: debug_teste_final.html")
            
            # Resultado final
            if "Item Teste Código 05" in html or ("05" in html and "Nenhum item no inventário" not in html):
                print(f"\n   🎉 SUCESSO! O inventário está exibindo os itens!")
                print(f"   📊 Pontuação: {sucesso_total}/8 checks passed")
                
                # Verificar se há itens na tabela
                if "<tbody>" in html and "</tbody>" in html:
                    tbody_start = html.find("<tbody>")
                    tbody_end = html.find("</tbody>")
                    tbody_content = html[tbody_start:tbody_end]
                    
                    num_rows = tbody_content.count("<tr")
                    print(f"   📋 Linhas de dados na tabela: {num_rows}")
                
            elif "Nenhum item no inventário" in html:
                print(f"\n   ❌ PROBLEMA AINDA PERSISTE - Lista ainda aparece vazia")
                print(f"   🔍 O template ainda não está recebendo os dados corretamente")
            else:
                print(f"\n   ❓ RESULTADO INCONCLUSIVO - Verificar HTML salvo")
            
        # 3. Teste de busca específica
        print("\n3. Testando busca por código '05'...")
        search_response = session.get(f"{base_url}/secretaria/inventario?busca=05")
        print(f"   Busca: {search_response.status_code}")
        
        if search_response.status_code == 200:
            search_html = search_response.text
            
            if "05" in search_html and "Item Teste Código 05" in search_html:
                print("   ✅ Busca funcionando - item código 05 encontrado!")
            elif "Nenhum item encontrado" in search_html:
                print("   ❌ Busca não encontrou resultados")
            else:
                print("   ❓ Resultado da busca inconclusivo")
            
            # Salvar busca
            with open("debug_busca_final.html", "w", encoding="utf-8") as f:
                f.write(search_html)
            print(f"   💾 HTML da busca salvo em: debug_busca_final.html")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

if __name__ == "__main__":
    print("⏳ Aguardando servidor inicializar...")
    time.sleep(2)
    
    resultado = teste_final_inventario()
    
    if resultado:
        print("\n" + "=" * 50)
        print("🏁 TESTE FINAL CONCLUÍDO")
        print("📁 Arquivos salvos:")
        print("   - debug_teste_final.html")
        print("   - debug_busca_final.html")
        print("=" * 50)
    else:
        print("\n❌ TESTE FINAL FALHOU")