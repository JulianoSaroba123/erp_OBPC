#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste específico para certificados - verificar autenticação e templates
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from flask_login import current_user

def testar_certificados_autenticacao():
    print("=" * 60)
    print("TESTE: Certificados com Autenticação")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        print("\n🔐 TESTANDO AUTENTICAÇÃO:")
        print("-" * 40)
        
        # Criar um usuário de teste
        from app.models import Usuario, db
        
        # Verificar se existe usuário admin
        admin = Usuario.query.filter_by(username='admin').first()
        if not admin:
            print("❌ Usuário admin não encontrado - criando...")
            admin = Usuario(
                username='admin',
                senha='admin123',
                nome_completo='Administrador',
                nivel_acesso='admin',
                ativo=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuário admin criado")
        else:
            print("✅ Usuário admin encontrado")
        
        with app.test_client() as client:
            # Fazer login
            print("\n🧪 Fazendo login...")
            login_response = client.post('/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=True)
            
            print(f"Status do login: {login_response.status_code}")
            
            # Testar certificados
            print("\n🧪 Testando rota /midia/certificados/")
            response = client.get('/midia/certificados/')
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Página de certificados carregada com sucesso!")
                # Verificar se tem conteúdo esperado
                content = response.data.decode('utf-8')
                if 'Certificados' in content:
                    print("✅ Conteúdo de certificados encontrado")
                else:
                    print("⚠️ Conteúdo de certificados não encontrado")
            else:
                print(f"❌ Erro: {response.status_code}")
                if response.status_code == 302:
                    print("🔄 Redirecionamento detectado")
                    print(f"Location: {response.headers.get('Location', 'Não especificado')}")
                
                # Mostrar erro
                error_text = response.data.decode('utf-8')[:500]
                print(f"Erro: {error_text}")

if __name__ == "__main__":
    testar_certificados_autenticacao()