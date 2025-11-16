#!/usr/bin/env python3
"""
Teste específico para certificados e carteiras
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def testar_certificados_carteiras():
    """Testa especificamente certificados e carteiras"""
    
    app = create_app()
    
    with app.test_client() as client:
        print("🔍 Teste específico: Certificados e Carteiras")
        print("=" * 60)
        
        # 1. Fazer login
        login_data = {
            'email': 'admin@obpc.com',
            'senha': '123456',
            'lembrar': '1'
        }
        
        response = client.post('/login', data=login_data, follow_redirects=True)
        print(f"✅ Login: {response.status_code}")
        
        # 2. Testar rotas específicas
        rotas_teste = [
            ('/midia/certificados', 'Certificados'),
            ('/midia/carteiras', 'Carteiras'),
            ('/midia/carteiras/', 'Carteiras (com barra)')
        ]
        
        for rota, nome in rotas_teste:
            print(f"\n📋 Testando: {nome}")
            print(f"   URL: {rota}")
            
            try:
                response = client.get(rota, follow_redirects=False)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ {nome}: Funcionando!")
                elif response.status_code == 302:
                    location = response.headers.get('Location', '')
                    print(f"   ⚠️  {nome}: Redirecionando para {location}")
                    if 'login' in location:
                        print(f"   ❌ Problema: Redirecionando para login")
                elif response.status_code == 404:
                    print(f"   ❌ {nome}: Rota não encontrada (404)")
                else:
                    print(f"   ⚠️  {nome}: Status inesperado {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ ERRO ao testar {nome}: {e}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    testar_certificados_carteiras()