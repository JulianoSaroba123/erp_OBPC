"""Listar TODOS os lançamentos com 'oferta' na categoria"""
from app import create_app, db
from app.financeiro.financeiro_model import Lancamento
from sqlalchemy import extract

app = create_app()

with app.app_context():
    # Buscar entradas de janeiro/2026  com 'oferta' na categoria
    lancamentos = Lancamento.query.filter(
        extract('month', Lancamento.data) == 1,
        extract('year', Lancamento.data) == 2026,
        Lancamento.tipo == 'Entrada',
        Lancamento.categoria.ilike('%oferta%')
    ).order_by(Lancamento.categoria, Lancamento.id).all()
    
    print("\n" + "="*140)
    print(f"TODOS OS LANÇAMENTOS COM 'OFERTA' NA CATEGORIA - JANEIRO/2026 (Total: {len(lancamentos)} lançamentos)")
    print("="*140)
    
    # Agrupar por categoria
    categorias = {}
    
    for lanc in lancamentos:
        cat = lanc.categoria or 'SEM CATEGORIA'
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append(lanc)
    
    # Mostrar agrupado
    for categoria in sorted(categorias.keys()):
        lancamentos_cat = categorias[categoria]
        total_banco = sum(l.valor for l in lancamentos_cat if 'banco' in (l.conta or '').lower() or 'pix' in (l.conta or '').lower())
        total_dinheiro = sum(l.valor for l in lancamentos_cat if 'banco' not in (l.conta or '').lower() and 'pix' not in (l.conta or '').lower())
        
        print(f"\n📌 CATEGORIA: {categoria}")
        print(f"   Total Banco: R$ {total_banco:.2f} | Total Dinheiro: R$ {total_dinheiro:.2f}")
        print("   " + "-"*135)
        
        for lanc in lancamentos_cat:
            conta = lanc.conta or 'Não informado'
            valor = lanc.valor or 0
            print(f"   ID: {lanc.id:4d} | Data: {lanc.data.strftime('%d/%m/%Y')} | Conta: {conta:15s} | Valor: R$ {valor:9.2f}")
    
    print("\n" + "="*140)
    print("RESUMO GERAL:")
    print("="*140)
    
    total_geral = sum(l.valor or 0 for l in lancamentos)
    total_banco_geral = sum(l.valor or 0 for l in lancamentos if 'banco' in (l.conta or '').lower() or 'pix' in (l.conta or '').lower())
    total_dinheiro_geral = sum(l.valor or 0 for l in lancamentos if 'banco' not in (l.conta or '').lower() and 'pix' not in (l.conta or '').lower())
    
    print(f"Total de lançamentos: {len(lancamentos)}")
    print(f"Total Banco: R$ {total_banco_geral:.2f}")
    print(f"Total Dinheiro: R$ {total_dinheiro_geral:.2f}")
    print(f"TOTAL GERAL: R$ {total_geral:.2f}\n")
