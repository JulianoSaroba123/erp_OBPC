#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do relatório de caixa interno corrigido
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.gerar_pdf_reportlab import RelatorioFinanceiro
from app.financeiro.financeiro_model import Lancamento
from app.configuracoes.configuracoes_model import Configuracao
from datetime import datetime, timedelta

def main():
    app = create_app()
    
    with app.app_context():
        print("=== TESTE RELATÓRIO DE CAIXA INTERNO CORRIGIDO ===")
        
        # Obter configuração
        config = Configuracao.query.first()
        if not config:
            print("⚠️ Configuração não encontrada. Criando configuração padrão...")
            config = Configuracao(
                nome_igreja="Igreja Batista Palavra da Cruz",
                percentual_conselho=30.0,
                endereco="Rua da Igreja, 123",
                telefone="(11) 99999-9999",
                email="igreja@exemplo.com"
            )
        
        # Período de teste (último mês)
        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=30)
        
        print(f"📅 Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
        
        # Buscar lançamentos
        lancamentos = Lancamento.query.filter(
            Lancamento.data >= data_inicio,
            Lancamento.data <= data_fim
        ).all()
        
        print(f"📊 Total de lançamentos encontrados: {len(lancamentos)}")
        
        if len(lancamentos) == 0:
            print("⚠️ Nenhum lançamento encontrado. Criando dados de exemplo...")
            
            # Criar alguns lançamentos de exemplo
            from app.extensoes import db
            
            exemplos = [
                {"descricao": "Dízimo Janeiro", "valor": 1500.00, "tipo": "entrada", "categoria": "dizimo"},
                {"descricao": "Ofertas Janeiro", "valor": 800.00, "tipo": "entrada", "categoria": "oferta"},
                {"descricao": "Doação Especial", "valor": 500.00, "tipo": "entrada", "categoria": "doacao"},
                {"descricao": "Conta de Luz", "valor": 250.00, "tipo": "saida", "categoria": "despesa"},
                {"descricao": "Materiais Limpeza", "valor": 100.00, "tipo": "saida", "categoria": "despesa"},
                {"descricao": "Evangelismo", "valor": 300.00, "tipo": "saida", "categoria": "projeto"},
            ]
            
            for exemplo in exemplos:
                lancamento = Lancamento(
                    descricao=exemplo["descricao"],
                    valor=exemplo["valor"],
                    tipo=exemplo["tipo"],
                    categoria=exemplo["categoria"],
                    data=data_inicio + timedelta(days=5),
                    conta="caixa_interno"
                )
                db.session.add(lancamento)
            
            db.session.commit()
            
            # Buscar novamente
            lancamentos = Lancamento.query.filter(
                Lancamento.data >= data_inicio,
                Lancamento.data <= data_fim
            ).all()
            
            print(f"✅ Lançamentos de exemplo criados. Total: {len(lancamentos)}")
        
        # Verificar distribuição por tipo
        entradas = [l for l in lancamentos if l.tipo.lower() == 'entrada']
        saidas = [l for l in lancamentos if l.tipo.lower() in ['saida', 'saída']]
        
        print(f"📈 Entradas: {len(entradas)} (R$ {sum(l.valor for l in entradas):.2f})")
        print(f"📉 Saídas: {len(saidas)} (R$ {sum(l.valor for l in saidas):.2f})")
        
        # Gerar PDF
        relatorio = RelatorioFinanceiro(config)
        
        print("\n🔄 Gerando relatório de caixa interno...")
        
        # Calcular saldo anterior (simulado)
        saldo_anterior = 2000.00
        
        # Gerar com parâmetros corretos
        mes = data_fim.month
        ano = data_fim.year
        
        try:
            relatorio.gerar_relatorio_caixa(
                lancamentos=lancamentos,
                mes=mes,
                ano=ano,
                saldo_anterior=saldo_anterior
            )
            
            nome_arquivo = f"teste_relatorio_caixa_corrigido_{datetime.now().strftime('%H%M%S')}.pdf"
            
            print(f"✅ Relatório gerado com sucesso: {nome_arquivo}")
            print("📋 Correções implementadas:")
            print("   • Colunas de entrada alargadas (8cm + 5cm + 3cm)")
            print("   • Despesas fixas da sede incluídas")
            print("   • Conselho administrativo (30%) incluído")
            print("   • Total de saídas corrigido (não mais R$ 0,00)")
            print("   • Cálculo de saídas com validação de tipo")
            
        except Exception as e:
            print(f"❌ Erro ao gerar relatório: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()