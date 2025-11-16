#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para investigar problemas no inventário
Verifica dados no banco e debug da busca
"""

import sqlite3
import os

def investigar_inventario():
    """Investiga problemas no inventário"""
    
    print("🔍 INVESTIGANDO INVENTÁRIO...")
    print("=" * 50)
    
    # Verificar se o banco existe
    if not os.path.exists('igreja.db'):
        print("❌ Arquivo igreja.db não encontrado!")
        return
    
    # Conectar diretamente ao banco SQLite
    try:
        conn = sqlite3.connect('igreja.db')
        cursor = conn.cursor()
        
        # 1. Verificar se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%inventario%';")
        tabelas = cursor.fetchall()
        print(f"📋 Tabelas de inventário encontradas: {tabelas}")
        
        # 2. Verificar todas as tabelas do banco
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        todas_tabelas = cursor.fetchall()
        print(f"📊 Todas as tabelas no banco: {[t[0] for t in todas_tabelas]}")
        
        # 3. Procurar tabelas que podem conter inventário
        inventario_tables = [t[0] for t in todas_tabelas if 'inventario' in t[0].lower() or 'item' in t[0].lower() or 'patrimonio' in t[0].lower()]
        print(f"🎯 Tabelas relacionadas ao inventário: {inventario_tables}")
        
        # 4. Para cada tabela encontrada, verificar estrutura e dados
        for tabela in inventario_tables:
            print(f"\n📋 ANALISANDO TABELA: {tabela}")
            print("-" * 30)
            
            # Estrutura da tabela
            cursor.execute(f"PRAGMA table_info({tabela});")
            colunas = cursor.fetchall()
            print(f"🏗️ Estrutura: {[col[1] for col in colunas]}")
            
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {tabela};")
            total = cursor.fetchone()[0]
            print(f"📊 Total de registros: {total}")
            
            if total > 0:
                # Mostrar alguns registros
                cursor.execute(f"SELECT * FROM {tabela} LIMIT 5;")
                registros = cursor.fetchall()
                print(f"📄 Primeiros registros:")
                for i, reg in enumerate(registros, 1):
                    print(f"   {i}: {reg}")
                
                # Verificar se existe código 05
                try:
                    cursor.execute(f"SELECT * FROM {tabela} WHERE codigo = '05' OR codigo = 5;")
                    codigo_05 = cursor.fetchall()
                    print(f"🔍 Registros com código 05: {len(codigo_05)}")
                    for reg in codigo_05:
                        print(f"   📌 Código 05: {reg}")
                except sqlite3.OperationalError as e:
                    print(f"   ⚠️ Erro ao buscar código 05: {e}")
                
                # Verificar códigos únicos
                try:
                    cursor.execute(f"SELECT DISTINCT codigo FROM {tabela} ORDER BY codigo;")
                    codigos = cursor.fetchall()
                    print(f"🏷️ Códigos únicos: {[c[0] for c in codigos]}")
                except sqlite3.OperationalError as e:
                    print(f"   ⚠️ Erro ao buscar códigos: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
    
    print("\n" + "=" * 50)
    print("🔍 INVESTIGAÇÃO CONCLUÍDA")

if __name__ == "__main__":
    investigar_inventario()