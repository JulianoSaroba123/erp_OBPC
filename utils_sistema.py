#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitários do Sistema OBPC
Funções auxiliares para verificações e configurações do sistema
"""

import os
import sys
import socket
import subprocess

def verificar_dependencias():
    """Verifica se as dependências Python estão instaladas"""
    dependencias_obrigatorias = [
        'flask',
        'flask_sqlalchemy', 
        'flask_login',
        'flask_migrate',
        'werkzeug',
        'jinja2'
    ]
    
    dependencias_opcionais = [
        'requests',
        'reportlab',
        'pillow'
    ]
    
    print("🔍 Verificando dependências obrigatórias...")
    
    for dep in dependencias_obrigatorias:
        try:
            __import__(dep)
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep} - OBRIGATÓRIO")
            print(f"\n💡 Para instalar as dependências, execute:")
            print(f"   pip install {dep}")
            print(f"\nOu execute: InstalarOBPC.bat")
            raise SystemExit(1)
    
    print("🔍 Verificando dependências opcionais...")
    for dep in dependencias_opcionais:
        try:
            __import__(dep)
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ⚠️  {dep} - OPCIONAL (pode afetar algumas funcionalidades)")
    
    return True

def verificar_banco():
    """Verifica se o banco de dados existe e está acessível"""
    caminhos_banco = [
        'instance/igreja.db',
        'igreja.db',
        'app/instance/igreja.db'
    ]
    
    for caminho in caminhos_banco:
        if os.path.exists(caminho):
            # Verificar se o arquivo não está corrompido
            try:
                import sqlite3
                conn = sqlite3.connect(caminho)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tabelas = cursor.fetchall()
                conn.close()
                
                if len(tabelas) > 0:
                    print(f"✅ Banco de dados encontrado: {caminho}")
                    print(f"   Tabelas encontradas: {len(tabelas)}")
                    return True
                else:
                    print(f"⚠️  Banco encontrado mas sem tabelas: {caminho}")
                    
            except Exception as e:
                print(f"❌ Erro ao verificar banco {caminho}: {e}")
                continue
    
    print("❌ Banco de dados não encontrado ou inacessível!")
    return False

def porta_disponivel(porta=5000):
    """Verifica se uma porta está disponível"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            resultado = s.connect_ex(('127.0.0.1', porta))
            return resultado != 0  # Retorna True se a porta estiver livre
    except Exception:
        return False

def encontrar_porta_livre(porta_inicial=5000, porta_final=5010):
    """Encontra a primeira porta livre em um intervalo"""
    for porta in range(porta_inicial, porta_final + 1):
        if porta_disponivel(porta):
            return porta
    return None

def verificar_python():
    """Verifica a versão do Python"""
    versao = sys.version_info
    if versao.major < 3 or (versao.major == 3 and versao.minor < 7):
        print(f"❌ Python {versao.major}.{versao.minor} detectado")
        print("💡 O sistema requer Python 3.7 ou superior")
        return False
    
    print(f"✅ Python {versao.major}.{versao.minor}.{versao.micro}")
    return True

def verificar_arquivo_principal():
    """Verifica se o arquivo principal run.py existe"""
    if not os.path.exists('run.py'):
        print("❌ Arquivo run.py não encontrado!")
        print("💡 Certifique-se de estar na pasta correta do sistema")
        return False
    
    print("✅ Arquivo run.py encontrado")
    return True

def verificar_estrutura_projeto():
    """Verifica se a estrutura básica do projeto existe"""
    diretorios_obrigatorios = [
        'app',
        'app/templates',
        'app/static'
    ]
    
    arquivos_obrigatorios = [
        'run.py',
        'requirements.txt'
    ]
    
    # Verificar diretórios
    for diretorio in diretorios_obrigatorios:
        if not os.path.exists(diretorio):
            print(f"❌ Diretório obrigatório não encontrado: {diretorio}")
            return False
    
    # Verificar arquivos
    for arquivo in arquivos_obrigatorios:
        if not os.path.exists(arquivo):
            print(f"❌ Arquivo obrigatório não encontrado: {arquivo}")
            return False
    
    print("✅ Estrutura do projeto OK")
    return True

def executar_verificacao_completa():
    """Executa todas as verificações do sistema"""
    print("🔍 VERIFICAÇÃO COMPLETA DO SISTEMA OBPC")
    print("=" * 50)
    
    verificacoes = [
        ("Python", verificar_python),
        ("Estrutura do Projeto", verificar_estrutura_projeto),
        ("Arquivo Principal", verificar_arquivo_principal),
        ("Dependências", verificar_dependencias),
        ("Banco de Dados", verificar_banco)
    ]
    
    resultados = []
    
    for nome, funcao in verificacoes:
        print(f"\n📋 Verificando: {nome}")
        try:
            resultado = funcao()
            resultados.append((nome, resultado))
        except Exception as e:
            print(f"❌ Erro na verificação de {nome}: {e}")
            resultados.append((nome, False))
    
    # Resumo final
    print("\n" + "=" * 50)
    print("📊 RESUMO DAS VERIFICAÇÕES:")
    print("=" * 50)
    
    total_verificacoes = len(resultados)
    verificacoes_ok = sum(1 for _, ok in resultados if ok)
    
    for nome, ok in resultados:
        status = "✅ OK" if ok else "❌ FALHOU"
        print(f"  {nome}: {status}")
    
    print(f"\n📈 Resultado: {verificacoes_ok}/{total_verificacoes} verificações passaram")
    
    if verificacoes_ok == total_verificacoes:
        print("🎉 Sistema pronto para execução!")
        return True
    else:
        print("⚠️  Sistema com problemas. Corrija os erros antes de prosseguir.")
        return False

# Teste das verificações
if __name__ == '__main__':
    executar_verificacao_completa()
