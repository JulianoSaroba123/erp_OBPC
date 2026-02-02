#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para Cadastrar Despesas Fixas Iniciais
Igreja O Brasil para Cristo - Tietê/SP

Cadastra as 5 despesas fixas mensais:
1. Contribuição Força para Viver
2. Contador
3. Site
4. Projeto Filipe
5. Auxilio Conchas
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.financeiro.despesas_fixas_model import DespesaFixaConselho

def cadastrar_despesas_fixas():
    """Cadastra as despesas fixas iniciais no sistema"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("CADASTRO DE DESPESAS FIXAS - OBPC")
        print("=" * 80)
        
        # Lista de despesas fixas a serem cadastradas
        despesas_para_cadastrar = [
            {
                'nome': 'Contribuição Força para Viver',
                'descricao': 'Contribuição mensal para o projeto Força para Viver da sede',
                'valor_padrao': 0.0,  # Definir o valor posteriormente
                'tipo': 'contribuicao',
                'categoria': 'CONTRIB. SEDE'
            },
            {
                'nome': 'Contador',
                'descricao': 'Pagamento mensal do contador da sede',
                'valor_padrao': 0.0,  # Definir o valor posteriormente
                'tipo': 'servico',
                'categoria': 'DESP. ADMINISTRATIVAS'
            },
            {
                'nome': 'Site',
                'descricao': 'Manutenção e hospedagem do site institucional',
                'valor_padrao': 0.0,  # Definir o valor posteriormente
                'tipo': 'servico',
                'categoria': 'DESP. ADMINISTRATIVAS'
            },
            {
                'nome': 'Projeto Filipe',
                'descricao': 'Contribuição mensal para o Projeto Filipe',
                'valor_padrao': 0.0,  # Definir o valor posteriormente
                'tipo': 'projeto',
                'categoria': 'CONTRIB. SEDE'
            },
            {
                'nome': 'Auxílio Conchas',
                'descricao': 'Oferta voluntária mensal para a Igreja Sede em Conchas',
                'valor_padrao': 0.0,  # Definir o valor posteriormente
                'tipo': 'oferta',
                'categoria': 'OFERTAS VOLUNTÁRIAS'
            }
        ]
        
        cadastradas = 0
        atualizadas = 0
        
        for despesa_data in despesas_para_cadastrar:
            # Verificar se já existe
            despesa_existente = DespesaFixaConselho.query.filter_by(
                nome=despesa_data['nome']
            ).first()
            
            if despesa_existente:
                print(f"\n✓ '{despesa_data['nome']}' já existe no banco!")
                print(f"  - Valor atual: R$ {despesa_existente.valor_padrao:.2f}")
                print(f"  - Status: {'ATIVO' if despesa_existente.ativo else 'INATIVO'}")
                atualizadas += 1
            else:
                # Criar nova despesa
                nova_despesa = DespesaFixaConselho(
                    nome=despesa_data['nome'],
                    descricao=despesa_data['descricao'],
                    valor_padrao=despesa_data['valor_padrao'],
                    tipo=despesa_data['tipo'],
                    categoria=despesa_data['categoria'],
                    ativo=True
                )
                
                db.session.add(nova_despesa)
                print(f"\n✓ Cadastrando '{despesa_data['nome']}'...")
                print(f"  - Tipo: {despesa_data['tipo']}")
                print(f"  - Categoria: {despesa_data['categoria']}")
                print(f"  - Valor inicial: R$ 0,00 (definir manualmente no sistema)")
                cadastradas += 1
        
        # Salvar no banco de dados
        try:
            db.session.commit()
            print("\n" + "=" * 80)
            print(f"✅ OPERAÇÃO CONCLUÍDA COM SUCESSO!")
            print(f"   - {cadastradas} nova(s) despesa(s) cadastrada(s)")
            print(f"   - {atualizadas} despesa(s) já existente(s)")
            print("=" * 80)
            
            # Listar todas as despesas ativas
            print("\n📋 DESPESAS FIXAS ATIVAS NO SISTEMA:")
            print("-" * 80)
            
            despesas_ativas = DespesaFixaConselho.obter_despesas_ativas()
            total = 0
            
            for despesa in despesas_ativas:
                print(f"  • {despesa.nome:40} R$ {despesa.valor_padrao:>10.2f}")
                total += despesa.valor_padrao
            
            print("-" * 80)
            print(f"  TOTAL MENSAL:                             R$ {total:>10.2f}")
            print("=" * 80)
            
            print("\n💡 PRÓXIMOS PASSOS:")
            print("   1. Acesse o sistema: Financeiro > Gerenciar Despesas Fixas")
            print("   2. Edite cada despesa e defina o valor mensal correto")
            print("   3. Use o botão 'Gerar Lançamentos' para criar os lançamentos mensais")
            print("   4. O sistema vai criar automaticamente as saídas no mês selecionado")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRO ao salvar no banco: {str(e)}")
            return False
        
        return True

if __name__ == '__main__':
    print("\n🚀 Iniciando cadastro de despesas fixas...\n")
    sucesso = cadastrar_despesas_fixas()
    
    if sucesso:
        print("\n✅ Script executado com sucesso!")
        print("   Acesse o sistema para configurar os valores.\n")
    else:
        print("\n❌ Erro na execução do script.\n")
        sys.exit(1)
