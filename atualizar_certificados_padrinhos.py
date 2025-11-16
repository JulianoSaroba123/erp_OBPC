#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def atualizar_certificados_padrinhos():
    """Adiciona coluna padrinhos na tabela certificados"""
    
    print("🔄 ATUALIZANDO ESTRUTURA DE CERTIFICADOS - PADRINHOS")
    print("=" * 60)
    
    # Caminhos possíveis do banco
    caminhos_banco = [
        os.path.join('instance', 'database.db'),
        'igreja.db',
        'database.db'
    ]
    
    db_path = None
    for caminho in caminhos_banco:
        if os.path.exists(caminho):
            db_path = caminho
            break
    
    if not db_path:
        print(f"❌ Banco de dados não encontrado em nenhum dos caminhos: {caminhos_banco}")
        return
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a tabela certificados existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='certificados';")
        tabela_existe = cursor.fetchone()
        
        if not tabela_existe:
            print("❌ Tabela 'certificados' não existe!")
            conn.close()
            return
        
        print("✅ Tabela 'certificados' encontrada")
        
        # Verificar se a coluna padrinhos já existe
        cursor.execute("PRAGMA table_info(certificados);")
        colunas = cursor.fetchall()
        colunas_nomes = [col[1] for col in colunas]
        
        print(f"📋 Colunas atuais: {', '.join(colunas_nomes)}")
        
        if 'padrinhos' in colunas_nomes:
            print("✅ Coluna 'padrinhos' já existe!")
        else:
            print("🔄 Adicionando coluna 'padrinhos'...")
            
            # Adicionar a coluna padrinhos
            cursor.execute("ALTER TABLE certificados ADD COLUMN padrinhos TEXT;")
            print("✅ Coluna 'padrinhos' adicionada com sucesso!")
        
        # Verificar estrutura final
        cursor.execute("PRAGMA table_info(certificados);")
        colunas_final = cursor.fetchall()
        
        print(f"\n📊 ESTRUTURA FINAL da tabela certificados:")
        for col in colunas_final:
            print(f"  - {col[1]} ({col[2]})")
        
        # Verificar certificados existentes
        cursor.execute("SELECT COUNT(*) FROM certificados;")
        total_certificados = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM certificados WHERE tipo_certificado = 'Apresentação';")
        total_apresentacoes = cursor.fetchone()[0]
        
        print(f"\n📈 CERTIFICADOS EXISTENTES:")
        print(f"  Total: {total_certificados}")
        print(f"  Apresentações: {total_apresentacoes}")
        
        # Commit das alterações
        conn.commit()
        conn.close()
        
        print(f"\n🎉 ATUALIZAÇÃO CONCLUÍDA!")
        print(f"✅ Agora você pode adicionar padrinhos nos certificados de apresentação!")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    atualizar_certificados_padrinhos()