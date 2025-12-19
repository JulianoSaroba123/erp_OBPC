from app import create_app
from app.financeiro.financeiro_model import Lancamento
from app.extensoes import db

app = create_app()

with app.app_context():
    print("=== Lançamentos Financeiros (inclui data nula) ===")
    todos = Lancamento.query.all()
    if not todos:
        print("Nenhum lançamento encontrado.")
    for l in todos:
        print(f"ID: {l.id} | Tipo: {l.tipo} | Valor: {l.valor} | Data: {l.data} | Categoria: {l.categoria} | Descrição: {l.descricao}")
        if not l.data:
            print("  -> ATENÇÃO: Data nula!")
    print(f"Total: {len(todos)} lançamentos.")
