#!/usr/bin/env python3
"""
Script para testar login usando Flask test client
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def testar_login_flask_client():
    """Testa login usando Flask test client"""
    
    app = create_app()
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            # Configurar sessão para testes
            sess.permanent = True
            
        print("🔍 Testando login com Flask test client...")
        print("=" * 50)
        
        # 1. Acessar página de login
        print("1. Acessando página de login...")
        response = client.get('/login')
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ Erro ao acessar login")
            return False
        
        print("✅ Página de login acessível")
        
        # 2. Fazer login
        print("\n2. Fazendo login...")
        login_data = {
            'email': 'admin@obpc.com',
            'senha': '123456',
            'lembrar': '1'
        }
        
        response = client.post('/login', data=login_data, follow_redirects=True)
        print(f"   Status final: {response.status_code}")
        print(f"   URL final: {response.request.path}")
        
        if 'painel' in response.request.path:
            print("✅ Login realizado com sucesso!")
        else:
            print(f"⚠️  URL final inesperada: {response.request.path}")
            return False
        
        # 3. Testar acesso à mídia após login
        print("\n3. Testando acesso à mídia...")
        
        response = client.get('/midia/agenda', follow_redirects=False)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Acesso à mídia funcionando!")
            return True
        elif response.status_code == 302:
            location = response.headers.get('Location', '')
            print(f"   Redirecionado para: {location}")
            
            if 'login' in location:
                print("❌ Ainda redirecionando para login")
                
                # Verificar se há dados na sessão
                with client.session_transaction() as sess:
                    print(f"   Dados da sessão: {list(sess.keys())}")
                    if '_user_id' in sess:
                        print(f"   User ID na sessão: {sess['_user_id']}")
                    else:
                        print("   ❌ Nenhum _user_id na sessão")
                
                return False
            else:
                print(f"⚠️  Redirecionamento inesperado: {location}")
        else:
            print(f"❌ Status inesperado: {response.status_code}")
        
        return False

if __name__ == "__main__":
    print("TESTE DE LOGIN - Flask Test Client")
    print("=" * 50)
    
    sucesso = testar_login_flask_client()
    
    if sucesso:
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("O sistema de login e mídia estão funcionando.")
    else:
        print("\n❌ PROBLEMAS DETECTADOS")
        print("Verifique a configuração de sessões e cookies.")
    
    print("=" * 50)