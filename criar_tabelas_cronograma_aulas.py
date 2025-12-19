#!/usr/bin/env python3
"""
Script para criar as novas tabelas de cronogramas e aulas de departamentos
OBPC - Sistema de Gestão de Igreja
Data: 06/10/2025
"""

import sqlite3
import os
import sys
from datetime import datetime

def conectar_banco():
    """Conecta ao banco de dados SQLite"""
    possiveis_caminhos = [
        os.path.join(os.path.dirname(__file__), 'instance', 'igreja.db'),
        os.path.join(os.path.dirname(__file__), 'igreja.db')
    ]
    
    for caminho in possiveis_caminhos:
        if os.path.exists(caminho):
            try:
                conn = sqlite3.connect(caminho)
                conn.execute("PRAGMA foreign_keys = ON")
                print(f"📁 Conectado ao banco: {caminho}")
                return conn
            except Exception as e:
                print(f"❌ Erro ao conectar: {e}")
                return None
    
    print("❌ Banco de dados não encontrado!")
    return None

def criar_tabelas_cronograma_aulas(conn):
    """Cria as novas tabelas para cronogramas e aulas"""
    try:
        cursor = conn.cursor()
        
        print("🔄 Criando tabela cronogramas_departamento...")
        
        # Tabela de cronogramas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cronogramas_departamento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                departamento_id INTEGER NOT NULL,
                data_evento DATE NOT NULL,
                titulo VARCHAR(200) NOT NULL,
                descricao TEXT,
                horario VARCHAR(50),
                local VARCHAR(200),
                responsavel VARCHAR(100),
                exibir_no_painel BOOLEAN DEFAULT 0,
                ativo BOOLEAN DEFAULT 1,
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (departamento_id) REFERENCES departamentos (id) ON DELETE CASCADE
            )
        """)
        
        print("✅ Tabela cronogramas_departamento criada")
        
        print("🔄 Criando tabela aulas_departamento...")
        
        # Tabela de aulas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS aulas_departamento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                departamento_id INTEGER NOT NULL,
                titulo VARCHAR(200) NOT NULL,
                descricao TEXT,
                professora VARCHAR(100),
                dia_semana VARCHAR(20),
                horario VARCHAR(50),
                local VARCHAR(200),
                data_inicio DATE,
                data_fim DATE,
                max_alunos INTEGER,
                material_necessario TEXT,
                exibir_no_painel BOOLEAN DEFAULT 0,
                ativo BOOLEAN DEFAULT 1,
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (departamento_id) REFERENCES departamentos (id) ON DELETE CASCADE
            )
        """)
        
        print("✅ Tabela aulas_departamento criada")
        
        # Criar índices para performance
        print("🔄 Criando índices...")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cronogramas_departamento ON cronogramas_departamento(departamento_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cronogramas_data ON cronogramas_departamento(data_evento)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cronogramas_painel ON cronogramas_departamento(exibir_no_painel)")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_aulas_departamento ON aulas_departamento(departamento_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_aulas_painel ON aulas_departamento(exibir_no_painel)")
        
        print("✅ Índices criados")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        conn.rollback()
        return False

