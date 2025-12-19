#!/usr/bin/env python3
"""
Script para testar todas as rotas da mídia
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def testar_todas_rotas_midia():
    """Testa todas as rotas da mídia"""
    
    app = create_app()
    
    with app.test_client() as client:
        print("🎬 Testando todas as rotas da mídia")
        print("=" * 50)
        
        # 1. Fazer login
        login_data = {
            'email': 'admin@obpc.com',
            'senha': '123456',
            'lembrar': '1'
        }
        
        response = client.post('/login', data=login_data, follow_redirects=True)
        print(f"✅ Login: {response.status_code}")
        
        # 2. Testar rotas da mídia
        rotas_midia = [
            ('/midia/agenda', 'Agenda Semanal'),
            ('/midia/agenda/', 'Agenda Semanal (com barra)'),
            ('/midia/certificados', 'Certificados'),
            ('/midia/carteiras', 'Carteiras'),
            ('/midia/agenda/novo', 'Novo Agenda'),
            ('/midia/certificados/novo', 'Novo Certificado'),
            ('/midia/carteiras/nova', 'Nova Carteira')
        ]
        
        print("\n📊 Testando rotas...")
        for rota, descricao in rotas_midia:
            response = client.get(rota, follow_redirects=False)
            
            if response.status_code == 200:
                print(f"✅ {descricao}: {response.status_code}")
            elif response.status_code == 302:
                location = response.headers.get('Location', '')
                if 'login' in location:
                    print(f"❌ {descricao}: Redirecionando para login")
                else:
                    print(f"⚠️  {descricao}: Redirecionando para {location}")
            else:
                print(f"❌ {descricao}: Status {response.status_code}")
        
        print("\n" + "=" * 50)
        print("🎉 TESTE COMPLETO DAS ROTAS DA MÍDIA FINALIZADO!")

if __name__ == "__main__":
    testar_todas_rotas_midia()