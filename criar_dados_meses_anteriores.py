#!/usr/bin/env python3
"""
Script para criar dados de exemplo de meses anteriores para testar o saldo anterior
"""

from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento
from datetime import date

def criar_dados_meses_anteriores():
    """Cria lançamentos de exemplo para agosto e setembro/2025"""
    
    print("🔄 Criando dados de meses anteriores...")
    
    # Dados de AGOSTO 2025
    agosto_dados = [
        # Entradas Agosto
        {"data": date(2025, 8, 5), "tipo": "Entrada", "categoria": "Dízimo", "descricao": "Dízimo - João Silva", "valor": 300.00, "conta": "Banco"},
        {"data": date(2025, 8, 8), "tipo": "Entrada", "categoria": "Dízimo", "descricao": "Dízimo - Maria Santos", "valor": 200.00, "conta": "Dinheiro"},
        {"data": date(2025, 8, 12), "tipo": "Entrada", "categoria": "Oferta", "descricao": "Oferta Especial", "valor": 150.00, "conta": "Pix"},
        {"data": date(2025, 8, 15), "tipo": "Entrada", "categoria": "Oferta Alçada", "descricao": "Oferta Domingo", "valor": 180.00, "conta": "Dinheiro"},
        
        # Saídas Agosto
        {"data": date(2025, 8, 10), "tipo": "Saída", "categoria": "Despesa Operacional", "descricao": "Conta de Luz", "valor": 120.00, "conta": "Banco"},
        {"data": date(2025, 8, 20), "tipo": "Saída", "categoria": "Manutenção", "descricao": "Material de Limpeza", "valor": 45.00, "conta": "Dinheiro"},
    ]
    
    # Dados de SETEMBRO 2025
    setembro_dados = [
        # Entradas Setembro
        {"data": date(2025, 9, 3), "tipo": "Entrada", "categoria": "Dízimo", "descricao": "Dízimo - Pedro Oliveira", "valor": 280.00, "conta": "Banco"},
        {"data": date(2025, 9, 7), "tipo": "Entrada", "categoria": "Dízimo", "descricao": "Dízimo - Ana Costa", "valor": 320.00, "conta": "Pix"},
        {"data": date(2025, 9, 10), "tipo": "Entrada", "categoria": "Oferta", "descricao": "Oferta da Juventude", "valor": 95.00, "conta": "Dinheiro"},
        {"data": date(2025, 9, 14), "tipo": "Entrada", "categoria": "Oferta Alçada", "descricao": "Oferta Quarta", "valor": 140.00, "conta": "Banco"},
        {"data": date(2025, 9, 21), "tipo": "Entrada", "categoria": "Oferta", "descricao": "Oferta de Gratidão", "valor": 110.00, "conta": "Pix"},
        
        # Saídas Setembro
        {"data": date(2025, 9, 8), "tipo": "Saída", "categoria": "Despesa Operacional", "descricao": "Água e Esgoto", "valor": 75.00, "conta": "Banco"},
        {"data": date(2025, 9, 15), "tipo": "Saída", "categoria": "Transporte", "descricao": "Combustível", "valor": 100.00, "conta": "Dinheiro"},
        {"data": date(2025, 9, 25), "tipo": "Saída", "categoria": "Desconto", "descricao": "Taxa Bancária", "valor": 12.00, "conta": "Banco"},
    ]
    
    # Criar lançamentos de agosto
    for dados in agosto_dados:
        lancamento = Lancamento(
            data=dados["data"],
            tipo=dados["tipo"],
            categoria=dados["categoria"],
            descricao=dados["descricao"],
            valor=dados["valor"],
            conta=dados["conta"],
            observacoes=f"Dados de exemplo - {dados['data'].strftime('%B/%Y')}"
        )
        db.session.add(lancamento)
    
    # Criar lançamentos de setembro
    for dados in setembro_dados:
        lancamento = Lancamento(
            data=dados["data"],
            tipo=dados["tipo"],
            categoria=dados["categoria"],
            descricao=dados["descricao"],
            valor=dados["valor"],
            conta=dados["conta"],
            observacoes=f"Dados de exemplo - {dados['data'].strftime('%B/%Y')}"
        )
        db.session.add(lancamento)
    
    try:
        db.session.commit()
        print("✅ Dados de meses anteriores criados com sucesso!")
        
        # Calcular totais por mês
        agosto_entradas = sum([d["valor"] for d in agosto_dados if d["tipo"] == "Entrada"])
        agosto_saidas = sum([d["valor"] for d in agosto_dados if d["tipo"] == "Saída"])
        agosto_saldo = agosto_entradas - agosto_saidas
        
        setembro_entradas = sum([d["valor"] for d in setembro_dados if d["tipo"] == "Entrada"])
        setembro_saidas = sum([d["valor"] for d in setembro_dados if d["tipo"] == "Saída"])
        setembro_saldo = setembro_entradas - setembro_saidas
        
        saldo_acumulado = agosto_saldo + setembro_saldo
        
        print(f"\n📊 Resumo dos dados criados:")
        print(f"📅 AGOSTO 2025:")
        print(f"   💰 Entradas: R$ {agosto_entradas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        print(f"   💸 Saídas: R$ {agosto_saidas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        print(f"   📈 Saldo: R$ {agosto_saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        print(f"\n📅 SETEMBRO 2025:")
        print(f"   💰 Entradas: R$ {setembro_entradas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        print(f"   💸 Saídas: R$ {setembro_saidas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        print(f"   📈 Saldo: R$ {setembro_saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        print(f"\n💰 SALDO ACUMULADO ATÉ SETEMBRO: R$ {saldo_acumulado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        print("   (Este será o saldo anterior para OUTUBRO)")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao criar dados: {str(e)}")

if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        print("🚀 Iniciando criação de dados de meses anteriores...")
        criar_dados_meses_anteriores()
        print("🎉 Processo concluído!")