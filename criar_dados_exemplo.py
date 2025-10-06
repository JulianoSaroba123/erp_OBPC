#!/usr/bin/env python3
"""
Script para criar dados de exemplo para os relatórios financeiros
"""

from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento
from datetime import date, datetime
import random

def criar_dados_exemplo():
    """Cria lançamentos de exemplo para outubro/2025"""
    
    # Lista de dízimos
    dizimos = [
        {"descricao": "Dízimo - João Silva", "categoria": "Dízimo", "valor": 350.00, "conta": "Banco"},
        {"descricao": "Dízimo - Maria Santos", "categoria": "Dízimo", "valor": 250.00, "conta": "Dinheiro"},
        {"descricao": "Dízimo - Pedro Oliveira", "categoria": "Dízimo", "valor": 180.00, "conta": "Pix"},
        {"descricao": "Dízimo - Ana Costa", "categoria": "Dízimo", "valor": 420.00, "conta": "Banco"},
        {"descricao": "Dízimo - Carlos Ferreira", "categoria": "Dízimo", "valor": 150.00, "conta": "Dinheiro"},
    ]
    
    # Lista de ofertas
    ofertas = [
        {"descricao": "Oferta Alçada - Domingo", "categoria": "Oferta Alçada", "valor": 280.00, "conta": "Dinheiro"},
        {"descricao": "Oferta Especial - Missões", "categoria": "Oferta", "valor": 150.00, "conta": "Banco"},
        {"descricao": "Oferta da Juventude", "categoria": "Oferta", "valor": 85.00, "conta": "Pix"},
        {"descricao": "Oferta Alçada - Quarta", "categoria": "Oferta Alçada", "valor": 120.00, "conta": "Dinheiro"},
        {"descricao": "Oferta de Gratidão", "categoria": "Oferta", "valor": 200.00, "conta": "Banco"},
    ]
    
    # Lista de saídas
    saidas = [
        {"descricao": "Conta de Luz", "categoria": "Despesa Operacional", "valor": 180.00, "conta": "Banco"},
        {"descricao": "Água e Esgoto", "categoria": "Despesa Operacional", "valor": 85.00, "conta": "Banco"},
        {"descricao": "Material de Limpeza", "categoria": "Manutenção", "valor": 65.00, "conta": "Dinheiro"},
        {"descricao": "Taxa Bancária", "categoria": "Desconto", "valor": 15.00, "conta": "Banco"},
        {"descricao": "Combustível", "categoria": "Transporte", "valor": 120.00, "conta": "Dinheiro"},
        {"descricao": "Manutenção - Ar Condicionado", "categoria": "Manutenção", "valor": 250.00, "conta": "Banco"},
    ]
    
    print("🔄 Criando dados de exemplo...")
    
    # Criar dízimos
    for i, dizimo in enumerate(dizimos, 1):
        lancamento = Lancamento(
            data=date(2025, 10, i * 3),  # Dias 3, 6, 9, 12, 15
            tipo="Entrada",
            categoria=dizimo["categoria"],
            descricao=dizimo["descricao"],
            valor=dizimo["valor"],
            conta=dizimo["conta"],
            observacoes=f"Lançamento automático - {dizimo['categoria']}"
        )
        db.session.add(lancamento)
    
    # Criar ofertas
    for i, oferta in enumerate(ofertas, 1):
        lancamento = Lancamento(
            data=date(2025, 10, i * 4 + 1),  # Dias 5, 9, 13, 17, 21
            tipo="Entrada",
            categoria=oferta["categoria"],
            descricao=oferta["descricao"],
            valor=oferta["valor"],
            conta=oferta["conta"],
            observacoes=f"Lançamento automático - {oferta['categoria']}"
        )
        db.session.add(lancamento)
    
    # Criar saídas
    for i, saida in enumerate(saidas, 1):
        lancamento = Lancamento(
            data=date(2025, 10, i * 4 + 2),  # Dias 6, 10, 14, 18, 22, 26
            tipo="Saída",
            categoria=saida["categoria"],
            descricao=saida["descricao"],
            valor=saida["valor"],
            conta=saida["conta"],
            observacoes=f"Lançamento automático - {saida['categoria']}"
        )
        db.session.add(lancamento)
    
    try:
        db.session.commit()
        print("✅ Dados de exemplo criados com sucesso!")
        
        # Mostrar resumo
        entradas = sum([d["valor"] for d in dizimos]) + sum([o["valor"] for o in ofertas])
        saidas_total = sum([s["valor"] for s in saidas])
        saldo = entradas - saidas_total
        
        print(f"\n📊 Resumo dos dados criados:")
        print(f"💰 Total de Entradas: R$ {entradas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        print(f"💸 Total de Saídas: R$ {saidas_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        print(f"📈 Saldo do Mês: R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        print(f"📅 Registros criados para: Outubro/2025")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao criar dados: {str(e)}")

if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        print("🚀 Iniciando criação de dados de exemplo...")
        criar_dados_exemplo()
        print("🎉 Processo concluído!")