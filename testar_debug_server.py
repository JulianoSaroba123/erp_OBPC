#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Testar o servidor com debug ativo
"""

import requests
import time

def testar_servidor_debug():
    """Faz login e acessa inventário no servidor de debug"""
    
    print("🧪 TESTANDO SERVIDOR COM DEBUG ATIVO")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5001"  # Porta 5001 do debug
    session = requests.Session()
    
    try:
        # 1. Fazer login
        print("1. Fazendo login no servidor debug...")
        login_url = f"{base_url}/login"
        
        login_data = {
            'email': 'admin@obpc.com',
            'senha': '123456'
        }
        
        login_response = session.post(login_url, data=login_data, allow_redirects=True)
        print(f"   Login: {login_response.status_code}")
        
        # 2. Acessar inventário (isso deve gerar logs no console)
        print("2. Acessando inventário com debug...")
        inventario_url = f"{base_url}/secretaria/inventario"
        
        response = session.get(inventario_url)
        print(f"   Inventário: {response.status_code}")
        
        if response.status_code == 200:
            # Verificar se agora tem dados
            html = response.text
            
            if "Nenhum item no inventário" in html:
                print("   ❌ AINDA MOSTRA LISTA VAZIA")
            elif "Item Teste Código 05" in html or "05" in html:
                print("   ✅ DADOS ENCONTRADOS!")
            else:
                print("   ❓ RESULTADO INCONCLUSIVO")
            
            # Salvar para análise
            with open("debug_com_logs.html", "w", encoding="utf-8") as f:
                f.write(html)
            print(f"   💾 HTML salvo em: debug_com_logs.html")
        
        # 3. Testar busca específica
        print("3. Testando busca por '05'...")
        search_url = f"{base_url}/secretaria/inventario?busca=05"
        
        search_response = session.get(search_url)
        print(f"   Busca: {search_response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

if __name__ == "__main__":
    print("⏳ Aguardando 2 segundos para o servidor inicializar...")
    time.sleep(2)
    
    resultado = testar_servidor_debug()
    
    if resultado:
        print("\n" + "=" * 50)
        print("✅ TESTE CONCLUÍDO")
        print("📊 VERIFIQUE OS LOGS NO CONSOLE DO SERVIDOR DEBUG!")
        print("📁 HTML salvo em: debug_com_logs.html")
        print("=" * 50)
    else:
        print("\n❌ TESTE FALHOU")