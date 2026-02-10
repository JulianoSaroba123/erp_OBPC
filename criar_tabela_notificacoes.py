#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para criar tabelas de notificações no banco de dados
Execute este script no Render para criar as tabelas necessárias
"""

from app import create_app, db
from sqlalchemy import text, inspect
import sys

def criar_tabelas():
    """Cria as tabelas de notificações"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Iniciando atualização do banco de dados...")
            
            # Verificar se a tabela existe
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"📋 Tabelas existentes: {', '.join(tables)}")
            
            # Criar todas as tabelas
            print("📦 Criando/atualizando tabelas...")
            db.create_all()
            
            # Verificar se a coluna hora_notificacao_automatica existe
            if 'configuracao_notificacoes' in tables:
                columns = [col['name'] for col in inspector.get_columns('configuracao_notificacoes')]
                print(f"📝 Colunas em configuracao_notificacoes: {', '.join(columns)}")
                
                # Adicionar coluna se não existir
                if 'hora_notificacao_automatica' not in columns:
                    print("➕ Adicionando coluna hora_notificacao_automatica...")
                    try:
                        db.session.execute(text(
                            "ALTER TABLE configuracao_notificacoes ADD COLUMN hora_notificacao_automatica VARCHAR(5) DEFAULT '08:00'"
                        ))
                        db.session.commit()
                        print("✅ Coluna adicionada com sucesso!")
                    except Exception as e:
                        print(f"⚠️  Erro ao adicionar coluna (talvez já exista): {str(e)}")
                        db.session.rollback()
            
            # Importar modelos apenas após criar tabelas
            from app.notificacoes.notificacoes_model import ConfiguracaoNotificacoes
            
            # Verificar configuração
            try:
                config = db.session.query(ConfiguracaoNotificacoes).first()
                
                if not config:
                    print("➕ Criando configuração padrão de notificações...")
                    config = ConfiguracaoNotificacoes(
                        email_habilitado=False,
                        whatsapp_habilitado=False,
                        notificar_aniversariantes=True,
                        notificar_admin=True,
                        dias_antes=0,
                        hora_notificacao_automatica='08:00'
                    )
                    db.session.add(config)
                    db.session.commit()
                    print("✅ Configuração criada!")
                else:
                    print("✅ Configuração já existe")
                    # Atualizar campo se estiver None
                    if config.hora_notificacao_automatica is None:
                        config.hora_notificacao_automatica = '08:00'
                        db.session.commit()
                        print("✅ Campo hora_notificacao_automatica atualizado")
                        
            except Exception as e:
                print(f"⚠️  Erro ao verificar configuração: {str(e)}")
                db.session.rollback()
            
            print("\n✅ Processo concluído com sucesso!")
            print("🔄 Agora atualize a página no navegador (F5)")
            
        except Exception as e:
            print(f"\n❌ Erro: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    criar_tabelas()
