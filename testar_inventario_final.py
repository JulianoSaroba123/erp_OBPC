#!/usr/bin/env python3
"""
Teste para verificar se o PDF do inventário está funcionando
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests

def testar_pdf_inventario():
    """Testa se o PDF do inventário está funcionando"""
    
    print("🧪 TESTE: PDF do Inventário")
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
        
        # 2. Testar PDF do inventário
        print("\n2. Gerando PDF do inventário...")
        pdf_url = f"{base_url}/secretaria/inventario/pdf"
        
        pdf_response = session.get(pdf_url)
        
        print(f"Status: {pdf_response.status_code}")
        print(f"Content-Type: {pdf_response.headers.get('Content-Type', 'N/A')}")
        print(f"Content-Length: {len(pdf_response.content)} bytes")
        
        if pdf_response.status_code == 200:
            content_type = pdf_response.headers.get('Content-Type', '')
            if 'application/pdf' in content_type:
                # Salvar PDF para análise
                with open('inventario_teste_final.pdf', 'wb') as f:
                    f.write(pdf_response.content)
                
                print("✅ PDF gerado com sucesso!")
                print(f"📄 Tamanho: {len(pdf_response.content)} bytes")
                print("💾 PDF salvo como 'inventario_teste_final.pdf'")
                
                # Se o PDF é grande o suficiente, provavelmente tem logo
                if len(pdf_response.content) > 8000:
                    print("🎯 PDF parece incluir o logo (tamanho grande)!")
                
                return True
            else:
                print("❌ Resposta não é PDF")
                print("Conteúdo:", pdf_response.text[:200])
                return False
        else:
            print(f"❌ Erro HTTP: {pdf_response.status_code}")
            print("Conteúdo:", pdf_response.text[:200])
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        return False

if __name__ == "__main__":
    sucesso = testar_pdf_inventario()
    
    print("\n" + "=" * 40)
    if sucesso:
        print("🎉 PDF DO INVENTÁRIO FUNCIONANDO!")
        print("📋 Verifique o arquivo 'inventario_teste_final.pdf'")
    else:
        print("❌ PROBLEMAS NO PDF DO INVENTÁRIO")
    print("=" * 40)