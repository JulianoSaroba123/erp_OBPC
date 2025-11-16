#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Testar requisição HTTP real para a rota de inventário
"""

import requests
import time
import sys

def testar_requisicao_inventario():
    """Testa requisição HTTP real para a página de inventário"""
    
    print("🌐 TESTE DE REQUISIÇÃO HTTP PARA INVENTÁRIO")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000"
    
    try:
        # 1. Testar se o servidor está rodando
        print("1. Testando conexão com servidor...")
        response = requests.get(base_url, timeout=5)
        print(f"   ✅ Servidor respondeu: {response.status_code}")
        
        # 2. Testar a página de login
        print("\n2. Testando página de login...")
        login_url = f"{base_url}/auth/login"
        response = requests.get(login_url, timeout=5)
        print(f"   📝 Login page: {response.status_code}")
        
        # 3. Simular login (se necessário)
        session = requests.Session()
        
        # 4. Testar acesso direto à página de inventário
        print("\n3. Testando acesso à página de inventário...")
        inventario_url = f"{base_url}/secretaria/inventario/lista"
        
        response = session.get(inventario_url, timeout=10)
        print(f"   📋 Inventário page: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Página carregada com sucesso!")
            
            # Verificar conteúdo HTML
            html_content = response.text
            
            # Procurar por elementos específicos
            checks = [
                ("Lista de Itens", "Lista de Itens" in html_content),
                ("Tabela de inventário", "table" in html_content and "inventario" in html_content),
                ("Item código 05", "05" in html_content),
                ("Nenhum item", "Nenhum item" in html_content or "inventário vazio" in html_content.lower()),
                ("Template renderizado", "<html" in html_content and "</html>" in html_content)
            ]
            
            print("\n   📊 Análise do conteúdo HTML:")
            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"      {status} {check_name}: {result}")
            
            # Salvar HTML para análise
            with open("debug_inventario_html.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"\n   💾 HTML salvo em: debug_inventario_html.html")
            
            # Verificar tamanho do HTML
            print(f"   📏 Tamanho do HTML: {len(html_content)} caracteres")
            
        elif response.status_code == 302:
            print("   🔄 Redirecionamento detectado (provável problema de autenticação)")
            print(f"   📍 Location: {response.headers.get('Location', 'N/A')}")
        elif response.status_code == 404:
            print("   ❌ Página não encontrada - problema na rota")
        elif response.status_code == 500:
            print("   💥 Erro interno do servidor")
        else:
            print(f"   ⚠️ Status code inesperado: {response.status_code}")
        
        # 5. Testar com parâmetros de busca
        print("\n4. Testando busca por código '05'...")
        search_url = f"{base_url}/secretaria/inventario/lista?busca=05"
        response = session.get(search_url, timeout=10)
        print(f"   🔍 Busca por '05': {response.status_code}")
        
        if response.status_code == 200:
            html_search = response.text
            if "05" in html_search:
                print("   ✅ Código 05 encontrado na busca!")
            else:
                print("   ❌ Código 05 NÃO encontrado na busca")
            
            # Salvar HTML da busca
            with open("debug_busca_05.html", "w", encoding="utf-8") as f:
                f.write(html_search)
            print(f"   💾 HTML da busca salvo em: debug_busca_05.html")
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao servidor")
        print("   Verifique se o Flask está rodando em http://127.0.0.1:5000")
        return False
    except requests.exceptions.Timeout:
        print("❌ Erro: Timeout na requisição")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return False
    
    return True

def iniciar_servidor_flask():
    """Inicia o servidor Flask em background"""
    import subprocess
    import time
    
    print("🚀 Iniciando servidor Flask...")
    
    # Iniciar servidor
    process = subprocess.Popen([
        "python", "run.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Aguardar alguns segundos para o servidor iniciar
    time.sleep(3)
    
    return process

if __name__ == "__main__":
    print("Iniciando teste completo da interface web...")
    
    # Tentar se conectar primeiro
    try:
        response = requests.get("http://127.0.0.1:5000", timeout=2)
        print("✅ Servidor já está rodando!")
    except:
        print("🚀 Servidor não está rodando, iniciando...")
        flask_process = iniciar_servidor_flask()
    
    # Executar testes
    resultado = testar_requisicao_inventario()
    
    if resultado:
        print("\n" + "=" * 50)
        print("🎉 TESTES CONCLUÍDOS - VERIFIQUE OS ARQUIVOS HTML SALVOS")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ TESTES FALHARAM - VERIFIQUE SE O SERVIDOR ESTÁ RODANDO")
        print("=" * 50)