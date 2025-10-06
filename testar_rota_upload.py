#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste Direto da Rota de Upload - Sistema OBPC
Igreja O Brasil para Cristo - Tietê/SP

Script para testar diretamente a rota de upload
"""

import sys
import os
import requests
import io
from PIL import Image

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def criar_imagem_teste():
    """Cria uma imagem de teste pequena"""
    # Criar uma imagem simples de teste (100x100 pixels)
    img = Image.new('RGB', (100, 100), color='red')
    
    # Salvar em memória como JPEG
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG')
    img_buffer.seek(0)
    
    return img_buffer

def testar_rota_upload():
    """Testa a rota de upload diretamente"""
    print("🔧 TESTE DIRETO DA ROTA DE UPLOAD")
    print("=" * 40)
    
    # URL da aplicação
    base_url = "http://127.0.0.1:5000"
    
    try:
        # Primeiro, fazer login (se necessário)
        # Vamos tentar acessar a página de configurações primeiro
        session = requests.Session()
        
        print("📋 Testando acesso à página de configurações...")
        response = session.get(f"{base_url}/configuracoes")
        print(f"Status da página de configurações: {response.status_code}")
        
        if response.status_code == 302:
            print("⚠️  Redirecionamento detectado - fazendo login...")
            
            # Fazer login
            login_data = {
                'email': 'admin@obpc.com',
                'senha': '123456'
            }
            
            login_response = session.post(f"{base_url}/login", data=login_data)
            print(f"Status do login: {login_response.status_code}")
            
            # Tentar acessar configurações novamente
            response = session.get(f"{base_url}/configuracoes")
            print(f"Status da página de configurações após login: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Acesso à página de configurações OK")
            
            # Criar imagem de teste
            print("📋 Criando imagem de teste...")
            img_buffer = criar_imagem_teste()
            
            # Preparar dados para upload
            files = {
                'logo': ('test_logo.jpg', img_buffer, 'image/jpeg')
            }
            
            print("📋 Fazendo upload da imagem...")
            upload_response = session.post(f"{base_url}/configuracoes/upload-logo", files=files)
            
            print(f"Status do upload: {upload_response.status_code}")
            print(f"Content-Type: {upload_response.headers.get('content-type', 'N/A')}")
            
            if upload_response.headers.get('content-type', '').startswith('application/json'):
                json_data = upload_response.json()
                print(f"Resposta JSON: {json_data}")
                
                if json_data.get('success'):
                    print("✅ Upload realizado com sucesso!")
                    print(f"📁 Arquivo salvo em: {json_data.get('logo_path')}")
                else:
                    print(f"❌ Erro no upload: {json_data.get('message')}")
            else:
                print(f"Resposta não-JSON: {upload_response.text[:200]}...")
                
        else:
            print(f"❌ Erro ao acessar página de configurações: {response.status_code}")
            print(f"Conteúdo: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    testar_rota_upload()