#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Testar as rotas corretas do inventário
"""

import requests
import time

def testar_rotas_corretas():
    """Testa as rotas corretas do inventário"""
    
    print("🌐 TESTE DAS ROTAS CORRETAS DO INVENTÁRIO")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    try:
        # 1. Testar rota principal do inventário
        print("1. Testando rota principal: /secretaria/inventario")
        inventario_url = f"{base_url}/secretaria/inventario"
        
        response = session.get(inventario_url, timeout=10)
        print(f"   📋 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Página carregada com sucesso!")
            
            html_content = response.text
            
            # Verificar elementos específicos
            checks = [
                ("HTML válido", "<html" in html_content and "</html>" in html_content),
                ("Título inventário", "inventário" in html_content.lower() or "Inventário" in html_content),
                ("Tabela HTML", "<table" in html_content),
                ("Item código 05", "05" in html_content),
                ("Lista vazia", "nenhum item" in html_content.lower() or "vazio" in html_content.lower()),
                ("Botão cadastrar", "cadastrar" in html_content.lower() or "novo" in html_content.lower()),
                ("Campo busca", "busca" in html_content.lower() or "search" in html_content.lower()),
                ("JavaScript", "<script" in html_content)
            ]
            
            print("\n   📊 Análise do conteúdo:")
            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"      {status} {check_name}")
            
            # Salvar HTML
            with open("debug_inventario_real.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"\n   💾 HTML salvo em: debug_inventario_real.html")
            
            # Verificar tamanho
            print(f"   📏 Tamanho: {len(html_content)} caracteres")
            
            # Procurar por erros específicos
            if "error" in html_content.lower() or "exception" in html_content.lower():
                print("   ⚠️ POSSÍVEL ERRO NO TEMPLATE DETECTADO!")
            
        elif response.status_code == 302:
            location = response.headers.get('Location', 'N/A')
            print(f"   🔄 Redirecionamento para: {location}")
            
            # Se for redirecionamento para login, tentar acessar
            if 'login' in location:
                print("   🔑 Redirecionado para login - problema de autenticação")
        
        elif response.status_code == 500:
            print("   💥 Erro 500 - problema no servidor")
            print(f"   📄 Conteúdo: {response.text[:500]}...")
            
        else:
            print(f"   ❌ Status inesperado: {response.status_code}")
        
        # 2. Testar com parâmetros
        print("\n2. Testando com parâmetros de busca...")
        search_url = f"{base_url}/secretaria/inventario?busca=05"
        response = session.get(search_url, timeout=10)
        print(f"   🔍 Busca por '05': {response.status_code}")
        
        if response.status_code == 200:
            if "05" in response.text:
                print("   ✅ Código 05 encontrado!")
            else:
                print("   ❌ Código 05 não encontrado")
        
        # 3. Testar outras rotas relacionadas
        print("\n3. Testando outras rotas...")
        
        rotas_teste = [
            ("/secretaria/inventario/novo", "Página de cadastro"),
            ("/secretaria/inventario/pdf", "PDF do inventário")
        ]
        
        for rota, descricao in rotas_teste:
            url = f"{base_url}{rota}"
            try:
                resp = session.get(url, timeout=5)
                print(f"   📄 {descricao}: {resp.status_code}")
            except Exception as e:
                print(f"   ❌ {descricao}: Erro - {str(e)}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Servidor não está rodando")
        return False
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testando rotas corretas do inventário...")
    resultado = testar_rotas_corretas()
    
    if resultado:
        print("\n" + "=" * 50)
        print("✅ TESTE CONCLUÍDO - VERIFIQUE debug_inventario_real.html")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)  
        print("❌ TESTE FALHOU")
        print("=" * 50)