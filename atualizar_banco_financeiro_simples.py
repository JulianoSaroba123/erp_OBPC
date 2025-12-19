#!/usr/bin/env python3
"""
Script simplificado para atualizar o banco de dados financeiro
"""

import sqlite3
import os
from datetime import datetime

def atualizar_banco_financeiro():
    """Atualiza estrutura do banco para o módulo financeiro"""
    
    print("=== ATUALIZANDO BANCO DE DADOS FINANCEIRO ===")
    print()
    
    # Conectar ao banco SQLite
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"✅ Conectado ao banco: {db_path}")
        
        # 1. Verificar e adicionar coluna comprovante na tabela lancamentos
        print("\n🔄 VERIFICANDO COLUNA 'comprovante' NA TABELA 'lancamentos'...")
        
        cursor.execute("PRAGMA table_info(lancamentos)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'comprovante' not in columns:
            print("   ➕ Adicionando coluna 'comprovante'...")
            cursor.execute("ALTER TABLE lancamentos ADD COLUMN comprovante VARCHAR(300)")
            print("   ✅ Coluna 'comprovante' adicionada!")
        else:
            print("   ✅ Coluna 'comprovante' já existe!")
        
        # 2. Verificar e adicionar colunas de conciliação
        colunas_conciliacao = [
            ('hash_duplicata', 'VARCHAR(64)'),
            ('banco_origem', 'VARCHAR(100)'),
            ('documento_ref', 'VARCHAR(50)'),
            ('conciliado_em', 'DATETIME'),
            ('conciliado_por', 'VARCHAR(100)'),
            ('par_conciliacao_id', 'INTEGER')
        ]
        
        print("\n🔄 VERIFICANDO COLUNAS DE CONCILIAÇÃO...")
        for col_name, col_type in colunas_conciliacao:
            if col_name not in columns:
                print(f"   ➕ Adicionando coluna '{col_name}'...")
                cursor.execute(f"ALTER TABLE lancamentos ADD COLUMN {col_name} {col_type}")
                print(f"   ✅ Coluna '{col_name}' adicionada!")
            else:
                print(f"   ✅ Coluna '{col_name}' já existe!")
        
        # 3. Criar tabela conciliacao_historico
        print("\n🔄 VERIFICANDO TABELA 'conciliacao_historico'...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conciliacao_historico'")
        if not cursor.fetchone():
            print("   ➕ Criando tabela 'conciliacao_historico'...")
            cursor.execute("""
                CREATE TABLE conciliacao_historico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_conciliacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    usuario VARCHAR(100) NOT NULL,
                    total_conciliados INTEGER NOT NULL DEFAULT 0,
                    total_pendentes INTEGER NOT NULL DEFAULT 0,
                    tipo_conciliacao VARCHAR(20) DEFAULT 'manual',
                    observacao TEXT,
                    tempo_execucao REAL,
                    regras_aplicadas TEXT
                )
            """)
            print("   ✅ Tabela 'conciliacao_historico' criada!")
        else:
            print("   ✅ Tabela 'conciliacao_historico' já existe!")
        
        # 4. Criar tabela conciliacao_pares
        print("\n🔄 VERIFICANDO TABELA 'conciliacao_pares'...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conciliacao_pares'")
        if not cursor.fetchone():
            print("   ➕ Criando tabela 'conciliacao_pares'...")
            cursor.execute("""
                CREATE TABLE conciliacao_pares (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    historico_id INTEGER,
                    lancamento_manual_id INTEGER NOT NULL,
                    lancamento_importado_id INTEGER NOT NULL,
                    score_similaridade REAL,
                    regra_aplicada VARCHAR(200),
                    metodo_conciliacao VARCHAR(50) DEFAULT 'manual',
                    usuario VARCHAR(100),
                    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ativo BOOLEAN DEFAULT 1,
                    FOREIGN KEY (historico_id) REFERENCES conciliacao_historico (id),
                    FOREIGN KEY (lancamento_manual_id) REFERENCES lancamentos (id),
                    FOREIGN KEY (lancamento_importado_id) REFERENCES lancamentos (id)
                )
            """)
            print("   ✅ Tabela 'conciliacao_pares' criada!")
        else:
            print("   ✅ Tabela 'conciliacao_pares' já existe!")
        
        # 5. Criar tabela importacao_extrato
        print("\n🔄 VERIFICANDO TABELA 'importacao_extrato'...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='importacao_extrato'")
        if not cursor.fetchone():
            print("   ➕ Criando tabela 'importacao_extrato'...")
            cursor.execute("""
                CREATE TABLE importacao_extrato (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_arquivo VARCHAR(255) NOT NULL,
                    hash_arquivo VARCHAR(64) NOT NULL UNIQUE,
                    banco VARCHAR(100),
                    data_importacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                    usuario VARCHAR(100) NOT NULL,
                    total_registros INTEGER DEFAULT 0,
                    registros_processados INTEGER DEFAULT 0,
                    registros_duplicados INTEGER DEFAULT 0,
                    registros_erro INTEGER DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'processando',
                    log_detalhado TEXT
                )
            """)
            print("   ✅ Tabela 'importacao_extrato' criada!")
        else:
            print("   ✅ Tabela 'importacao_extrato' já existe!")
        
        # 6. Criar índices para melhor performance
        print("\n🔄 CRIANDO ÍNDICES...")
        indices = [
            ("idx_lancamentos_hash", "CREATE INDEX IF NOT EXISTS idx_lancamentos_hash ON lancamentos(hash_duplicata)"),
            ("idx_lancamentos_origem", "CREATE INDEX IF NOT EXISTS idx_lancamentos_origem ON lancamentos(origem)"),
            ("idx_lancamentos_conciliado", "CREATE INDEX IF NOT EXISTS idx_lancamentos_conciliado ON lancamentos(conciliado)"),
            ("idx_pares_historico", "CREATE INDEX IF NOT EXISTS idx_pares_historico ON conciliacao_pares(historico_id)"),
            ("idx_pares_ativo", "CREATE INDEX IF NOT EXISTS idx_pares_ativo ON conciliacao_pares(ativo)"),
            ("idx_extrato_hash", "CREATE INDEX IF NOT EXISTS idx_extrato_hash ON importacao_extrato(hash_arquivo)")
        ]
        
        for nome_idx, sql_idx in indices:
            try:
                cursor.execute(sql_idx)
                print(f"   ✅ Índice '{nome_idx}' criado!")
            except sqlite3.Error:
                print(f"   ✅ Índice '{nome_idx}' já existe!")
        
        # Commit todas as alterações
        conn.commit()
        
        print("\n🎉 BANCO DE DADOS ATUALIZADO COM SUCESSO!")
        print("\n📊 ESTRUTURA FINAL:")
        
        # Verificar estrutura final
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tabelas = [tab[0] for tab in cursor.fetchall()]
        
        tabelas_financeiro = [t for t in tabelas if any(x in t for x in ['lancamentos', 'conciliacao', 'importacao', 'despesa'])]
        
        for tabela in tabelas_financeiro:
            cursor.execute(f"PRAGMA table_info({tabela})")
            colunas = [col[1] for col in cursor.fetchall()]
            print(f"   📋 {tabela}: {len(colunas)} colunas")
        
        # Verificar dados existentes
        cursor.execute("SELECT COUNT(*) FROM lancamentos")
        total_lancamentos = cursor.fetchone()[0]
        print(f"\n📈 DADOS EXISTENTES:")
        print(f"   💰 Lançamentos: {total_lancamentos}")
        
        if total_lancamentos > 0:
            cursor.execute("SELECT COUNT(*) FROM lancamentos WHERE origem = 'manual'")
            manuais = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM lancamentos WHERE origem = 'importado'")
            importados = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM lancamentos WHERE conciliado = 1")
            conciliados = cursor.fetchone()[0]
            
            print(f"   ✋ Manuais: {manuais}")
            print(f"   📥 Importados: {importados}")
            print(f"   🔗 Conciliados: {conciliados}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    sucesso = atualizar_banco_financeiro()
    if sucesso:
        print("\n🎯 PRÓXIMOS PASSOS:")
        print("   1. ✅ Banco atualizado")
        print("   2. 🔄 Testar importação de extratos")
        print("   3. 🤖 Testar conciliação automática")
        print("   4. 📊 Verificar dashboard de conciliação")
    else:
        print("\n⚠️  VERIFIQUE OS ERROS ACIMA E TENTE NOVAMENTE")