#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
from datetime import datetime

def verificar_banco_direto():
    """Verifica dados financeiros diretamente no banco SQLite"""
    
    # Caminho do banco
    db_path = os.path.join('instance', 'database.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado em: {db_path}")
        return
    
    print(f"✅ Banco encontrado em: {db_path}")
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a tabela lancamentos existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lancamentos';")
        tabela_existe = cursor.fetchone()
        
        if not tabela_existe:
            print("❌ Tabela 'lancamentos' não existe!")
            return
        
        print("✅ Tabela 'lancamentos' existe")
        
        # Verificar estrutura da tabela
        cursor.execute("PRAGMA table_info(lancamentos);")
        colunas = cursor.fetchall()
        
        print(f"\n📋 Estrutura da tabela lancamentos ({len(colunas)} colunas):")
        for col in colunas:
            print(f"  - {col[1]} ({col[2]})")
        
        # Contar total de registros
        cursor.execute("SELECT COUNT(*) FROM lancamentos;")
        total = cursor.fetchone()[0]
        
        print(f"\n📊 Total de lançamentos: {total}")
        
        if total > 0:
            # Mostrar alguns exemplos
            cursor.execute("SELECT id, data, descricao, valor, tipo FROM lancamentos LIMIT 5;")
            exemplos = cursor.fetchall()
            
            print("\n📝 Primeiros 5 lançamentos:")
            for exemplo in exemplos:
                print(f"  ID: {exemplo[0]} | Data: {exemplo[1]} | Desc: {exemplo[2][:30]}... | Valor: R$ {exemplo[3]} | Tipo: {exemplo[4]}")
            
            # Verificar distribuição por tipo
            cursor.execute("SELECT tipo, COUNT(*) FROM lancamentos GROUP BY tipo;")
            tipos = cursor.fetchall()
            
            print("\n📈 Distribuição por tipo:")
            for tipo in tipos:
                print(f"  {tipo[0]}: {tipo[1]} lançamentos")
        else:
            print("\n⚠️  Nenhum lançamento encontrado na tabela!")
            print("\nVerificando outras tabelas financeiras...")
            
            # Verificar outras tabelas
            for tabela in ['importacao_extrato', 'conciliacao_historico', 'conciliacao_pares']:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabela}';")
                if cursor.fetchone():
                    cursor.execute(f"SELECT COUNT(*) FROM {tabela};")
                    count = cursor.fetchone()[0]
                    print(f"  {tabela}: {count} registros")
                else:
                    print(f"  {tabela}: não existe")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao acessar banco: {str(e)}")

if __name__ == "__main__":
    print("🔍 Verificação Direta do Banco de Dados Financeiro")
    print("=" * 50)
    verificar_banco_direto()