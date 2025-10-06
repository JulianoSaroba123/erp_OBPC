#!/usr/bin/env python3
"""
Script para testar os cálculos de saldo anterior
"""

from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento

def testar_saldo_anterior():
    """Testa os cálculos de saldo anterior para diferentes meses"""
    
    print("🧪 TESTANDO CÁLCULOS DE SALDO ANTERIOR")
    print("=" * 50)
    
    # Testar para diferentes meses
    meses_teste = [
        {"mes": 8, "ano": 2025, "nome": "Agosto 2025"},
        {"mes": 9, "ano": 2025, "nome": "Setembro 2025"},
        {"mes": 10, "ano": 2025, "nome": "Outubro 2025"},
        {"mes": 11, "ano": 2025, "nome": "Novembro 2025"},
        {"mes": 1, "ano": 2026, "nome": "Janeiro 2026"},
    ]
    
    for teste in meses_teste:
        print(f"\n📅 {teste['nome']}:")
        
        saldo_anterior = Lancamento.calcular_saldo_ate_mes_anterior(teste['mes'], teste['ano'])
        
        if teste['mes'] == 1:
            mes_ref = 12
            ano_ref = teste['ano'] - 1
        else:
            mes_ref = teste['mes'] - 1
            ano_ref = teste['ano']
        
        print(f"   💰 Saldo anterior (até {mes_ref:02d}/{ano_ref}): R$ {saldo_anterior:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        # Calcular totais do mês atual para verificação
        from sqlalchemy import extract
        
        lancamentos_mes = Lancamento.query.filter(
            extract('month', Lancamento.data) == teste['mes'],
            extract('year', Lancamento.data) == teste['ano']
        ).all()
        
        if lancamentos_mes:
            entradas_mes = sum([l.valor for l in lancamentos_mes if l.tipo == 'Entrada'])
            saidas_mes = sum([l.valor for l in lancamentos_mes if l.tipo == 'Saída'])
            saldo_mes = entradas_mes - saidas_mes
            saldo_acumulado = saldo_anterior + saldo_mes
            
            print(f"   📈 Entradas do mês: R$ {entradas_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            print(f"   📉 Saídas do mês: R$ {saidas_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            print(f"   💵 Saldo do mês: R$ {saldo_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            print(f"   🏆 Saldo acumulado: R$ {saldo_acumulado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        else:
            print(f"   ⚠️  Nenhum lançamento encontrado para este mês")
    
    print("\n" + "=" * 50)
    print("✅ Teste concluído!")

if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        testar_saldo_anterior()