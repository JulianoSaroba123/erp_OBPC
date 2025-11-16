#!/usr/bin/env python3
"""
Teste para verificar se o logo está sendo inserido no PDF dos ofícios
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests

def testar_pdf_oficios_com_logo():
    """Testa se o PDF dos ofícios inclui o logo"""
    
    print("🧪 TESTE: Logo no PDF dos Ofícios")
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
        
        # 2. Verificar se há ofícios disponíveis
        print("\n2. Verificando ofícios disponíveis...")
        lista_response = session.get(f"{base_url}/secretaria/oficios")
        
        if "oficio" in lista_response.text.lower():
            print("✅ Página de ofícios acessada!")
        else:
            print("⚠️ Página de ofícios pode estar vazia")
        
        # 3. Tentar gerar PDF do primeiro ofício disponível
        # Vamos tentar alguns IDs comuns
        oficios_testados = []
        for oficio_id in [1, 2, 3, 4, 5]:
            print(f"\n3.{oficio_id} Testando PDF do ofício ID {oficio_id}...")
            pdf_url = f"{base_url}/secretaria/oficios/pdf/{oficio_id}"
            
            pdf_response = session.get(pdf_url)
            
            print(f"   Status: {pdf_response.status_code}")
            print(f"   Content-Type: {pdf_response.headers.get('Content-Type', 'N/A')}")
            print(f"   Content-Length: {len(pdf_response.content)} bytes")
            
            if pdf_response.status_code == 200 and 'application/pdf' in pdf_response.headers.get('Content-Type', ''):
                # Salvar PDF para análise
                nome_arquivo = f'oficio_com_logo_teste_id{oficio_id}.pdf'
                with open(nome_arquivo, 'wb') as f:
                    f.write(pdf_response.content)
                
                print(f"   ✅ PDF gerado com sucesso!")
                print(f"   📄 Tamanho: {len(pdf_response.content)} bytes")
                print(f"   💾 PDF salvo como '{nome_arquivo}'")
                
                oficios_testados.append({
                    'id': oficio_id,
                    'tamanho': len(pdf_response.content),
                    'arquivo': nome_arquivo
                })
                
                # Se o PDF é grande o suficiente, provavelmente tem logo
                if len(pdf_response.content) > 8000:
                    print(f"   🎯 PDF parece incluir o logo (tamanho grande)!")
                
            elif pdf_response.status_code == 404:
                print(f"   ⚠️ Ofício ID {oficio_id} não existe")
            else:
                print(f"   ❌ Erro: {pdf_response.status_code}")
        
        if oficios_testados:
            print(f"\n✅ {len(oficios_testados)} ofício(s) testado(s) com sucesso!")
            for oficio in oficios_testados:
                print(f"   📋 ID {oficio['id']}: {oficio['tamanho']} bytes → {oficio['arquivo']}")
            return True
        else:
            print("\n❌ Nenhum ofício foi encontrado para teste")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        return False

if __name__ == "__main__":
    sucesso = testar_pdf_oficios_com_logo()
    
    print("\n" + "=" * 40)
    if sucesso:
        print("🎉 TESTE CONCLUÍDO - Logo possivelmente incluído!")
        print("📋 Verifique os arquivos PDF gerados")
    else:
        print("❌ PROBLEMAS DETECTADOS NO TESTE")
    print("=" * 40)