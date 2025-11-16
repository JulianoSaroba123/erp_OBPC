#!/usr/bin/env python3
"""
Script para testar diretamente a rota de PDF das atas
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
import requests

def testar_rota_pdf():
    """Testa a rota de PDF diretamente"""
    
    # URL base
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 TESTE: Rota de PDF das Atas")
    print("=" * 50)
    
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
        
        if login_response.status_code == 200 and "painel" in login_response.url.lower():
            print("✅ Login realizado com sucesso!")
        else:
            print(f"❌ Erro no login: {login_response.status_code}")
            return False
        
        # 2. Testar rota de PDF (usando ID 4 que criamos)
        print("\n2. Testando rota de PDF...")
        pdf_url = f"{base_url}/secretaria/atas/pdf/4"
        
        pdf_response = session.get(pdf_url)
        
        print(f"Status: {pdf_response.status_code}")
        print(f"Content-Type: {pdf_response.headers.get('Content-Type', 'N/A')}")
        print(f"Content-Length: {len(pdf_response.content)} bytes")
        
        if pdf_response.status_code == 200:
            if 'application/pdf' in pdf_response.headers.get('Content-Type', ''):
                print("✅ PDF gerado com sucesso!")
                print(f"📄 Tamanho: {len(pdf_response.content)} bytes")
                return True
            else:
                print("⚠️ Resposta recebida, mas não é PDF")
                print("Conteúdo:", pdf_response.text[:200] + "..." if len(pdf_response.text) > 200 else pdf_response.text)
        else:
            print(f"❌ Erro na geração do PDF: {pdf_response.status_code}")
            if pdf_response.text:
                print("Erro:", pdf_response.text[:200] + "..." if len(pdf_response.text) > 200 else pdf_response.text)
        
        return False
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        return False

if __name__ == "__main__":
    sucesso = testar_rota_pdf()
    
    print("\n" + "=" * 50)
    if sucesso:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
    else:
        print("❌ PROBLEMAS DETECTADOS NO TESTE")
    print("=" * 50)