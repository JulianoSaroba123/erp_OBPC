#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def adicionar_coluna_genero():
    """Adiciona coluna de gênero na tabela certificados"""
    # Usar o mesmo banco que o sistema
    db_path = 'igreja.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Primeiro criar a tabela certificados se não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certificados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_pessoa VARCHAR(200) NOT NULL,
                tipo_certificado VARCHAR(50) NOT NULL,
                data_evento DATE NOT NULL,
                pastor_responsavel VARCHAR(200) NOT NULL,
                local_evento VARCHAR(200),
                observacoes TEXT,
                numero_certificado VARCHAR(50),
                padrinhos TEXT,
                genero VARCHAR(10),
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("✅ Tabela 'certificados' criada/atualizada com campo 'genero'!")
        
        # Commit das alterações
        conn.commit()
        
        # Verificar estrutura
        cursor.execute("PRAGMA table_info(certificados)")
        colunas = cursor.fetchall()
        
        print("\n📊 Estrutura da tabela 'certificados':")
        for coluna in colunas:
            print(f"  - {coluna[1]}: {coluna[2]}")
            
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao atualizar banco: {e}")
    except Exception as e:
        print(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    print("=== ATUALIZANDO TABELA CERTIFICADOS ===\n")
    adicionar_coluna_genero()
    print("\n=== ATUALIZAÇÃO CONCLUÍDA ===")