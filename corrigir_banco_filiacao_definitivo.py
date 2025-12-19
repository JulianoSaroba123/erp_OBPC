#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir definitivamente o banco de dados 
mantendo o campo filiação e resolvendo conflitos SQLAlchemy
"""

import sqlite3
import os
import sys
from datetime import datetime

def main():
    print("🔧 CORREÇÃO DEFINITIVA DO BANCO DE DADOS")
    print("=" * 50)
    
    banco_path = "igreja.db"
    
    if not os.path.exists(banco_path):
        print(f"❌ Banco de dados não encontrado: {banco_path}")
        return
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(banco_path)
        cursor = conn.cursor()
        
        print("📊 Verificando estrutura atual...")
        
        # Verificar se a tabela certificados existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='certificados'")
        tabela_existe = cursor.fetchone()
        
        if not tabela_existe:
            print("❌ Tabela 'certificados' não encontrada!")
            return
        
        # Verificar estrutura atual
        cursor.execute("PRAGMA table_info(certificados)")
        colunas_atuais = cursor.fetchall()
        
        print("📋 Colunas atuais:")
        colunas_nomes = []
        for col in colunas_atuais:
            print(f"  - {col[1]}: {col[2]}")
            colunas_nomes.append(col[1])
        
        # Verificar se filiacao existe
        tem_filiacao = 'filiacao' in colunas_nomes
        
        if not tem_filiacao:
            print("\n➕ Adicionando coluna 'filiacao'...")
            cursor.execute("ALTER TABLE certificados ADD COLUMN filiacao TEXT")
            print("✅ Coluna 'filiacao' adicionada!")
        else:
            print("\n✅ Coluna 'filiacao' já existe!")
        
        # Verificar se genero existe
        tem_genero = 'genero' in colunas_nomes
        
        if not tem_genero:
            print("➕ Adicionando coluna 'genero'...")
            cursor.execute("ALTER TABLE certificados ADD COLUMN genero VARCHAR(10)")
            print("✅ Coluna 'genero' adicionada!")
        else:
            print("✅ Coluna 'genero' já existe!")
        
        # Verificar se padrinhos existe
        tem_padrinhos = 'padrinhos' in colunas_nomes
        
        if not tem_padrinhos:
            print("➕ Adicionando coluna 'padrinhos'...")
            cursor.execute("ALTER TABLE certificados ADD COLUMN padrinhos TEXT")
            print("✅ Coluna 'padrinhos' adicionada!")
        else:
            print("✅ Coluna 'padrinhos' já existe!")
        
        # Confirmar mudanças
        conn.commit()
        
        # Verificar estrutura final
        print("\n📊 Estrutura final da tabela:")
        cursor.execute("PRAGMA table_info(certificados)")
        colunas_finais = cursor.fetchall()
        
        for col in colunas_finais:
            print(f"  - {col[1]}: {col[2]}")
        
        # Testar uma consulta simples
        print("\n🧪 Testando consulta...")
        cursor.execute("SELECT COUNT(*) FROM certificados")
        total = cursor.fetchone()[0]
        print(f"📈 Total de certificados: {total}")
        
        # Se houver certificados, mostrar alguns campos
        if total > 0:
            cursor.execute("""
                SELECT id, nome_pessoa, tipo_certificado, filiacao, padrinhos 
                FROM certificados 
                LIMIT 3
            """)
            exemplos = cursor.fetchall()
            
            print("\n📝 Exemplos de registros:")
            for exemplo in exemplos:
                print(f"  ID: {exemplo[0]} | Nome: {exemplo[1]} | Tipo: {exemplo[2]}")
                if exemplo[3]:
                    print(f"    Filiação: {exemplo[3]}")
                if exemplo[4]:
                    print(f"    Padrinhos: {exemplo[4]}")
        
        conn.close()
        
        print(f"\n✅ Banco de dados corrigido com sucesso!")
        print("🎯 Agora o campo filiação deve funcionar perfeitamente!")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    sucesso = main()
    if sucesso:
        print("\n🚀 Execute o sistema novamente - os certificados devem aparecer!")
    else:
        print("\n💥 Falha na correção - verifique os erros acima")