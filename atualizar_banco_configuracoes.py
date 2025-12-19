#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para atualizar estrutura do banco de dados
Sistema OBPC - Igreja O Brasil para Cristo - Tietê/SP

Adiciona campos faltantes nas tabelas existentes
"""

import sqlite3
import os
from app import create_app
from app.extensoes import db

def verificar_e_adicionar_coluna_cep():
    """Verifica e adiciona a coluna CEP na tabela configuracoes se não existir"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Verificando estrutura da tabela configuracoes...")
        
        try:
            # Conectar diretamente ao banco SQLite
            db_path = os.path.join(app.instance_path, 'igreja.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar se a coluna CEP existe
            cursor.execute("PRAGMA table_info(configuracoes)")
            colunas = [info[1] for info in cursor.fetchall()]
            
            print(f"📋 Colunas existentes: {colunas}")
            
            if 'cep' not in colunas:
                print("➕ Adicionando coluna CEP...")
                cursor.execute("ALTER TABLE configuracoes ADD COLUMN cep VARCHAR(9)")
                conn.commit()
                print("✅ Coluna CEP adicionada com sucesso!")
            else:
                print("✅ Coluna CEP já existe!")
            
            # Verificar novamente
            cursor.execute("PRAGMA table_info(configuracoes)")
            colunas_atuais = [info[1] for info in cursor.fetchall()]
            print(f"📋 Colunas após atualização: {colunas_atuais}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Erro ao atualizar banco: {str(e)}")
            return False
    
    return True

def verificar_outras_tabelas():
    """Verifica se todas as tabelas necessárias existem"""
    app = create_app()
    
    with app.app_context():
        print("\n🔍 Verificando todas as tabelas...")
        
        try:
            # Conectar diretamente ao banco SQLite
            db_path = os.path.join(app.instance_path, 'igreja.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Listar todas as tabelas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tabelas = [row[0] for row in cursor.fetchall()]
            
            print(f"📋 Tabelas existentes: {tabelas}")
            
            # Tabelas esperadas
            tabelas_esperadas = [
                'usuarios', 'membros', 'obreiros', 'departamentos', 
                'lancamentos', 'eventos', 'configuracoes'
            ]
            
            for tabela in tabelas_esperadas:
                if tabela in tabelas:
                    print(f"✅ Tabela '{tabela}' existe")
                else:
                    print(f"❌ Tabela '{tabela}' não encontrada")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Erro ao verificar tabelas: {str(e)}")
            return False
    
    return True

def main():
    """Função principal"""
    print("🔧 ATUALIZAÇÃO DO BANCO DE DADOS")
    print("=" * 40)
    
    # Verificar e adicionar coluna CEP
    if verificar_e_adicionar_coluna_cep():
        print("✅ Estrutura da tabela configuracoes atualizada!")
    else:
        print("❌ Falha ao atualizar estrutura!")
        return
    
    # Verificar outras tabelas
    verificar_outras_tabelas()
    
    print("\n" + "=" * 40)
    print("🎉 Atualização do banco concluída!")
    print("💡 Agora você pode acessar /configuracoes sem erros")

if __name__ == '__main__':
    main()