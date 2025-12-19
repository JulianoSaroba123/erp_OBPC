#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def adicionar_coluna_filiacao():
    """Adiciona coluna filiação na tabela certificados"""
    
    print("=== ADICIONANDO CAMPO FILIAÇÃO ===\n")
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect('igreja.db')
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(certificados)")
        colunas = cursor.fetchall()
        colunas_nomes = [col[1] for col in colunas]
        
        if 'filiacao' not in colunas_nomes:
            # Adicionar coluna filiação
            cursor.execute("ALTER TABLE certificados ADD COLUMN filiacao TEXT")
            print("✅ Coluna 'filiacao' adicionada com sucesso!")
        else:
            print("ℹ️ Coluna 'filiacao' já existe.")
        
        # Verificar estrutura final
        cursor.execute("PRAGMA table_info(certificados)")
        colunas_final = cursor.fetchall()
        
        print(f"\n📊 Estrutura da tabela 'certificados':")
        for col in colunas_final:
            tipo = col[2]
            nome = col[1]
            print(f"  - {nome}: {tipo}")
        
        conn.commit()
        conn.close()
        
        print(f"\n=== COLUNA FILIAÇÃO ADICIONADA ===")
        
    except Exception as e:
        print(f"❌ Erro ao adicionar coluna: {e}")

if __name__ == "__main__":
    adicionar_coluna_filiacao()