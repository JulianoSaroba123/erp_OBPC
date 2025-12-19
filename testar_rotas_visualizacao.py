#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import sys

def testar_rotas_certificados():
    """Testa as rotas dos certificados"""
    base_url = "http://127.0.0.1:5000"
    
    print("=== TESTANDO ROTAS DOS CERTIFICADOS ===\n")
    
    # Teste 1: Lista de certificados
    try:
        response = requests.get(f"{base_url}/midia/certificados")
        print(f"✅ Lista de certificados: {response.status_code}")
        if response.status_code == 200:
            print("   - Página carregou corretamente")
        else:
            print(f"   - Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao acessar lista: {e}")
    
    # Teste 2: Formulário de novo certificado
    try:
        response = requests.get(f"{base_url}/midia/certificados/novo")
        print(f"✅ Novo certificado: {response.status_code}")
        if response.status_code == 200:
            print("   - Formulário carregou corretamente")
        else:
            print(f"   - Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao acessar formulário: {e}")
    
    # Teste 3: Verificar se existem certificados para testar visualização
    print(f"\n=== INSTRUÇÕES PARA TESTE MANUAL ===")
    print(f"1. Acesse: {base_url}/midia/certificados/novo")
    print(f"2. Crie um certificado de teste")
    print(f"3. Na lista, clique no botão 'Visualizar' (ícone de olho)")
    print(f"4. Verifique se mostra o template do certificado (não a lista)")
    print(f"5. Teste também o botão PDF para ver a logo maior")
    
    print(f"\n=== RESULTADO ESPERADO ===")
    print(f"- Visualizar: deve mostrar o certificado em tela com logo grande")
    print(f"- PDF: deve gerar PDF com logo bem maior que antes")
    print(f"- Nome da igreja removido para dar espaço à logo")

if __name__ == "__main__":
    testar_rotas_certificados()