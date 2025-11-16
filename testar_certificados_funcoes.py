#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste específico para certificados - verificar se funções existem e templates estão corretos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def testar_funcoes_certificados():
    print("=" * 60)
    print("TESTE: Funções dos Certificados")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        # Verificar rotas do blueprint midia
        from app.midia.midia_routes import midia_bp
        
        print("\n📋 ROTAS DO BLUEPRINT MÍDIA:")
        print("-" * 40)
        
        for rule in app.url_map.iter_rules():
            if rule.endpoint and rule.endpoint.startswith('midia.'):
                print(f"✅ {rule.endpoint} -> {rule.rule}")
        
        print("\n🔍 VERIFICAR TEMPLATES:")
        print("-" * 40)
        
        # Tentar renderizar página de certificados
        with app.test_client() as client:
            try:
                # Simular login (necessário para acessar páginas protegidas)
                with client.session_transaction() as sess:
                    sess['user_id'] = 1
                    sess['_fresh'] = True
                
                print("🧪 Testando rota /midia/certificados/")
                response = client.get('/midia/certificados/')
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("✅ Template renderizado com sucesso!")
                else:
                    print(f"❌ Erro: {response.status_code}")
                    if hasattr(response, 'data'):
                        error_text = response.data.decode('utf-8')[:500]
                        print(f"Erro: {error_text}")
                        
            except Exception as e:
                print(f"❌ Erro ao testar certificados: {str(e)}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    testar_funcoes_certificados()