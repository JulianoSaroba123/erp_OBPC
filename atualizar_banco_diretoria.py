#!/usr/bin/env python3
"""
Script para adicionar os novos campos da diretoria na tabela de configurações
"""
import sys
import os

# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.configuracoes.configuracoes_model import Configuracao

def atualizar_banco_diretoria():
    """Adiciona os novos campos da diretoria ao banco de dados"""
    print("Iniciando atualização do banco de dados para diretoria...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Primeiro, vamos tentar adicionar as colunas uma por uma
            comandos_sql = [
                "ALTER TABLE configuracao ADD COLUMN presidente VARCHAR(100)",
                "ALTER TABLE configuracao ADD COLUMN vice_presidente VARCHAR(100)",
                "ALTER TABLE configuracao ADD COLUMN primeiro_secretario VARCHAR(100)",
                "ALTER TABLE configuracao ADD COLUMN segundo_secretario VARCHAR(100)",
                "ALTER TABLE configuracao ADD COLUMN primeiro_tesoureiro VARCHAR(100)",
                "ALTER TABLE configuracao ADD COLUMN segundo_tesoureiro VARCHAR(100)"
            ]
            
            for comando in comandos_sql:
                try:
                    db.session.execute(comando)
                    print(f"✓ Executado: {comando}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"! Coluna já existe: {comando}")
                    else:
                        print(f"✗ Erro: {comando} - {e}")
            
            db.session.commit()
            print("✓ Comandos SQL executados com sucesso!")
            
            # Agora vamos atualizar a configuração existente com dados padrão
            config = Configuracao.query.first()
            if config:
                if not config.presidente:
                    config.presidente = config.dirigente  # Usar o dirigente atual como presidente
                if not config.vice_presidente:
                    config.vice_presidente = "Pastora Ana Silva"
                if not config.primeiro_secretario:
                    config.primeiro_secretario = "José dos Santos"
                if not config.segundo_secretario:
                    config.segundo_secretario = "Maria da Silva"
                if not config.primeiro_tesoureiro:
                    config.primeiro_tesoureiro = config.tesoureiro  # Usar o tesoureiro atual como 1º tesoureiro
                if not config.segundo_tesoureiro:
                    config.segundo_tesoureiro = "Ana Santos"
                
                db.session.commit()
                print("✓ Configuração atualizada com dados padrão da diretoria")
            
            print("\n✅ Atualização do banco de dados concluída com sucesso!")
            print("Os novos campos da diretoria foram adicionados:")
            print("- Presidente (Pastor Dirigente)")
            print("- Vice-Presidente (Pastora)")
            print("- 1º Secretário(a)")
            print("- 2º Secretário(a)")
            print("- 1º Tesoureiro(a)")
            print("- 2º Tesoureiro(a)")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Erro ao atualizar banco de dados: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = atualizar_banco_diretoria()
    sys.exit(0 if success else 1)