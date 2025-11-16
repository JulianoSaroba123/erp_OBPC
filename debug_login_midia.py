"""
Debug do Sistema de Login - Sistema OBPC
Testando autenticação e acesso ao módulo Mídia
"""

import requests
import json

def testar_login_e_midia():
    """Testa login e acesso ao módulo mídia"""
    base_url = "http://127.0.0.1:5000"
    
    # Criar sessão para manter cookies
    session = requests.Session()
    
    print("🔍 TESTE DE AUTENTICAÇÃO - MÓDULO MÍDIA")
    print("="*50)
    
    try:
        # 1. Testar página de login
        print("1️⃣ Testando página de login...")
        login_page = session.get(f"{base_url}/login")
        print(f"   Status: {login_page.status_code}")
        
        if login_page.status_code == 200:
            print("   ✅ Página de login acessível")
        else:
            print("   ❌ Problema na página de login")
            return
        
        # 2. Tentar acessar mídia sem login
        print("\n2️⃣ Testando acesso à mídia sem login...")
        midia_response = session.get(f"{base_url}/midia/agenda", allow_redirects=False)
        print(f"   Status: {midia_response.status_code}")
        
        if midia_response.status_code == 302:
            print("   ✅ Redirecionamento para login funcionando")
            print(f"   🔄 Redirecionado para: {midia_response.headers.get('Location', 'N/A')}")
        else:
            print("   ⚠️ Comportamento inesperado")
        
        # 3. Verificar se existe CSRF token na página de login
        print("\n3️⃣ Verificando CSRF token...")
        if 'csrf_token' in login_page.text or 'name="csrf_token"' in login_page.text:
            print("   ✅ CSRF token encontrado")
        else:
            print("   ⚠️ CSRF token não encontrado")
        
        # 4. Testar formulário de login (simulado)
        print("\n4️⃣ Informações para login manual:")
        print("   📧 Email: admin@obpc.com")
        print("   🔑 Senha: (use a senha cadastrada)")
        print(f"   🌐 URL Login: {base_url}/login")
        print(f"   🎯 URL Mídia: {base_url}/midia/agenda")
        
        print("\n" + "="*50)
        print("📋 INSTRUÇÕES:")
        print("1. Acesse o link de login acima")
        print("2. Use as credenciais fornecidas")
        print("3. Após o login, teste o link da mídia")
        print("4. Se ainda der erro, verifique o console do navegador")
        print("="*50)
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Servidor não está rodando!")
        print("🚀 Execute: python run.py")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")

if __name__ == '__main__':
    testar_login_e_midia()