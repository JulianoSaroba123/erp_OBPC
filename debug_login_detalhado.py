#!/usr/bin/env python3
"""
Script para diagnosticar problema específico do Flask-Login
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.usuario.usuario_model import Usuario
from flask_login import current_user

def diagnosticar_flask_login():
    """Diagnostica problemas específicos do Flask-Login"""
    
    app = create_app()
    
    with app.test_client() as client:
        with app.test_request_context():
            print("🔍 Diagnóstico Flask-Login")
            print("=" * 40)
            
            # 1. Verificar se login_manager está configurado
            from app.extensoes import login_manager
            print(f"✅ Login manager configurado: {login_manager.login_view}")
            
            # 2. Verificar user_loader
            try:
                usuario = login_manager._user_callback('1')
                if usuario:
                    print(f"✅ User loader funcionando: {usuario.nome}")
                else:
                    print("❌ User loader retornou None")
            except Exception as e:
                print(f"❌ Erro no user loader: {e}")
            
            # 3. Testar login direto
            print("\n🔐 Testando login...")
            
            login_data = {
                'email': 'admin@obpc.com',
                'senha': '123456',
                'lembrar': '1'
            }
            
            # Fazer login
            response = client.post('/login', data=login_data, follow_redirects=True)
            print(f"   Status: {response.status_code}")
            
            # Verificar se usuário está logado na sessão
            with client.session_transaction() as sess:
                print(f"   Chaves na sessão: {list(sess.keys())}")
                if '_user_id' in sess:
                    print(f"   User ID: {sess['_user_id']}")
                if '_fresh' in sess:
                    print(f"   Fresh: {sess['_fresh']}")
            
            # 4. Testar acesso simples a uma rota protegida
            print("\n🔒 Testando rota protegida...")
            response = client.get('/painel', follow_redirects=False)
            print(f"   Status painel: {response.status_code}")
            
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                print(f"   Redirecionado para: {location}")
            
            # 5. Testar mídia especificamente
            print("\n📺 Testando mídia...")
            response = client.get('/midia/agenda', follow_redirects=False)
            print(f"   Status mídia: {response.status_code}")
            
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                print(f"   Redirecionado para: {location}")
                
                # Analisar URL de redirecionamento
                if location == '/':
                    print("   ⚠️  Redirecionando para raiz - problema com login_required")
                elif 'login' in location:
                    print("   ⚠️  Redirecionando para login - usuário não autenticado")
                else:
                    print(f"   ⚠️  Redirecionamento inesperado: {location}")

if __name__ == "__main__":
    diagnosticar_flask_login()