#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste de Acesso ao Inventário
============================
Testa se a página do inventário está funcionando sem erro.
"""

import requests
import sys

def testar_inventario():
    """Testa acesso à página do inventário"""
    try:
        print("🧪 TESTE: Página do Inventário")
        print("=" * 40)
        
        # Fazer login primeiro
        print("1. Fazendo login...")
        session = requests.Session()
        
        # Fazer login
        login_data = {
            'email': 'admin@obpc.com',
            'password': 'admin123'
        }
        
        login_response = session.post('http://127.0.0.1:5000/login', data=login_data)
        
        if login_response.status_code == 200:
            print("✅ Login realizado com sucesso")
            
            # Testar página do inventário
            print("2. Testando página do inventário...")
            inventario_response = session.get('http://127.0.0.1:5000/secretaria/inventario')
            
            if inventario_response.status_code == 200:
                print("✅ Página do inventário carregada com sucesso!")
                print(f"📊 Status: {inventario_response.status_code}")
                print(f"📄 Tamanho da resposta: {len(inventario_response.content)} bytes")
                
                # Verificar se tem conteúdo esperado
                if 'Inventário Patrimonial' in inventario_response.text:
                    print("✅ Conteúdo da página encontrado")
                    
                if 'valor_total' in inventario_response.text or 'R$' in inventario_response.text:
                    print("✅ Valor total sendo exibido")
                    
                return True
            else:
                print(f"❌ Erro ao carregar inventário: {inventario_response.status_code}")
                return False
        else:
            print(f"❌ Erro no login: {login_response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao servidor Flask")
        print("   Verifique se o servidor está rodando em http://127.0.0.1:5000")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    sucesso = testar_inventario()
    if sucesso:
        print("\n" + "=" * 40)
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 40)
    else:
        print("\n" + "=" * 40)
        print("❌ TESTE FALHOU")
        print("=" * 40)
        sys.exit(1)