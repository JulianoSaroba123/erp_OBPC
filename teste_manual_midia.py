#!/usr/bin/env python3
"""
Script simples para testar login e mídia localmente
"""

import subprocess
import sys
import time
import os

def verificar_servidor():
    """Verifica se o servidor está rodando"""
    try:
        import urllib.request
        urllib.request.urlopen('http://localhost:5000', timeout=3)
        return True
    except:
        return False

def main():
    print("=" * 60)
    print("🎯 TESTE RÁPIDO - OBPC MÍDIA")
    print("=" * 60)
    
    # 1. Verificar servidor
    print("1. Verificando servidor...")
    if verificar_servidor():
        print("✅ Servidor está rodando em http://localhost:5000")
    else:
        print("❌ Servidor não está rodando")
        print("Execute: python run.py")
        return
    
    # 2. Instruções para teste manual
    print("\n2. 📋 INSTRUÇÕES PARA TESTE MANUAL:")
    print("-" * 40)
    print("👤 CREDENCIAIS DE LOGIN:")
    print("   Email: admin@obpc.com")
    print("   Senha: 123456")
    print("   ✓ Marque a opção 'Lembrar de mim'")
    
    print("\n🔗 LINKS PARA TESTAR:")
    print("   • Login: http://localhost:5000/usuario/login")
    print("   • Agenda: http://localhost:5000/midia/agenda")
    print("   • Certificados: http://localhost:5000/midia/certificados")
    print("   • Carteirinhas: http://localhost:5000/midia/carteirinhas")
    
    print("\n✅ RESULTADO ESPERADO:")
    print("   1. Fazer login com sucesso")
    print("   2. Acessar /midia/agenda SEM ser redirecionado para login")
    print("   3. Ver a página da agenda da mídia")
    
    print("\n❌ SE DER PROBLEMA:")
    print("   - Ainda redireciona para login = Problema de sessão")
    print("   - Erro 404 = Problema de rota")
    print("   - Erro 500 = Problema no código")
    
    print("\n🔧 MELHORIAS IMPLEMENTADAS:")
    print("   • Sessão persiste por 24 horas")
    print("   • Checkbox 'Lembrar de mim' (7 dias)")
    print("   • Cookies seguros configurados")
    print("   • Rotas da mídia corrigidas")
    
    print("\n" + "=" * 60)
    print("🌐 Abra seu navegador em: http://localhost:5000")
    print("=" * 60)

if __name__ == "__main__":
    main()