#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples do logo OBPC
"""

import os

def main():
    print("=== VERIFICAÇÃO SIMPLES DO LOGO OBPC ===")
    
    # Verificar logos na pasta correta
    pasta_static = "app/static"
    arquivos_logo = [
        'Logo_OBPC.jpg',
        'logo_obpc_novo.jpg', 
        'logo_obpc.ico'
    ]
    
    print(f"📁 Verificando pasta: {pasta_static}")
    
    for arquivo in arquivos_logo:
        caminho = os.path.join(pasta_static, arquivo)
        existe = os.path.exists(caminho)
        
        if existe:
            tamanho = os.path.getsize(caminho) / 1024
            print(f"✅ {arquivo} - {tamanho:.1f}KB")
        else:
            print(f"❌ {arquivo} - NÃO ENCONTRADO")
    
    print("\n🔧 STATUS:")
    if os.path.exists(os.path.join(pasta_static, 'Logo_OBPC.jpg')):
        print("✅ Logo principal (Logo_OBPC.jpg) está disponível")
        print("✅ O login deve carregar o logo agora")
        print("✅ A sidebar deve mostrar o logo")
        print("✅ Os relatórios PDF devem incluir o logo")
    else:
        print("❌ Logo principal não encontrado")
    
    print(f"\n📋 Para testar:")
    print("1. Inicie o servidor Flask")
    print("2. Acesse a página de login")
    print("3. Verifique se o logo aparece")

if __name__ == "__main__":
    main()