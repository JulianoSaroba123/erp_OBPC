#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para Criar Sistema de Despesas Fixas do Conselho Administrativo
Igreja O Brasil para Cristo - Tietê/SP

Este script cria a infraestrutura para gerenciar despesas fixas mensais
que são enviadas para o conselho administrativo.
"""

import os
import sys

# Adicionar o diretório pai ao path do Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensoes import db
from datetime import datetime

# Criar aplicação Flask
app = create_app()

class DespesaFixaConselho(db.Model):
    """Modelo para despesas fixas do conselho administrativo"""
    __tablename__ = 'despesas_fixas_conselho'
    
    # Campos principais
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)  # Ex: "Oferta Voluntária Conchas"
    descricao = db.Column(db.Text, nullable=True)  # Descrição detalhada
    valor_padrao = db.Column(db.Float, nullable=False, default=0.0)  # Valor padrão mensal
    
    # Configurações
    ativo = db.Column(db.Boolean, nullable=False, default=True)  # Se está ativo
    tipo = db.Column(db.String(50), nullable=False, default='despesa_fixa')  # Tipo da despesa
    categoria = db.Column(db.String(100), nullable=True)  # Categoria se necessário
    
    # Campos de auditoria
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DespesaFixaConselho {self.nome}: R$ {self.valor_padrao:.2f}>'
    
    @classmethod
    def obter_despesas_ativas(cls):
        """Obtém todas as despesas fixas ativas"""
        return cls.query.filter_by(ativo=True).order_by(cls.nome).all()
    
    @classmethod
    def obter_total_despesas_fixas(cls):
        """Calcula o total das despesas fixas ativas"""
        despesas = cls.obter_despesas_ativas()
        return sum(despesa.valor_padrao for despesa in despesas)
    
    @classmethod
    def obter_despesas_como_dict(cls):
        """Retorna as despesas como dicionário para uso nos relatórios"""
        despesas = cls.obter_despesas_ativas()
        return {
            despesa.nome.lower().replace(' ', '_').replace('ã', 'a').replace('ç', 'c'): despesa.valor_padrao 
            for despesa in despesas
        }


def criar_despesas_fixas_padrao():
    """Cria as despesas fixas padrão do sistema"""
    despesas_padrao = [
        {
            'nome': 'Oferta Voluntária Conchas',
            'descricao': 'Oferta voluntária mensal para a igreja de Conchas',
            'valor_padrao': 50.00,
            'tipo': 'despesa_fixa',
            'categoria': 'Ofertas Especiais'
        },
        {
            'nome': 'Site',
            'descricao': 'Manutenção e hospedagem do site da igreja',
            'valor_padrao': 25.00,
            'tipo': 'despesa_fixa',
            'categoria': 'Tecnologia'
        },
        {
            'nome': 'Projeto Filipe',
            'descricao': 'Contribuição mensal para o Projeto Filipe',
            'valor_padrao': 100.00,
            'tipo': 'despesa_fixa',
            'categoria': 'Projetos Sociais'
        },
        {
            'nome': 'Força para Viver',
            'descricao': 'Contribuição para o programa Força para Viver',
            'valor_padrao': 30.00,
            'tipo': 'despesa_fixa',
            'categoria': 'Programas'
        },
        {
            'nome': 'Contador Sede',
            'descricao': 'Honorários do contador da sede administrativa',
            'valor_padrao': 150.00,
            'tipo': 'despesa_fixa',
            'categoria': 'Serviços Profissionais'
        }
    ]
    
    print("📋 Criando despesas fixas padrão do conselho...")
    
    for despesa_data in despesas_padrao:
        # Verificar se já existe
        despesa_existente = DespesaFixaConselho.query.filter_by(nome=despesa_data['nome']).first()
        
        if not despesa_existente:
            despesa = DespesaFixaConselho(
                nome=despesa_data['nome'],
                descricao=despesa_data['descricao'],
                valor_padrao=despesa_data['valor_padrao'],
                tipo=despesa_data['tipo'],
                categoria=despesa_data['categoria'],
                ativo=True
            )
            
            db.session.add(despesa)
            print(f"✅ Criada: {despesa.nome} - R$ {despesa.valor_padrao:.2f}")
        else:
            print(f"ℹ️  Já existe: {despesa_existente.nome} - R$ {despesa_existente.valor_padrao:.2f}")
    
    try:
        db.session.commit()
        print(f"\n🎉 Sistema de despesas fixas criado com sucesso!")
        
        # Mostrar resumo
        total = DespesaFixaConselho.obter_total_despesas_fixas()
        print(f"💰 Total das despesas fixas mensais: R$ {total:.2f}")
        
        despesas_ativas = DespesaFixaConselho.obter_despesas_ativas()
        print(f"📊 Total de despesas ativas: {len(despesas_ativas)}")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao criar despesas fixas: {str(e)}")
        return False
    
    return True


def main():
    """Função principal"""
    print("="*60)
    print("🏛️  SISTEMA DE DESPESAS FIXAS - CONSELHO ADMINISTRATIVO")
    print("⛪ Igreja O Brasil para Cristo - Tietê/SP")
    print("="*60)
    
    with app.app_context():
        try:
            # Criar tabelas se não existirem
            print("🔧 Criando estrutura do banco de dados...")
            db.create_all()
            print("✅ Estrutura do banco criada com sucesso!")
            
            # Criar despesas fixas padrão
            if criar_despesas_fixas_padrao():
                print("\n" + "="*60)
                print("✅ SISTEMA DE DESPESAS FIXAS CONFIGURADO!")
                print("="*60)
                print("\n📝 Próximos passos:")
                print("1. Integrar com os relatórios")
                print("2. Criar interface de gerenciamento")
                print("3. Permitir edição dos valores")
                print("\n💡 As despesas fixas agora podem ser gerenciadas automaticamente!")
            else:
                print("❌ Falha na configuração do sistema.")
                
        except Exception as e:
            print(f"❌ Erro crítico: {str(e)}")
            return False
    
    return True


if __name__ == '__main__':
    main()