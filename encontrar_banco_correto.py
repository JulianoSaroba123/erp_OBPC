#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para encontrar e corrigir o banco de dados correto
"""

import sqlite3
import os
import glob

def verificar_banco(caminho_banco):
    """Verifica a estrutura de um banco de dados"""
    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        
        # Verificar se tabela certificados existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='certificados'")
        if not cursor.fetchone():
            conn.close()
            return None
            
        # Verificar estrutura
        cursor.execute("PRAGMA table_info(certificados)")
        colunas = cursor.fetchall()
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM certificados")
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'colunas': [col[1] for col in colunas],
            'total_registros': total
        }
        
    except Exception:
        return None

def main():
    print("🔍 PROCURANDO BANCOS DE DADOS")
    print("=" * 40)
    
    # Procurar todos os arquivos .db
    bancos_encontrados = []
    
    # Procurar na pasta atual
    for arquivo in glob.glob("*.db"):
        info = verificar_banco(arquivo)
        if info:
            bancos_encontrados.append((arquivo, info))
    
    # Procurar na pasta app
    for arquivo in glob.glob("app/*.db"):
        info = verificar_banco(arquivo)
        if info:
            bancos_encontrados.append((arquivo, info))
    
    # Procurar em subpastas
    for arquivo in glob.glob("**/*.db", recursive=True):
        info = verificar_banco(arquivo)
        if info:
            bancos_encontrados.append((arquivo, info))
    
    if not bancos_encontrados:
        print("❌ Nenhum banco com tabela 'certificados' encontrado!")
        return
    
    print(f"📊 Encontrados {len(bancos_encontrados)} bancos com certificados:")
    print()
    
    for caminho, info in bancos_encontrados:
        print(f"📁 {caminho}")
        print(f"   📈 Registros: {info['total_registros']}")
        print(f"   📋 Colunas: {', '.join(info['colunas'])}")
        
        # Verificar se tem filiacao
        tem_filiacao = 'filiacao' in info['colunas']
        print(f"   {'✅' if tem_filiacao else '❌'} Campo filiação: {'SIM' if tem_filiacao else 'NÃO'}")
        print()
    
    # Encontrar o banco com mais registros (provavelmente o correto)
    banco_principal = max(bancos_encontrados, key=lambda x: x[1]['total_registros'])
    caminho_principal = banco_principal[0]
    
    print(f"🎯 Banco principal identificado: {caminho_principal}")
    
    # Se não for o igreja.db, copiar
    if caminho_principal != "igreja.db":
        print(f"🔄 Copiando {caminho_principal} para igreja.db...")
        
        import shutil
        shutil.copy2(caminho_principal, "igreja.db")
        print("✅ Banco copiado!")
    
    # Verificar se o banco principal tem filiacao
    info_principal = banco_principal[1]
    if 'filiacao' not in info_principal['colunas']:
        print("➕ Adicionando coluna filiacao ao banco principal...")
        
        conn = sqlite3.connect("igreja.db")
        cursor = conn.cursor()
        
        try:
            cursor.execute("ALTER TABLE certificados ADD COLUMN filiacao TEXT")
            conn.commit()
            print("✅ Coluna filiacao adicionada!")
        except Exception as e:
            print(f"ℹ️ Coluna já existe ou erro: {str(e)}")
        
        conn.close()
    
    # Teste final
    print("\n🧪 Teste final...")
    info_final = verificar_banco("igreja.db")
    if info_final:
        print(f"✅ igreja.db pronto com {info_final['total_registros']} registros")
        print(f"📋 Colunas: {', '.join(info_final['colunas'])}")
        
        if 'filiacao' in info_final['colunas']:
            print("✅ Campo filiação presente!")
        else:
            print("❌ Campo filiação ainda não está presente")
    
    print("\n🚀 Agora reinicie o sistema Flask!")

if __name__ == "__main__":
    main()