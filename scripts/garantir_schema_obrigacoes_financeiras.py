from flask import Flask

from app.config import Config
from app.extensoes import db
from sqlalchemy import inspect

from app.financeiro.obrigacoes_model import (
    ObrigacaoFinanceira,
    PagamentoObrigacao,
    PagamentoObrigacaoItem,
    ObrigacaoEvento,
)


TABELAS_NOVAS = [
    ObrigacaoFinanceira.__table__,
    PagamentoObrigacao.__table__,
    PagamentoObrigacaoItem.__table__,
    ObrigacaoEvento.__table__,
]


def garantir_schema_obrigacoes_financeiras():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        inspector = inspect(db.engine)
        existentes = set(inspector.get_table_names())

        criadas = []
        for tabela in TABELAS_NOVAS:
            if tabela.name not in existentes:
                tabela.create(bind=db.engine, checkfirst=True)
                criadas.append(tabela.name)

        print("=== SCHEMA OBRIGACOES FINANCEIRAS ===")
        if criadas:
            for nome in criadas:
                print(f"CRIADA: {nome}")
        else:
            print("NENHUMA ALTERACAO: tabelas já existem")


if __name__ == "__main__":
    garantir_schema_obrigacoes_financeiras()
