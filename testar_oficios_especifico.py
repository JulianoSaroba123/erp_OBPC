#!/usr/bin/env python3
"""
Script para testar especificamente o módulo de Ofícios
Sistema OBPC
"""

import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.secretaria.oficios.oficios_model import Oficio

def testar_oficios_pdf():
    """Testa especificamente os ofícios"""
    app = create_app()
    
    with app.app_context():
        with app.test_client() as client:
            try:
                print("📄 === TESTANDO MÓDULO OFÍCIOS - PDF ===")
                print()
                
                # Verificar se há ofícios
                oficios = Oficio.query.all()
                print(f"📊 Ofícios disponíveis: {len(oficios)}")
                
                if len(oficios) == 0:
                    print("⚠️  Nenhum ofício encontrado. Execute criar_dados_oficios.py primeiro")
                    return False
                
                # Pegar o primeiro ofício
                oficio = oficios[0]
                print(f"🎯 Testando ofício: {oficio.numero} - {oficio.assunto}")
                print()
                
                # Testar a rota diretamente
                print("🌐 Testando rota de PDF...")
                
                # Simular login (sem autenticação real para teste)
                with client.session_transaction() as sess:
                    sess['_user_id'] = '1'
                    sess['_fresh'] = True
                
                # URL da rota do PDF
                url = f'/secretaria/oficios/pdf/{oficio.id}'
                print(f"   URL: {url}")
                
                response = client.get(url)
                print(f"   Status Code: {response.status_code}")
                print(f"   Content-Type: {response.content_type}")
                print(f"   Tamanho da Resposta: {len(response.data)} bytes")
                
                if response.status_code == 200:
                    print("   ✅ Rota funcionando!")
                    if response.content_type == 'application/pdf':
                        print("   ✅ Content-Type correto!")
                    else:
                        print(f"   ⚠️  Content-Type inesperado: {response.content_type}")
                else:
                    print(f"   ❌ Erro na rota: {response.status_code}")
                    if response.status_code == 302:
                        print("   📝 Redirecionamento (provavelmente para login)")
                        print(f"   Location: {response.headers.get('Location', 'N/A')}")
                    else:
                        print(f"   Dados: {response.data.decode('utf-8')[:200]}...")
                
                print()
                
                # Verificar template
                print("📋 Verificando template PDF...")
                template_path = 'app/secretaria/oficios/templates/oficios/pdf_oficio.html'
                if os.path.exists(template_path):
                    print("   ✅ Template existe")
                    with open(template_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f"   📏 Tamanho do template: {len(content)} caracteres")
                else:
                    print("   ❌ Template não encontrado!")
                    return False
                
                # Verificar diretório de saída
                print()
                print("📁 Verificando diretório de saída...")
                output_dir = 'app/static/oficios'
                if os.path.exists(output_dir):
                    print("   ✅ Diretório existe")
                    files = os.listdir(output_dir)
                    print(f"   📄 Arquivos: {len(files)}")
                    if files:
                        print("   Arquivos existentes:")
                        for f in files[-3:]:  # Últimos 3 arquivos
                            print(f"      • {f}")
                else:
                    print("   ❌ Diretório não encontrado!")
                
                # Verificar todas as rotas do módulo
                print()
                print("🗺️  Rotas do módulo oficios:")
                for rule in app.url_map.iter_rules():
                    if 'oficios' in rule.rule:
                        print(f"   {rule.rule} → {rule.endpoint}")
                
                return True
                
            except Exception as e:
                print(f"❌ ERRO durante teste: {str(e)}")
                import traceback
                traceback.print_exc()
                return False

if __name__ == "__main__":
    sucesso = testar_oficios_pdf()
    if sucesso:
        print("\n✨ Teste de ofícios concluído!")
    else:
        print("\n❌ Teste de ofícios falharam!")
        sys.exit(1)