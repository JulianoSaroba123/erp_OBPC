#!/usr/bin/env python3
"""
Script para simular clique no botão de PDF e verificar redirecionamento
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from urllib.parse import urlparse

def testar_clique_pdf():
    """Simula o clique no botão de PDF e verifica redirecionamento"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 TESTE: Simulando clique no botão PDF")
    print("=" * 60)
    
    # Criar sessão para manter cookies
    session = requests.Session()
    
    try:
        # 1. Fazer login
        print("1. Fazendo login...")
        login_data = {
            'email': 'admin@obpc.com',
            'senha': '123456'
        }
        
        login_response = session.post(f"{base_url}/login", data=login_data)
        
        if login_response.status_code == 200:
            print("✅ Login realizado com sucesso!")
        else:
            print(f"❌ Erro no login: {login_response.status_code}")
            return False
        
        # 2. Acessar a lista de atas
        print("\n2. Acessando lista de atas...")
        lista_response = session.get(f"{base_url}/secretaria/atas")
        
        if lista_response.status_code == 200:
            print("✅ Lista de atas acessada!")
        else:
            print(f"❌ Erro ao acessar lista: {lista_response.status_code}")
            return False
        
        # 3. Testar clique no botão PDF (configurado para NÃO seguir redirecionamentos)
        print("\n3. Simulando clique no botão PDF...")
        pdf_url = f"{base_url}/secretaria/atas/pdf/4"
        
        print(f"📍 URL sendo acessada: {pdf_url}")
        
        # allow_redirects=False para ver se há redirecionamento
        pdf_response = session.get(pdf_url, allow_redirects=False)
        
        print(f"📊 Status Code: {pdf_response.status_code}")
        print(f"📄 Content-Type: {pdf_response.headers.get('Content-Type', 'N/A')}")
        print(f"📏 Content-Length: {len(pdf_response.content)} bytes")
        
        # Verificar se há redirecionamento
        if pdf_response.status_code in [301, 302, 303, 307, 308]:
            location = pdf_response.headers.get('Location', 'N/A')
            print(f"🔄 REDIRECIONAMENTO DETECTADO!")
            print(f"   Para: {location}")
            
            # Seguir o redirecionamento manualmente
            print("\n4. Seguindo redirecionamento...")
            final_response = session.get(pdf_response.headers['Location'])
            print(f"📊 Status final: {final_response.status_code}")
            print(f"📄 Content-Type final: {final_response.headers.get('Content-Type', 'N/A')}")
            
            if "atas" in final_response.url and "lista" in final_response.url:
                print("❌ PROBLEMA CONFIRMADO: Redirecionamento para lista de atas!")
                return False
            
        elif pdf_response.status_code == 200:
            content_type = pdf_response.headers.get('Content-Type', '')
            if 'application/pdf' in content_type:
                print("✅ PDF gerado com sucesso!")
                print(f"📄 Tamanho: {len(pdf_response.content)} bytes")
                
                # Salvar o PDF para teste
                with open('teste_ata_gerada.pdf', 'wb') as f:
                    f.write(pdf_response.content)
                print("💾 PDF salvo como 'teste_ata_gerada.pdf'")
                return True
            else:
                print("⚠️ Resposta HTML em vez de PDF")
                if "lista" in pdf_response.text.lower() and "atas" in pdf_response.text.lower():
                    print("❌ PROBLEMA: Retornando página de lista em vez de PDF!")
                return False
        else:
            print(f"❌ Erro inesperado: {pdf_response.status_code}")
            if pdf_response.text:
                print("Conteúdo:", pdf_response.text[:300] + "..." if len(pdf_response.text) > 300 else pdf_response.text)
            return False
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = testar_clique_pdf()
    
    print("\n" + "=" * 60)
    if sucesso:
        print("🎉 BOTÃO PDF FUNCIONANDO CORRETAMENTE!")
    else:
        print("❌ PROBLEMA COM O BOTÃO PDF DETECTADO!")
    print("=" * 60)