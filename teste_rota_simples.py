#!/usr/bin/env python3
"""
Teste simples de rota protegida na mídia
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from flask_login import login_required, current_user

def testar_rota_simples():
    """Testa rota simples"""
    
    app = create_app()
    
    # Adicionar rota de teste simples
    @app.route('/teste-login')
    def teste_login():
        if current_user.is_authenticated:
            return f"Usuário logado: {current_user.nome}"
        else:
            return "Usuário não logado"
    
    @app.route('/teste-protegido')
    @login_required
    def teste_protegido():
        return f"Acesso protegido! Usuário: {current_user.nome}"
    
    with app.test_client() as client:
        print("🔍 Teste de rota simples")
        print("=" * 30)
        
        # 1. Fazer login
        login_data = {
            'email': 'admin@obpc.com',
            'senha': '123456',
            'lembrar': '1'
        }
        
        response = client.post('/login', data=login_data, follow_redirects=True)
        print(f"Login status: {response.status_code}")
        
        # 2. Testar rota simples (sem proteção)
        response = client.get('/teste-login')
        print(f"Teste simples: {response.status_code}")
        print(f"Conteúdo: {response.data.decode()}")
        
        # 3. Testar rota protegida
        response = client.get('/teste-protegido', follow_redirects=False)
        print(f"Teste protegido: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Conteúdo: {response.data.decode()}")
        elif response.status_code == 302:
            print(f"Redirecionado para: {response.headers.get('Location')}")
        
        # 4. Testar mídia original
        response = client.get('/midia/agenda', follow_redirects=False)
        print(f"Mídia original: {response.status_code}")
        
        if response.status_code == 302:
            print(f"Redirecionado para: {response.headers.get('Location')}")

if __name__ == "__main__":
    testar_rota_simples()