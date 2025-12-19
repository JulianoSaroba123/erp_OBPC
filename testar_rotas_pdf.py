#!/usr/bin/env python3
"""
Script para testar as rotas de PDF dos módulos Atas e Inventário
Sistema OBPC
"""

import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.secretaria.atas.atas_model import Ata
from app.secretaria.inventario.inventario_model import ItemInventario

def testar_rotas_pdf():
    """Testa as rotas de PDF"""
    app = create_app()
    
    with app.app_context():
        with app.test_client() as client:
            try:
                print("🌐 === TESTANDO ROTAS DE PDF ===")
                print()
                
                # Teste 1: Rota do inventário
                print("📦 Testando rota do inventário...")
                response = client.get('/secretaria/inventario/pdf')
                print(f"   Status Code: {response.status_code}")
                print(f"   Content-Type: {response.content_type}")
                print(f"   Tamanho da Resposta: {len(response.data)} bytes")
                
                if response.status_code == 200:
                    print("   ✅ Rota do inventário funcionando!")
                else:
                    print(f"   ❌ Erro na rota do inventário: {response.status_code}")
                    print(f"   Dados: {response.data.decode('utf-8')[:200]}...")
                
                print()
                
                # Teste 2: Rota das atas (precisa de um ID válido)
                ata = Ata.query.first()
                if ata:
                    print(f"📄 Testando rota das atas (ID: {ata.id})...")
                    response = client.get(f'/secretaria/atas/pdf/{ata.id}')
                    print(f"   Status Code: {response.status_code}")
                    print(f"   Content-Type: {response.content_type}")
                    print(f"   Tamanho da Resposta: {len(response.data)} bytes")
                    
                    if response.status_code == 200:
                        print("   ✅ Rota das atas funcionando!")
                    else:
                        print(f"   ❌ Erro na rota das atas: {response.status_code}")
                        print(f"   Dados: {response.data.decode('utf-8')[:200]}...")
                else:
                    print("📄 ❌ Nenhuma ata encontrada para teste")
                
                print()
                
                # Teste 3: Verificar todas as rotas registradas
                print("🗺️  Rotas registradas:")
                for rule in app.url_map.iter_rules():
                    if 'pdf' in rule.rule.lower():
                        print(f"   {rule.rule} → {rule.endpoint}")
                
                return True
                
            except Exception as e:
                print(f"❌ ERRO durante teste: {str(e)}")
                import traceback
                traceback.print_exc()
                return False

if __name__ == "__main__":
    sucesso = testar_rotas_pdf()
    if sucesso:
        print("\n✨ Teste de rotas concluído!")
    else:
        print("\n❌ Teste de rotas falharam!")
        sys.exit(1)