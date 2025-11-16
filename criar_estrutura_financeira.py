#!/usr/bin/env python3
"""
Script para criar estrutura completa do módulo financeiro
"""

import sqlite3
import os
from datetime import datetime

def criar_estrutura_financeira():
    """Cria estrutura completa do módulo financeiro"""
    
    print("=== CRIANDO ESTRUTURA COMPLETA DO MÓDULO FINANCEIRO ===")
    print()
    
    # Conectar ao banco SQLite
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
    
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
        print(f"✅ Diretório criado: {os.path.dirname(db_path)}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"✅ Conectado ao banco: {db_path}")
        
        # Verificar tabelas existentes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas_existentes = [tab[0] for tab in cursor.fetchall()]
        print(f"📋 Tabelas existentes: {tabelas_existentes}")
        
        # 1. Criar tabela lancamentos
        print("\n🔄 CRIANDO TABELA 'lancamentos'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lancamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data DATE DEFAULT (DATE('now')),
                tipo VARCHAR(20) NOT NULL,
                categoria VARCHAR(100),
                descricao VARCHAR(200),
                valor REAL NOT NULL,
                conta VARCHAR(50),
                observacoes TEXT,
                comprovante VARCHAR(300),
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                origem VARCHAR(50) DEFAULT 'manual',
                conciliado BOOLEAN DEFAULT 0,
                hash_duplicata VARCHAR(64),
                banco_origem VARCHAR(100),
                documento_ref VARCHAR(50),
                conciliado_em DATETIME,
                conciliado_por VARCHAR(100),
                par_conciliacao_id INTEGER
            )
        """)
        print("   ✅ Tabela 'lancamentos' criada!")
        
        # 2. Criar tabela conciliacao_historico
        print("\n🔄 CRIANDO TABELA 'conciliacao_historico'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conciliacao_historico (
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
        
        # 3. Criar tabela conciliacao_pares
        print("\n🔄 CRIANDO TABELA 'conciliacao_pares'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conciliacao_pares (
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
        
        # 4. Criar tabela importacao_extrato
        print("\n🔄 CRIANDO TABELA 'importacao_extrato'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS importacao_extrato (
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
        
        # 5. Criar tabela despesas_fixas_conselho (se não existir)
        print("\n🔄 CRIANDO TABELA 'despesas_fixas_conselho'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS despesas_fixas_conselho (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR(100) NOT NULL,
                descricao TEXT,
                categoria VARCHAR(50),
                valor_padrao REAL DEFAULT 0,
                ativo BOOLEAN DEFAULT 1,
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ Tabela 'despesas_fixas_conselho' criada!")
        
        # 6. Criar índices para melhor performance
        print("\n🔄 CRIANDO ÍNDICES...")
        indices = [
            ("idx_lancamentos_data", "CREATE INDEX IF NOT EXISTS idx_lancamentos_data ON lancamentos(data)"),
            ("idx_lancamentos_tipo", "CREATE INDEX IF NOT EXISTS idx_lancamentos_tipo ON lancamentos(tipo)"),
            ("idx_lancamentos_hash", "CREATE INDEX IF NOT EXISTS idx_lancamentos_hash ON lancamentos(hash_duplicata)"),
            ("idx_lancamentos_origem", "CREATE INDEX IF NOT EXISTS idx_lancamentos_origem ON lancamentos(origem)"),
            ("idx_lancamentos_conciliado", "CREATE INDEX IF NOT EXISTS idx_lancamentos_conciliado ON lancamentos(conciliado)"),
            ("idx_pares_historico", "CREATE INDEX IF NOT EXISTS idx_pares_historico ON conciliacao_pares(historico_id)"),
            ("idx_pares_ativo", "CREATE INDEX IF NOT EXISTS idx_pares_ativo ON conciliacao_pares(ativo)"),
            ("idx_extrato_hash", "CREATE INDEX IF NOT EXISTS idx_extrato_hash ON importacao_extrato(hash_arquivo)"),
            ("idx_despesas_ativo", "CREATE INDEX IF NOT EXISTS idx_despesas_ativo ON despesas_fixas_conselho(ativo)")
        ]
        
        for nome_idx, sql_idx in indices:
            try:
                cursor.execute(sql_idx)
                print(f"   ✅ Índice '{nome_idx}' criado!")
            except sqlite3.Error:
                print(f"   ⚠️ Índice '{nome_idx}' já existe!")
        
        # 7. Inserir dados de exemplo para despesas fixas
        print("\n🔄 INSERINDO DESPESAS FIXAS PADRÃO...")
        despesas_padrao = [
            ("Taxa Convenção", "Taxa mensal para convenção", "Administrativa", 150.00),
            ("Seguro Igreja", "Seguro da propriedade", "Administrativa", 80.00),
            ("Manutenção Predial", "Manutenção geral do prédio", "Manutenção", 120.00)
        ]
        
        for nome, desc, cat, valor in despesas_padrao:
            cursor.execute("""
                INSERT OR IGNORE INTO despesas_fixas_conselho (nome, descricao, categoria, valor_padrao)
                VALUES (?, ?, ?, ?)
            """, (nome, desc, cat, valor))
        
        # 8. Inserir alguns lançamentos de exemplo
        print("\n🔄 INSERINDO LANÇAMENTOS DE EXEMPLO...")
        lancamentos_exemplo = [
            ('2024-11-01', 'Entrada', 'Dízimo', 'Dízimo do mês', 1500.00, 'Banco'),
            ('2024-11-01', 'Entrada', 'Oferta', 'Oferta dominical', 800.00, 'Dinheiro'),
            ('2024-11-02', 'Saída', 'Despesa Administrativa', 'Conta de luz', 250.00, 'Banco'),
            ('2024-11-03', 'Entrada', 'Dízimo', 'Dízimo semanal', 600.00, 'Pix'),
            ('2024-11-04', 'Saída', 'Manutenção', 'Reparo no telhado', 400.00, 'Banco')
        ]
        
        for data, tipo, categoria, descricao, valor, conta in lancamentos_exemplo:
            cursor.execute("""
                INSERT OR IGNORE INTO lancamentos (data, tipo, categoria, descricao, valor, conta, origem)
                VALUES (?, ?, ?, ?, ?, ?, 'manual')
            """, (data, tipo, categoria, descricao, valor, conta))
        
        # Commit todas as alterações
        conn.commit()
        
        print("\n🎉 ESTRUTURA FINANCEIRA CRIADA COM SUCESSO!")
        print("\n📊 VERIFICAÇÃO FINAL:")
        
        # Verificar estrutura final
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tabelas = [tab[0] for tab in cursor.fetchall()]
        
        tabelas_financeiro = [t for t in tabelas if any(x in t for x in ['lancamentos', 'conciliacao', 'importacao', 'despesa'])]
        
        for tabela in tabelas_financeiro:
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
            registros = cursor.fetchone()[0]
            print(f"   📋 {tabela}: {registros} registros")
        
        # Verificar dados dos lançamentos
        cursor.execute("SELECT COUNT(*) FROM lancamentos")
        total_lancamentos = cursor.fetchone()[0]
        
        if total_lancamentos > 0:
            cursor.execute("SELECT SUM(valor) FROM lancamentos WHERE tipo = 'Entrada'")
            total_entradas = cursor.fetchone()[0] or 0
            cursor.execute("SELECT SUM(valor) FROM lancamentos WHERE tipo = 'Saída'")
            total_saidas = cursor.fetchone()[0] or 0
            saldo = total_entradas - total_saidas
            
            print(f"\n💰 RESUMO FINANCEIRO:")
            print(f"   💚 Entradas: R$ {total_entradas:,.2f}")
            print(f"   🔴 Saídas: R$ {total_saidas:,.2f}")
            print(f"   💙 Saldo: R$ {saldo:,.2f}")
        
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
    sucesso = criar_estrutura_financeira()
    if sucesso:
        print("\n🎯 ESTRUTURA PRONTA! PRÓXIMOS PASSOS:")
        print("   1. ✅ Banco de dados configurado")
        print("   2. 🌐 Iniciar servidor: python app.py")
        print("   3. 🔗 Acessar: http://127.0.0.1:5000/financeiro")
        print("   4. 📥 Testar importação de extratos")
        print("   5. 🤖 Testar conciliação automática")
    else:
        print("\n⚠️  VERIFIQUE OS ERROS ACIMA E TENTE NOVAMENTE")