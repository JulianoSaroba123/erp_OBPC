#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para criar configuração padrão - Sistema OBPC
Igreja O Brasil para Cristo - Tietê/SP
"""

from app import create_app
from app.extensoes import db
from app.configuracoes.configuracoes_model import Configuracao

def criar_configuracao_padrao():
    """Cria a configuração padrão do sistema"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Verificando configurações do sistema...")
        
        # Verificar se já existe configuração
        config_existente = Configuracao.query.filter_by(id=1).first()
        
        if config_existente:
            print("⚠️  Configuração padrão já existe:")
            print(f"   • Nome da Igreja: {config_existente.nome_igreja}")
            print(f"   • Cidade: {config_existente.cidade}")
            print(f"   • Dirigente: {config_existente.dirigente or 'Não informado'}")
            print(f"   • Tesoureiro: {config_existente.tesoureiro or 'Não informado'}")
            print(f"   • Tema: {config_existente.tema}")
            
            resposta = input("\nDeseja resetar para os valores padrão? (s/N): ")
            if resposta.lower() not in ['s', 'sim', 'y', 'yes']:
                print("❌ Operação cancelada.")
                return
            
            # Remover configuração existente
            db.session.delete(config_existente)
            db.session.commit()
            print("🗑️  Configuração anterior removida.")
        
        # Criar nova configuração padrão
        try:
            config = Configuracao(
                id=1,
                nome_igreja='Igreja O Brasil para Cristo',
                cnpj='12.345.678/0001-90',
                dirigente='Pastor João Silva',
                tesoureiro='Maria Santos',
                cidade='Tietê',
                bairro='Centro',
                endereco='Rua da Igreja, 123',
                telefone='(15) 1234-5678',
                email='contato@obpc.org.br',
                logo='static/logo_obpc_novo.jpg',
                banco_padrao='Caixa Econômica Federal',
                percentual_conselho=10.0,
                saldo_inicial=0.0,
                rodape_relatorio='Igreja O Brasil para Cristo - Tietê/SP',
                exibir_logo_relatorio=True,
                campo_assinatura_1='Pastor Responsável',
                campo_assinatura_2='Tesoureiro(a)',
                fonte_relatorio='Helvetica',
                tema='escuro',
                cor_principal='#0b1b3a',
                cor_secundaria='#228B22',
                cor_destaque='#FFD700',
                mensagem_painel='Bem-vindo ao Sistema Administrativo da Igreja O Brasil para Cristo - Tietê/SP',
                backup_automatico=True,
                notificacoes_email=False,
                idioma='pt-BR',
                fuso_horario='America/Sao_Paulo'
            )
            
            db.session.add(config)
            db.session.commit()
            
            print("✅ Configuração padrão criada com sucesso!")
            print("\n📋 Dados da configuração:")
            print(f"   • Nome da Igreja: {config.nome_igreja}")
            print(f"   • CNPJ: {config.cnpj}")
            print(f"   • Dirigente: {config.dirigente}")
            print(f"   • Tesoureiro: {config.tesoureiro}")
            print(f"   • Cidade: {config.cidade}")
            print(f"   • Endereço: {config.endereco_completo()}")
            print(f"   • Telefone: {config.telefone_formatado()}")
            print(f"   • E-mail: {config.email}")
            print(f"   • Banco Padrão: {config.banco_padrao}")
            print(f"   • Percentual Conselho: {config.percentual_conselho}%")
            print(f"   • Tema: {config.tema.title()}")
            print(f"   • Cores: Principal={config.cor_principal}, Secundária={config.cor_secundaria}, Destaque={config.cor_destaque}")
            
            print("\n🌐 Acesse as configurações em: http://127.0.0.1:5000/configuracoes")
            print("⚙️  Use o menu lateral 'Configurações' para personalizar!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao criar configuração: {str(e)}")

if __name__ == '__main__':
    criar_configuracao_padrao()