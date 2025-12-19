#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def verificar_bancos():
    """Verifica todos os bancos e suas tabelas"""
    
    print("🔍 VERIFICANDO BANCOS DE DADOS")
    print("=" * 50)
    
    bancos = ['igreja.db', 'instance/database.db', 'database.db']
    
    for banco in bancos:
        print(f"\n📁 Verificando: {banco}")
        
        if not os.path.exists(banco):
            print(f"   ❌ Não existe")
            continue
            
        try:
            conn = sqlite3.connect(banco)
            cursor = conn.cursor()
            
            # Listar tabelas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tabelas = cursor.fetchall()
            
            print(f"   ✅ Encontrado ({os.path.getsize(banco)} bytes)")
            print(f"   📋 Tabelas ({len(tabelas)}):")
            
            for tabela in tabelas:
                cursor.execute(f"SELECT COUNT(*) FROM {tabela[0]};")
                count = cursor.fetchone()[0]
                print(f"      - {tabela[0]}: {count} registros")
                
                # Verificar se é a tabela certificados
                if tabela[0] == 'certificados':
                    cursor.execute(f"PRAGMA table_info({tabela[0]});")
                    colunas = cursor.fetchall()
                    print(f"        Colunas: {', '.join([col[1] for col in colunas])}")
            
            conn.close()
            
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")

if __name__ == "__main__":
    verificar_bancos()