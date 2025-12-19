import os
import sys
import sqlite3
from sqlalchemy import text
from app import create_app, db
from app.configuracoes.configuracoes_model import Configuracao

def verificar_tabela():
    """Verifica qual é o nome correto da tabela de configurações"""
    db_path = 'instance/igreja.db'
    
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Listar todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tabelas = cursor.fetchall()
        
        print("Tabelas encontradas:")
        for tabela in tabelas:
            print(f"- {tabela[0]}")
            
        # Procurar tabela de configurações
        for tabela in tabelas:
            if 'config' in tabela[0].lower():
                print(f"\nEstrutura da tabela {tabela[0]}:")
                cursor.execute(f"PRAGMA table_info({tabela[0]});")
                colunas = cursor.fetchall()
                for coluna in colunas:
                    print(f"  {coluna[1]} ({coluna[2]})")
                conn.close()
                return tabela[0]
        
        conn.close()
    
    return None

def atualizar_banco_diretoria():
    """Adiciona os novos campos da diretoria ao banco de dados"""
    
    # Primeiro verificar o nome da tabela
    nome_tabela = verificar_tabela()
    if not nome_tabela:
        print("✗ Tabela de configurações não encontrada!")
        return False
    
    print(f"\nUsando tabela: {nome_tabela}")
    
    app = create_app()
    
    with app.app_context():
        try:
            print("Iniciando atualização do banco de dados para diretoria...")
            
            # Lista de colunas para adicionar
            colunas_diretoria = [
                'presidente VARCHAR(100)',
                'vice_presidente VARCHAR(100)',
                'primeiro_secretario VARCHAR(100)',
                'segundo_secretario VARCHAR(100)',
                'primeiro_tesoureiro VARCHAR(100)',
                'segundo_tesoureiro VARCHAR(100)'
            ]
            
            # Adicionar cada coluna
            for coluna in colunas_diretoria:
                try:
                    comando = f"ALTER TABLE {nome_tabela} ADD COLUMN {coluna}"
                    db.session.execute(text(comando))
                    print(f"✓ Coluna adicionada: {coluna}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"⚠ Coluna já existe: {coluna}")
                    else:
                        print(f"✗ Erro: {comando} - {e}")
            
            # Confirmar alterações
            db.session.commit()
            print("✓ Comandos SQL executados com sucesso!")
            
            # Verificar se existe configuração e atualizar valores padrão
            config = Configuracao.query.first()
            if config:
                atualizado = False
                
                # Atualizar apenas se os campos estão vazios
                if not hasattr(config, 'presidente') or not config.presidente:
                    config.presidente = config.dirigente if config.dirigente else "Pastor Dirigente"
                    atualizado = True
                    
                if not hasattr(config, 'vice_presidente') or not config.vice_presidente:
                    config.vice_presidente = "Vice Presidente"
                    atualizado = True
                    
                if not hasattr(config, 'primeiro_secretario') or not config.primeiro_secretario:
                    config.primeiro_secretario = "1º Secretário"
                    atualizado = True
                    
                if not hasattr(config, 'segundo_secretario') or not config.segundo_secretario:
                    config.segundo_secretario = "2º Secretário"
                    atualizado = True
                    
                if not hasattr(config, 'primeiro_tesoureiro') or not config.primeiro_tesoureiro:
                    config.primeiro_tesoureiro = config.tesoureiro if config.tesoureiro else "1º Tesoureiro"
                    atualizado = True
                    
                if not hasattr(config, 'segundo_tesoureiro') or not config.segundo_tesoureiro:
                    config.segundo_tesoureiro = "2º Tesoureiro"
                    atualizado = True
                    
                if atualizado:
                    db.session.commit()
                    print("✓ Dados padrão da diretoria configurados!")
                else:
                    print("⚠ Dados da diretoria já estão configurados")
            else:
                print("⚠ Nenhuma configuração encontrada para atualizar")
                
            print("✓ Atualização concluída com sucesso!")
            
        except Exception as e:
            print(f"✗ Erro ao atualizar banco de dados: {e}")
            db.session.rollback()
            return False
            
    return True

if __name__ == "__main__":
    if atualizar_banco_diretoria():
        print("✅ Script executado com sucesso!")
    else:
        print("❌ Falha na execução do script!")
        sys.exit(1)