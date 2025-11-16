#!/usr/bin/env python3
"""
Teste de acesso direto ao módulo mídia com login automático
"""

import requests
import sys
import os

def testar_acesso_midia():
    """Testa acesso ao módulo mídia com login simulado"""
    base_url = "http://127.0.0.1:5000"
    
    # Criar sessão para manter cookies
    session = requests.Session()
    
    print("🔍 TESTE DE ACESSO DIRETO - MÓDULO MÍDIA")
    print("="*50)
    
    try:
        # 1. Verificar se servidor está rodando
        print("1️⃣ Verificando servidor...")
        response = session.get(base_url, timeout=5)
        if response.status_code == 200:
            print("   ✅ Servidor rodando")
        else:
            print(f"   ❌ Servidor com problema: {response.status_code}")
            return False
        
        # 2. Testar página de login
        print("\n2️⃣ Testando página de login...")
        login_response = session.get(f"{base_url}/login")
        if login_response.status_code == 200:
            print("   ✅ Página de login acessível")
        else:
            print(f"   ❌ Problema na página de login: {login_response.status_code}")
            return False
        
        # 3. Tentar fazer login
        print("\n3️⃣ Tentando login...")
        login_data = {
            'email': 'admin@obpc.com',
            'senha': '123456'
        }
        
        # Extrair CSRF token se existir
        if 'csrf_token' in login_response.text:
            import re
            csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', login_response.text)
            if csrf_match:
                login_data['csrf_token'] = csrf_match.group(1)
                print("   🔐 CSRF token encontrado")
        
        login_post = session.post(f"{base_url}/login", data=login_data)
        
        if login_post.status_code == 302:
            print("   ✅ Login realizado com sucesso (redirecionamento)")
        elif "dashboard" in login_post.text.lower() or "painel" in login_post.text.lower():
            print("   ✅ Login realizado com sucesso")
        else:
            print(f"   ⚠️ Status do login: {login_post.status_code}")
            print("   💡 Tentando continuar mesmo assim...")
        
        # 4. Testar acesso ao módulo mídia
        print("\n4️⃣ Testando acesso ao módulo mídia...")
        
        # Testar várias rotas
        rotas_teste = [
            '/midia/agenda',
            '/midia/agenda/',
            '/midia/certificados',
            '/midia/carteiras'
        ]
        
        sucesso = False
        for rota in rotas_teste:
            print(f"   🎯 Testando: {rota}")
            midia_response = session.get(f"{base_url}{rota}")
            
            if midia_response.status_code == 200:
                print(f"   ✅ {rota} - FUNCIONANDO!")
                sucesso = True
            elif midia_response.status_code == 302:
                location = midia_response.headers.get('Location', 'N/A')
                if 'login' in location:
                    print(f"   ❌ {rota} - Redirecionando para login")
                else:
                    print(f"   🔄 {rota} - Redirecionamento para: {location}")
            else:
                print(f"   ❌ {rota} - Status: {midia_response.status_code}")
        
        if sucesso:
            print("\n✅ PELO MENOS UMA ROTA FUNCIONOU!")
        else:
            print("\n❌ NENHUMA ROTA FUNCIONOU")
        
        # 5. Informações para teste manual
        print("\n" + "="*50)
        print("🌐 TESTE MANUAL:")
        print(f"   URL: {base_url}")
        print("   Email: admin@obpc.com")
        print("   Senha: 123456")
        print("   Mídia: http://127.0.0.1:5000/midia/agenda")
        print("="*50)
        
        return sucesso
        
    except requests.exceptions.ConnectionError:
        print("❌ ERRO: Servidor não está rodando!")
        print("💡 Execute: python run.py")
        return False
    except Exception as e:
        print(f"❌ ERRO inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    testar_acesso_midia()