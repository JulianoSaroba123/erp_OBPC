#!/usr/bin/env python3
"""
Script para atualizar a tabela departamentos com os novos campos:
- cronograma_mensal (TEXT)
- possui_aulas (BOOLEAN) 
- planejamento_aulas (TEXT)
- Renomear data_cadastro para criado_em

OBPC - Sistema de Gestão de Igreja
Versão: 2025.1
Data: 06/10/2025
"""

import sqlite3
import os
import sys
from datetime import datetime

def conectar_banco():
    """Conecta ao banco de dados SQLite"""
    # Tentar diferentes localizações do banco
    possiveis_caminhos = [
        os.path.join(os.path.dirname(__file__), 'instance', 'igreja.db'),
        os.path.join(os.path.dirname(__file__), 'igreja.db'),
        os.path.join(os.path.dirname(__file__), 'instance', 'obpc.db'),
        os.path.join(os.path.dirname(__file__), 'obpc.db')
    ]
    
    db_path = None
    for caminho in possiveis_caminhos:
        if os.path.exists(caminho):
            db_path = caminho
            break
    
    if not db_path:
        print("❌ Banco de dados não encontrado nos seguintes locais:")
        for caminho in possiveis_caminhos:
            print(f"   - {caminho}")
        print("\n💡 Dica: Execute primeiro o sistema para criar o banco de dados")
        return None
    
    print(f"📁 Banco encontrado em: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")  # Habilitar chaves estrangeiras
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return None

def verificar_colunas_existem(conn):
    """Verifica quais colunas já existem na tabela departamentos"""
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(departamentos)")
        colunas = [row[1] for row in cursor.fetchall()]
        return colunas
    except Exception as e:
        print(f"❌ Erro ao verificar colunas: {e}")
        return []

def executar_migracao(conn):
    """Executa a migração do banco de dados"""
    try:
        cursor = conn.cursor()
        
        print("🔄 Iniciando migração da tabela departamentos...")
        
        # Verificar colunas existentes
        colunas_existentes = verificar_colunas_existem(conn)
        print(f"📊 Colunas existentes: {colunas_existentes}")
        
        # Adicionar novas colunas se não existirem
        colunas_para_adicionar = {
            'cronograma_mensal': 'TEXT',
            'possui_aulas': 'BOOLEAN DEFAULT 0',
            'planejamento_aulas': 'TEXT'
        }
        
        for nome_coluna, tipo_coluna in colunas_para_adicionar.items():
            if nome_coluna not in colunas_existentes:
                try:
                    sql = f"ALTER TABLE departamentos ADD COLUMN {nome_coluna} {tipo_coluna}"
                    cursor.execute(sql)
                    print(f"✅ Coluna '{nome_coluna}' adicionada com sucesso")
                except Exception as e:
                    print(f"⚠️  Erro ao adicionar coluna '{nome_coluna}': {e}")
            else:
                print(f"ℹ️  Coluna '{nome_coluna}' já existe")
        
        # Verificar se precisa renomear data_cadastro para criado_em
        if 'data_cadastro' in colunas_existentes and 'criado_em' not in colunas_existentes:
            try:
                # SQLite não suporta ALTER COLUMN, então precisamos recriar a tabela
                print("🔄 Renomeando coluna data_cadastro para criado_em...")
                
                # Criar tabela temporária
                cursor.execute("""
                    CREATE TABLE departamentos_temp (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome VARCHAR(100) NOT NULL,
                        lider VARCHAR(100),
                        vice_lider VARCHAR(100),
                        descricao TEXT,
                        contato VARCHAR(120),
                        status VARCHAR(20) DEFAULT 'Ativo',
                        cronograma_mensal TEXT,
                        possui_aulas BOOLEAN DEFAULT 0,
                        planejamento_aulas TEXT,
                        criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Copiar dados da tabela original
                cursor.execute("""
                    INSERT INTO departamentos_temp 
                    (id, nome, lider, vice_lider, descricao, contato, status, 
                     cronograma_mensal, possui_aulas, planejamento_aulas, criado_em)
                    SELECT id, nome, lider, vice_lider, descricao, contato, status,
                           cronograma_mensal, possui_aulas, planejamento_aulas, 
                           COALESCE(data_cadastro, CURRENT_TIMESTAMP)
                    FROM departamentos
                """)
                
                # Remover tabela original
                cursor.execute("DROP TABLE departamentos")
                
                # Renomear tabela temporária
                cursor.execute("ALTER TABLE departamentos_temp RENAME TO departamentos")
                
                print("✅ Coluna renomeada com sucesso")
                
            except Exception as e:
                print(f"⚠️  Erro ao renomear coluna: {e}")
                # Reverter se der erro
                cursor.execute("DROP TABLE IF EXISTS departamentos_temp")
        
        elif 'criado_em' in colunas_existentes:
            print("ℹ️  Coluna 'criado_em' já existe")
        
        # Commit das alterações
        conn.commit()
        print("✅ Migração concluída com sucesso!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        conn.rollback()
        return False

def verificar_dados_apos_migracao(conn):
    """Verifica os dados após a migração"""
    try:
        cursor = conn.cursor()
        
        # Verificar estrutura final
        cursor.execute("PRAGMA table_info(departamentos)")
        colunas_finais = cursor.fetchall()
        
        print("\n📋 Estrutura final da tabela departamentos:")
        for coluna in colunas_finais:
            print(f"   - {coluna[1]} ({coluna[2]})")
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM departamentos")
        total_registros = cursor.fetchone()[0]
        
        print(f"\n📊 Total de departamentos: {total_registros}")
        
        if total_registros > 0:
            # Mostrar alguns exemplos
            cursor.execute("""
                SELECT nome, possui_aulas, 
                       CASE WHEN cronograma_mensal IS NOT NULL THEN 'Sim' ELSE 'Não' END as tem_cronograma,
                       CASE WHEN planejamento_aulas IS NOT NULL THEN 'Sim' ELSE 'Não' END as tem_planejamento
                FROM departamentos 
                LIMIT 5
            """)
            
            exemplos = cursor.fetchall()
            print("\n📝 Exemplos de departamentos:")
            for exemplo in exemplos:
                print(f"   - {exemplo[0]}: Aulas={exemplo[1]}, Cronograma={exemplo[2]}, Planejamento={exemplo[3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar dados: {e}")
        return False

def main():
    """Função principal"""
    print("=" * 60)
    print("🏛️  OBPC - Atualização do Módulo Departamentos")
    print("=" * 60)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Conectar ao banco
    conn = conectar_banco()
    if not conn:
        sys.exit(1)
    
    try:
        # Fazer backup antes da migração
        print("💾 Criando backup do banco...")
        backup_path = f"backup_departamentos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        # Executar migração
        if executar_migracao(conn):
            print("\n🎉 Migração realizada com sucesso!")
            
            # Verificar dados
            verificar_dados_apos_migracao(conn)
            
            print("\n" + "=" * 60)
            print("✅ ATUALIZAÇÃO CONCLUÍDA!")
            print("=" * 60)
            print("Novos campos adicionados:")
            print("• cronograma_mensal - Para atividades mensais")
            print("• possui_aulas - Checkbox para departamentos com ensino")
            print("• planejamento_aulas - Planejamento detalhado das aulas")
            print()
            print("🚀 O módulo Departamentos está pronto para uso!")
            
        else:
            print("\n❌ Falha na migração!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()