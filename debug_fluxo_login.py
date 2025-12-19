#!/usr/bin/env python3
"""
Script para testar fluxo completo de login via HTTP
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
import requests
from urllib.parse import urljoin

def testar_fluxo_login_completo():
    """Testa o fluxo completo de login"""
    
    base_url = "http://localhost:5000"
    
    print("🔍 Testando fluxo completo de login...")
    print("=" * 50)
    
    # Criar sessão para manter cookies
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    try:
        # 1. Acessar página inicial
        print("1. Acessando página inicial...")
        response = session.get(base_url)
        print(f"   Status: {response.status_code}")
        print(f"   URL final: {response.url}")
        print(f"   Cookies após acesso inicial: {len(session.cookies)}")
        
        # 2. Acessar página de login diretamente
        print("\n2. Acessando página de login...")
        login_url = urljoin(base_url, "/usuario/login")
        response = session.get(login_url)
        print(f"   Status: {response.status_code}")
        print(f"   Cookies após login page: {len(session.cookies)}")
        
        # 3. Fazer login
        print("\n3. Fazendo login...")
        login_data = {
            'email': 'admin@obpc.com',
            'senha': '123456',
            'lembrar': '1'
        }
        
        response = session.post(login_url, data=login_data, allow_redirects=True)
        print(f"   Status: {response.status_code}")
        print(f"   URL após login: {response.url}")
        print(f"   Cookies após login: {len(session.cookies)}")
        
        # Mostrar cookies
        for cookie in session.cookies:
            print(f"     - {cookie.name}: {cookie.value[:30]}...")
        
        # 4. Verificar se logou com sucesso
        if "login" in response.url.lower():
            print("   ❌ Login falhou - ainda na página de login")
            
            # Verificar se há mensagens de erro na resposta
            if "alert" in response.text.lower() or "erro" in response.text.lower():
                print("     Possível erro de credenciais")
            
            return False
        else:
            print("   ✅ Login realizado com sucesso!")
        
        # 5. Testar acesso à mídia
        print("\n4. Testando acesso à mídia...")
        midia_url = urljoin(base_url, "/midia/agenda")
        response = session.get(midia_url, allow_redirects=False)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            print(f"   Redirecionamento para: {location}")
            
            if 'login' in location.lower():
                print("   ❌ Ainda redirecionando para login!")
                
                # Verificar se o cookie de sessão existe
                session_cookie = None
                for cookie in session.cookies:
                    if 'session' in cookie.name.lower():
                        session_cookie = cookie
                        break
                
                if session_cookie:
                    print(f"   Cookie de sessão encontrado: {session_cookie.name}")
                    print(f"   Valor: {session_cookie.value[:50]}...")
                    print(f"   Seguro: {session_cookie.secure}")
                    print(f"   HttpOnly: {session_cookie.has_nonstandard_attr('HttpOnly')}")
                else:
                    print("   ❌ Nenhum cookie de sessão encontrado!")
                
                return False
            else:
                print(f"   ⚠️  Redirecionamento para: {location}")
        
        elif response.status_code == 200:
            print("   ✅ Acesso à mídia funcionando!")
            return True
        
        else:
            print(f"   ⚠️  Status inesperado: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Servidor não está rodando")
        print("Execute: python run.py")
        return False
    
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    print("TESTE COMPLETO DE LOGIN - OBPC")
    print("=" * 50)
    
    sucesso = testar_fluxo_login_completo()
    
    if sucesso:
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
    else:
        print("\n❌ PROBLEMAS DETECTADOS NO FLUXO DE LOGIN")
    
    print("=" * 50)