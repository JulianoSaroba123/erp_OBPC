#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar funcionalidades de busca automática por CNPJ e CEP
Sistema OBPC - Igreja O Brasil para Cristo - Tietê/SP
"""

import requests
import re

def testar_busca_cnpj():
    """Testa a busca por CNPJ usando a API ReceitaWS"""
    print("🔍 Testando busca por CNPJ...")
    
    # CNPJ de teste (pode usar qualquer CNPJ válido público)
    cnpj_teste = "11222333000181"  # CNPJ de exemplo
    
    try:
        url = f'https://www.receitaws.com.br/v1/cnpj/{cnpj_teste}'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            
            if dados.get('status') == 'ERROR':
                print(f"❌ Erro na consulta: {dados.get('message')}")
                return False
            
            print(f"✅ CNPJ encontrado!")
            print(f"   Nome: {dados.get('nome', 'N/A')}")
            print(f"   CNPJ: {dados.get('cnpj', 'N/A')}")
            print(f"   Endereço: {dados.get('logradouro', 'N/A')}")
            print(f"   Bairro: {dados.get('bairro', 'N/A')}")
            print(f"   Cidade: {dados.get('municipio', 'N/A')}")
            print(f"   CEP: {dados.get('cep', 'N/A')}")
            print(f"   Situação: {dados.get('situacao', 'N/A')}")
            return True
            
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout na consulta do CNPJ")
        return False
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

def testar_busca_cep():
    """Testa a busca por CEP usando a API ViaCEP"""
    print("\n🔍 Testando busca por CEP...")
    
    # CEP de teste (Centro de São Paulo)
    cep_teste = "01310200"  # CEP válido da Av. Paulista, São Paulo-SP
    
    try:
        url = f'https://viacep.com.br/ws/{cep_teste}/json/'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            
            if dados.get('erro'):
                print("❌ CEP não encontrado")
                return False
            
            print(f"✅ CEP encontrado!")
            print(f"   CEP: {dados.get('cep', 'N/A')}")
            print(f"   Logradouro: {dados.get('logradouro', 'N/A')}")
            print(f"   Bairro: {dados.get('bairro', 'N/A')}")
            print(f"   Cidade: {dados.get('localidade', 'N/A')}")
            print(f"   UF: {dados.get('uf', 'N/A')}")
            return True
            
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout na consulta do CEP")
        return False
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

def testar_formatacao():
    """Testa as funções de formatação"""
    print("\n🔧 Testando formatação...")
    
    # Teste formatação CNPJ
    cnpj_numero = "11222333000181"
    cnpj_formatado = re.sub(r'(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})', r'\1.\2.\3/\4-\5', cnpj_numero)
    print(f"   CNPJ: {cnpj_numero} → {cnpj_formatado}")
    
    # Teste formatação CEP
    cep_numero = "18530000"
    cep_formatado = re.sub(r'(\d{5})(\d{3})', r'\1-\2', cep_numero)
    print(f"   CEP: {cep_numero} → {cep_formatado}")
    
    return True

def main():
    """Função principal de teste"""
    print("🧪 TESTE DAS FUNCIONALIDADES DE BUSCA AUTOMÁTICA")
    print("=" * 55)
    
    # Testar conexão com APIs
    print("\n📡 Testando conectividade com APIs externas...")
    
    # Teste CNPJ
    sucesso_cnpj = testar_busca_cnpj()
    
    # Teste CEP
    sucesso_cep = testar_busca_cep()
    
    # Teste formatação
    sucesso_formatacao = testar_formatacao()
    
    # Relatório final
    print("\n" + "=" * 55)
    print("📊 RELATÓRIO FINAL")
    print("=" * 55)
    print(f"🏢 Busca por CNPJ: {'✅ OK' if sucesso_cnpj else '❌ FALHOU'}")
    print(f"📍 Busca por CEP: {'✅ OK' if sucesso_cep else '❌ FALHOU'}")
    print(f"🔧 Formatação: {'✅ OK' if sucesso_formatacao else '❌ FALHOU'}")
    
    if sucesso_cnpj and sucesso_cep and sucesso_formatacao:
        print("\n🎉 Todos os testes passaram! As funcionalidades estão prontas.")
        print("💡 Agora você pode usar as funcionalidades no módulo de configurações:")
        print("   1. Acesse /configuracoes")
        print("   2. Na aba 'Gerais', digite um CNPJ e clique no botão de busca")
        print("   3. Digite um CEP e clique no botão de busca")
        print("   4. Os dados serão preenchidos automaticamente!")
    else:
        print("\n⚠️  Alguns testes falharam. Verifique a conectividade com a internet.")
    
    print("\n" + "=" * 55)

if __name__ == '__main__':
    main()