def migrar_dados_existentes(conn):
    """Migra dados existentes dos campos de texto para as novas tabelas"""
    try:
        cursor = conn.cursor()
        
        print("🔄 Migrando dados existentes...")
        
        # Buscar departamentos com cronograma_mensal ou planejamento_aulas
        cursor.execute("""
            SELECT id, nome, cronograma_mensal, planejamento_aulas, possui_aulas
            FROM departamentos 
            WHERE cronograma_mensal IS NOT NULL 
            OR planejamento_aulas IS NOT NULL
        """)
        
        departamentos = cursor.fetchall()
        
        if departamentos:
            print(f"📊 Encontrados {len(departamentos)} departamentos com dados para migrar")
            
            for dept_id, nome, cronograma, planejamento, possui_aulas in departamentos:
                print(f"🔄 Migrando dados do departamento: {nome}")
                
                # Migrar cronograma_mensal como uma atividade genérica
                if cronograma and cronograma.strip():
                    cursor.execute("""
                        INSERT INTO cronogramas_departamento 
                        (departamento_id, data_evento, titulo, descricao, exibir_no_painel)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        dept_id,
                        datetime.now().date(),  # Data atual como placeholder
                        "Cronograma Mensal Migrado",
                        cronograma,
                        False  # Não exibir no painel por padrão
                    ))
                    print(f"  ✅ Cronograma migrado")
                
                # Migrar planejamento_aulas como uma aula genérica
                if planejamento and planejamento.strip() and possui_aulas:
                    cursor.execute("""
                        INSERT INTO aulas_departamento 
                        (departamento_id, titulo, descricao, exibir_no_painel)
                        VALUES (?, ?, ?, ?)
                    """, (
                        dept_id,
                        "Aula Migrada",
                        planejamento,
                        False  # Não exibir no painel por padrão
                    ))
                    print(f"  ✅ Planejamento de aulas migrado")
        else:
            print("ℹ️  Nenhum dado para migrar encontrado")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        conn.rollback()
        return False

def inserir_dados_exemplo(conn):
    """Insere alguns dados de exemplo para demonstração"""
    try:
        cursor = conn.cursor()
        
        print("🔄 Inserindo dados de exemplo...")
        
        # Buscar um departamento para usar como exemplo
        cursor.execute("SELECT id, nome FROM departamentos LIMIT 1")
        resultado = cursor.fetchone()
        
        if resultado:
            dept_id, nome = resultado
            print(f"📝 Criando exemplos para: {nome}")
            
            # Cronogramas de exemplo
            cronogramas_exemplo = [
                {
                    'data_evento': '2025-10-15',
                    'titulo': 'Reunião de Planejamento Mensal',
                    'descricao': 'Reunião para planejar as atividades do mês de novembro',
                    'horario': '19h30',
                    'local': 'Sala de reuniões',
                    'responsavel': 'Líder do Departamento',
                    'exibir_no_painel': True
                },
                {
                    'data_evento': '2025-10-22',
                    'titulo': 'Ensaio de Apresentação',
                    'descricao': 'Ensaio para a apresentação especial do próximo domingo',
                    'horario': '20h00',
                    'local': 'Santuário principal',
                    'responsavel': 'Coordenador de Música',
                    'exibir_no_painel': False
                }
            ]
            
            for cronograma in cronogramas_exemplo:
                cursor.execute("""
                    INSERT INTO cronogramas_departamento 
                    (departamento_id, data_evento, titulo, descricao, horario, local, responsavel, exibir_no_painel)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dept_id, cronograma['data_evento'], cronograma['titulo'],
                    cronograma['descricao'], cronograma['horario'], cronograma['local'],
                    cronograma['responsavel'], cronograma['exibir_no_painel']
                ))
            
            print("  ✅ Cronogramas de exemplo inseridos")
            
            # Aulas de exemplo
            aulas_exemplo = [
                {
                    'titulo': 'Curso de Discipulado',
                    'descricao': 'Curso básico para novos convertidos e membros interessados em crescer na fé',
                    'professora': 'Irmã Maria Santos',
                    'dia_semana': 'Quarta-feira',
                    'horario': '19h30 às 21h00',
                    'local': 'Sala de aulas',
                    'data_inicio': '2025-10-16',
                    'data_fim': '2025-12-18',
                    'max_alunos': 25,
                    'material_necessario': 'Bíblia, caderno, apostila',
                    'exibir_no_painel': True
                },
                {
                    'titulo': 'Estudo Bíblico - Livro de João',
                    'descricao': 'Estudo versículo por versículo do Evangelho de João',
                    'professora': 'Pastor João Silva',
                    'dia_semana': 'Domingo',
                    'horario': '17h00 às 18h00',
                    'local': 'Sala de jovens',
                    'data_inicio': '2025-10-13',
                    'max_alunos': 15,
                    'material_necessario': 'Bíblia',
                    'exibir_no_painel': False
                }
            ]
            
            for aula in aulas_exemplo:
                cursor.execute("""
                    INSERT INTO aulas_departamento 
                    (departamento_id, titulo, descricao, professora, dia_semana, horario, 
                     local, data_inicio, data_fim, max_alunos, material_necessario, exibir_no_painel)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dept_id, aula['titulo'], aula['descricao'], aula['professora'],
                    aula['dia_semana'], aula['horario'], aula['local'],
                    aula.get('data_inicio'), aula.get('data_fim'), aula.get('max_alunos'),
                    aula.get('material_necessario'), aula['exibir_no_painel']
                ))
            
            print("  ✅ Aulas de exemplo inseridas")
            
            # Marcar o departamento como tendo aulas
            cursor.execute("UPDATE departamentos SET possui_aulas = 1 WHERE id = ?", (dept_id,))
            
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inserir exemplos: {e}")
        conn.rollback()
        return False

def verificar_estrutura_final(conn):
    """Verifica a estrutura final das tabelas criadas"""
    try:
        cursor = conn.cursor()
        
        print("\n📋 ESTRUTURA FINAL DAS TABELAS:")
        print("-" * 50)
        
        # Verificar cronogramas
        cursor.execute("PRAGMA table_info(cronogramas_departamento)")
        colunas_cronograma = cursor.fetchall()
        
        print("📅 cronogramas_departamento:")
        for coluna in colunas_cronograma:
            print(f"   - {coluna[1]} ({coluna[2]})")
        
        # Verificar aulas
        cursor.execute("PRAGMA table_info(aulas_departamento)")
        colunas_aulas = cursor.fetchall()
        
        print("\n🎓 aulas_departamento:")
        for coluna in colunas_aulas:
            print(f"   - {coluna[1]} ({coluna[2]})")
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM cronogramas_departamento")
        total_cronogramas = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM aulas_departamento")
        total_aulas = cursor.fetchone()[0]
        
        print(f"\n📊 DADOS:")
        print(f"   - Cronogramas: {total_cronogramas}")
        print(f"   - Aulas: {total_aulas}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar estrutura: {e}")
        return False

def main():
    """Função principal"""
    print("=" * 60)
    print("🏛️  OBPC - Criação de Tabelas Cronograma e Aulas")
    print("=" * 60)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    conn = conectar_banco()
    if not conn:
        sys.exit(1)
    
    try:
        # Criar tabelas
        if not criar_tabelas_cronograma_aulas(conn):
            print("❌ Falha ao criar tabelas")
            sys.exit(1)
        
        # Migrar dados existentes
        if not migrar_dados_existentes(conn):
            print("⚠️  Falha na migração de dados")
        
        # Inserir dados de exemplo
        if not inserir_dados_exemplo(conn):
            print("⚠️  Falha ao inserir exemplos")
        
        # Verificar estrutura final
        verificar_estrutura_final(conn)
        
        print("\n" + "=" * 60)
        print("✅ CRIAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        print("📋 Novas funcionalidades disponíveis:")
        print("• Cronogramas detalhados com data, horário e responsável")
        print("• Sistema de aulas com professora e configurações")
        print("• Opção de exibir atividades no painel de entrada")
        print("• Interface dinâmica para adicionar/remover itens")
        print()
        print("🚀 Acesse /departamentos para testar!")
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()