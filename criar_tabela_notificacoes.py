#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para criar tabelas de notificações no banco de dados
Execute este script no Render para criar as tabelas necessárias
"""

from app import create_app, db
from app.notificacoes.notificacoes_model import ConfiguracaoNotificacoes, HistoricoNotificacoes

def criar_tabelas():
    """Cria as tabelas de notificações"""
    app = create_app()
    
    with app.app_context():
        try:
            # Criar todas as tabelas
            db.create_all()
            
            # Verificar se já existe configuração
            config = ConfiguracaoNotificacoes.query.first()
            
            if not config:
                print("Criando configuração padrão de notificações...")
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
                print("✅ Configuração criada com sucesso!")
            else:
                print("✅ Configuração já existe")
                # Atualizar campo hora_notificacao_automatica se não existir
                if not hasattr(config, 'hora_notificacao_automatica') or config.hora_notificacao_automatica is None:
                    config.hora_notificacao_automatica = '08:00'
                    db.session.commit()
                    print("✅ Campo hora_notificacao_automatica adicionado")
            
            print("\n✅ Tabelas de notificações criadas/verificadas com sucesso!")
            print(f"   - ConfiguracaoNotificacoes: OK")
            print(f"   - HistoricoNotificacoes: OK")
            
        except Exception as e:
            print(f"\n❌ Erro ao criar tabelas: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    criar_tabelas()
