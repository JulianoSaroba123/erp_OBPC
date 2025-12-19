#!/usr/bin/env python3
"""
Script para fazer login automático e verificar se o sistema está funcionando
"""

import requests
import json

def testar_login_automatico():
    """Testa login via requests"""
    print("🤖 TESTE DE LOGIN AUTOMÁTICO")
    print("=" * 35)
    
    base_url = "http://127.0.0.1:5000"
    
    # Criar sessão
    session = requests.Session()
    
    try:
        # 1. Acessar página de login
        print("📄 Acessando página de login...")
        response = session.get(f"{base_url}/login")
        print(f"  Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Erro ao acessar login: {response.status_code}")
            return
        
        # 2. Fazer login
        print("🔐 Tentando fazer login...")
        login_data = {
            'email': 'admin@obpc.com',
            'senha': '123456'
        }
        
        response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ Login bem-sucedido! (Redirecionamento)")
            redirect_url = response.headers.get('Location', '')
            print(f"  Redirecionando para: {redirect_url}")
        elif response.status_code == 200:
            print("⚠️ Login retornou 200 - verificar se houve erro")
            if "erro" in response.text.lower() or "invalid" in response.text.lower():
                print("❌ Erro no login detectado")
            else:
                print("✅ Login parece ter funcionado")
        else:
            print(f"❌ Erro no login: {response.status_code}")
        
        # 3. Tentar acessar área protegida
        print("🔒 Testando acesso à área protegida...")
        response = session.get(f"{base_url}/midia/certificados")
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Acesso autorizado à área de certificados!")
            if "Certificados" in response.text:
                print("✅ Página de certificados carregou corretamente!")
            if "Nenhum certificado encontrado" in response.text:
                print("📋 Lista vazia - normal após reset do banco")
            elif "TESTE VIA FLASK" in response.text:
                print("📋 Certificado de teste encontrado!")
        elif response.status_code == 302:
            print("❌ Redirecionado - login não persistiu")
        else:
            print(f"❌ Erro ao acessar certificados: {response.status_code}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao Flask")
        print("   Verifique se o servidor está rodando em http://127.0.0.1:5000")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    testar_login_automatico()