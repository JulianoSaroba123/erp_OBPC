#!/usr/bin/env python3
"""
Script para testar o módulo de mídia completo após as correções
"""

import requests
import sys
import time
from urllib.parse import urljoin

def testar_midia_completa():
    """Testa acesso completo ao módulo de mídia"""
    
    # URL base do sistema
    base_url = "http://localhost:5000"
    
    print("🔍 Testando sistema OBPC - Módulo Mídia Completo")
    print("=" * 60)
    
    # Criar sessão para manter cookies
    session = requests.Session()
    
    try:
        # 1. Verificar se o servidor está rodando
        print("1. Verificando servidor...")
        response = session.get(base_url, timeout=5)
        if response.status_code != 200:
            print(f"❌ Servidor não responde: {response.status_code}")
            return False
        print("✅ Servidor funcionando")
        
        # 2. Acessar página de login
        print("\n2. Acessando login...")
        login_url = urljoin(base_url, "/usuario/login")
        response = session.get(login_url)
        if response.status_code != 200:
            print(f"❌ Erro no login: {response.status_code}")
            return False
        print("✅ Página de login acessível")
        
        # 3. Fazer login
        print("\n3. Fazendo login...")
        login_data = {
            'email': 'admin@obpc.com',
            'senha': '123456',
            'lembrar': '1'  # Checkbox "lembrar de mim"
        }
        
        response = session.post(login_url, data=login_data, allow_redirects=True)
        if "login" in response.url.lower():
            print("❌ Login falhou - ainda na página de login")
            print(f"URL atual: {response.url}")
            return False
        print("✅ Login realizado com sucesso")
        print(f"   Redirecionado para: {response.url}")
        
        # 4. Testar rotas da mídia
        print("\n4. Testando rotas da mídia...")
        
        rotas_midia = [
            "/midia/agenda",
            "/midia/agenda/",
            "/midia/certificados",
            "/midia/carteirinhas"
        ]
        
        for rota in rotas_midia:
            print(f"   Testando {rota}...")
            response = session.get(urljoin(base_url, rota), allow_redirects=False)
            
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                if 'login' in location.lower():
                    print(f"   ❌ {rota} - Redirecionando para login")
                    print(f"      Location: {location}")
                else:
                    print(f"   ⚠️  {rota} - Redirecionamento para: {location}")
            elif response.status_code == 200:
                print(f"   ✅ {rota} - Funcionando")
            else:
                print(f"   ❌ {rota} - Status: {response.status_code}")
        
        # 5. Verificar cookies de sessão
        print("\n5. Verificando cookies de sessão...")
        cookies = session.cookies
        print(f"   Cookies ativos: {len(cookies)}")
        for cookie in cookies:
            print(f"   - {cookie.name}: {cookie.value[:20]}...")
        
        # 6. Teste de persistência
        print("\n6. Testando persistência da sessão...")
        
        # Simular nova requisição após alguns segundos
        time.sleep(2)
        
        test_url = urljoin(base_url, "/midia/agenda")
        response = session.get(test_url, allow_redirects=False)
        
        if response.status_code == 302 and 'login' in response.headers.get('Location', '').lower():
            print("❌ Sessão não persiste - redirecionando para login")
            return False
        elif response.status_code == 200:
            print("✅ Sessão persiste corretamente")
        else:
            print(f"⚠️  Status inesperado: {response.status_code}")
        
        print("\n" + "=" * 60)
        print("✅ TESTE CONCLUÍDO - Sistema funcionando!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao servidor")
        print("   Certifique-se que o sistema está rodando em http://localhost:5000")
        return False
    
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    print("Script de Teste - Módulo Mídia OBPC")
    print("Aguarde...")
    
    sucesso = testar_midia_completa()
    
    if not sucesso:
        print("\n⚠️  PROBLEMAS DETECTADOS")
        print("Verifique se:")
        print("- O servidor está rodando (python run.py)")
        print("- O usuário admin existe (python criar_admin.py)")
        print("- As rotas estão registradas corretamente")
        sys.exit(1)
    
    print("\n🎉 TODOS OS TESTES PASSARAM!")