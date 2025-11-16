#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste completo com login e acesso ao inventário
"""

import requests
from urllib.parse import urlparse, parse_qs

def testar_com_login():
    """Testa acessando o inventário com login"""
    
    print("🔐 TESTE COM LOGIN E ACESSO AO INVENTÁRIO")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    try:
        # 1. Fazer login
        print("1. Fazendo login...")
        login_url = f"{base_url}/login"
        
        # Primeiro, pegar a página de login para pegar cookies
        login_page = session.get(login_url)
        print(f"   📄 Página de login: {login_page.status_code}")
        
        # Fazer POST do login
        login_data = {
            'email': 'admin@obpc.com',
            'senha': '123456'
        }
        
        login_response = session.post(login_url, data=login_data, allow_redirects=False)
        print(f"   🔑 Tentativa de login: {login_response.status_code}")
        
        if login_response.status_code == 302:
            redirect_location = login_response.headers.get('Location', '')
            print(f"   ↪️ Redirecionado para: {redirect_location}")
            
            # Seguir redirecionamento
            if redirect_location:
                if not redirect_location.startswith('http'):
                    redirect_location = base_url + redirect_location
                
                dashboard_response = session.get(redirect_location)
                print(f"   🏠 Dashboard: {dashboard_response.status_code}")
                
                if "Sair" in dashboard_response.text or "logout" in dashboard_response.text:
                    print("   ✅ Login realizado com sucesso!")
                else:
                    print("   ❌ Login pode ter falhado")
            
        # 2. Acessar inventário autenticado
        print("\n2. Acessando inventário autenticado...")
        inventario_url = f"{base_url}/secretaria/inventario"
        
        response = session.get(inventario_url)
        print(f"   📋 Status inventário: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Inventário acessado com sucesso!")
            
            html_content = response.text
            
            # Análise detalhada
            checks = [
                ("HTML válido", "<html" in html_content and "</html>" in html_content),
                ("Título correto", "inventário" in html_content.lower() or "Inventário" in html_content),
                ("Navbar presente", "navbar" in html_content.lower()),
                ("Tabela HTML", "<table" in html_content),
                ("Item código 05", "05" in html_content),
                ("Lista vazia (erro)", "nenhum item" in html_content.lower() and "inventário" in html_content.lower()),
                ("Botões de ação", "cadastrar" in html_content.lower() or "novo" in html_content.lower()),
                ("Campo de busca", "busca" in html_content.lower() or "search" in html_content.lower()),
                ("Dropdowns filtro", "categoria" in html_content.lower() and "estado" in html_content.lower()),
                ("JavaScript", "<script" in html_content),
                ("Bootstrap", "bootstrap" in html_content.lower()),
                ("Página de login (erro)", "Digite seu e-mail" in html_content and "senha" in html_content.lower())
            ]
            
            print("\n   📊 Análise do conteúdo autenticado:")
            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"      {status} {check_name}")
            
            # Salvar HTML autenticado
            with open("debug_inventario_autenticado.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"\n   💾 HTML autenticado salvo em: debug_inventario_autenticado.html")
            
            print(f"   📏 Tamanho: {len(html_content)} caracteres")
            
            # Verificar se ainda é página de login
            if "Digite seu e-mail" in html_content:
                print("   🚨 AINDA MOSTRANDO PÁGINA DE LOGIN - PROBLEMA DE AUTENTICAÇÃO!")
            elif "05" in html_content:
                print("   🎉 CÓDIGO 05 ENCONTRADO - INVENTÁRIO FUNCIONANDO!")
            elif "nenhum item" in html_content.lower():
                print("   ⚠️ MOSTRANDO 'NENHUM ITEM' - POSSÍVEL PROBLEMA NO TEMPLATE")
            else:
                print("   ❓ RESULTADO INCONCLUSIVO - VERIFIQUE O HTML SALVO")
        
        # 3. Testar busca específica
        print("\n3. Testando busca por código '05'...")
        search_url = f"{base_url}/secretaria/inventario?busca=05"
        search_response = session.get(search_url)
        
        print(f"   🔍 Status busca: {search_response.status_code}")
        
        if search_response.status_code == 200:
            if "05" in search_response.text:
                print("   ✅ Busca por '05' retornou resultados!")
            else:
                print("   ❌ Busca por '05' não retornou resultados")
            
            # Salvar HTML da busca
            with open("debug_busca_autenticada.html", "w", encoding="utf-8") as f:
                f.write(search_response.text)
            print(f"   💾 HTML da busca salvo em: debug_busca_autenticada.html")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao servidor")
        return False
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testando acesso ao inventário com autenticação...")
    resultado = testar_com_login()
    
    if resultado:
        print("\n" + "=" * 50)
        print("✅ TESTE AUTENTICADO CONCLUÍDO")
        print("📁 Verifique os arquivos HTML salvos:")
        print("   - debug_inventario_autenticado.html")
        print("   - debug_busca_autenticada.html")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ TESTE FALHOU")
        print("=" * 50)