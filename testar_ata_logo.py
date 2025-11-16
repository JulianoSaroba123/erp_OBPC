#!/usr/bin/env python3
"""
Teste para verificar se o logo está sendo inserido no PDF das atas
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
import requests

def testar_pdf_com_logo():
    """Testa se o PDF das atas inclui o logo"""
    
    print("🧪 TESTE: Logo no PDF das Atas")
    print("=" * 40)
    
    # URL base
    base_url = "http://127.0.0.1:5000"
    
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
        
        # 2. Gerar PDF da ata ID 4
        print("\n2. Gerando PDF da ata...")
        pdf_url = f"{base_url}/secretaria/atas/pdf/4"
        
        pdf_response = session.get(pdf_url)
        
        print(f"Status: {pdf_response.status_code}")
        print(f"Content-Type: {pdf_response.headers.get('Content-Type', 'N/A')}")
        print(f"Content-Length: {len(pdf_response.content)} bytes")
        
        if pdf_response.status_code == 200 and 'application/pdf' in pdf_response.headers.get('Content-Type', ''):
            # Salvar PDF para análise
            with open('ata_com_logo_teste.pdf', 'wb') as f:
                f.write(pdf_response.content)
            
            print("✅ PDF gerado com sucesso!")
            print(f"📄 Tamanho: {len(pdf_response.content)} bytes")
            print("💾 PDF salvo como 'ata_com_logo_teste.pdf'")
            
            # Verificar se o PDF é maior que antes (indicando possível logo)
            if len(pdf_response.content) > 4000:  # Tamanho anterior era ~3697 bytes
                print("🎯 PDF parece incluir mais conteúdo (possivelmente o logo)!")
                return True
            else:
                print("⚠️ PDF tem tamanho similar ao anterior - logo pode não ter sido incluído")
                return False
        else:
            print(f"❌ Erro na geração do PDF: {pdf_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        return False

if __name__ == "__main__":
    sucesso = testar_pdf_com_logo()
    
    print("\n" + "=" * 40)
    if sucesso:
        print("🎉 TESTE CONCLUÍDO - Logo possivelmente incluído!")
        print("📋 Abra 'ata_com_logo_teste.pdf' para verificar")
    else:
        print("❌ PROBLEMAS DETECTADOS NO TESTE")
    print("=" * 40)