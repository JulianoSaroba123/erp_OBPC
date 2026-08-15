from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from flask import Flask
from werkzeug.datastructures import MultiDict

from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento
from app.financeiro.obrigacoes_model import ObrigacaoFinanceira
from app.financeiro.despesas_fixas_model import DespesaFixaConselho
from app.financeiro.envios_sede_model import EnvioSede
from app.financeiro.financeiro_routes import financeiro_bp
import app.financeiro.financeiro_routes as routes


class QueryFake:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.filters = []

    def distinct(self):
        return self

    def filter(self, *criteria):
        self.filters.extend(criteria)
        return self

    def order_by(self, *args):
        return self

    def limit(self, _value):
        return self

    def all(self):
        return list(self.rows)


def _obrigacao_fake(obrigacao_id, status, valor_devido, valor_pendente):
    return SimpleNamespace(
        id=obrigacao_id,
        tipo_obrigacao="ADMIN_SEDE_30" if obrigacao_id == 101 else "DESPESA_FIXA",
        origem_obrigacao="automatico",
        descricao=f"Obrigacao {obrigacao_id}",
        valor_devido=Decimal(valor_devido),
        valor_pendente=Decimal(valor_pendente),
        status=status,
    )


class TestD23D17CompetenciaUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__)
        cls.app.config.update(
            TESTING=True,
            SECRET_KEY="test",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(cls.app)
        cls.app.register_blueprint(financeiro_bp)

    def test_get_usa_competencia_01_2026_e_exibe_obrigacoes(self):
        obrigacao_parcial = _obrigacao_fake(101, "PARCIAL", "1000.00", "250.00")
        obrigacao_pago = _obrigacao_fake(102, "PAGO", "500.00", "0.00")

        query_obrigacoes = QueryFake([obrigacao_parcial, obrigacao_pago])
        query_categorias = QueryFake([])
        query_envios = QueryFake([])
        captured = {}

        def query_side_effect(*args, **_kwargs):
            alvo = args[0]
            if alvo is ObrigacaoFinanceira:
                return query_obrigacoes
            if getattr(alvo, "key", None) == "categoria":
                return query_categorias
            raise AssertionError(f"Consulta inesperada: {alvo!r}")

        with self.app.test_request_context("/financeiro/despesas-fixas?mes=1&ano=2026"):
            with patch.object(routes, "_garantir_colunas_envio_sede_regularizacao"), \
                patch.object(DespesaFixaConselho, "query", QueryFake([])), \
                patch.object(DespesaFixaConselho, "obter_despesas_ativas", return_value=[]), \
                patch.object(DespesaFixaConselho, "obter_total_despesas_fixas", return_value=0), \
                patch.object(EnvioSede, "query", query_envios), \
                patch.object(routes.Configuracao, "obter_configuracao", return_value=SimpleNamespace(percentual_conselho=30)), \
                patch.object(routes, "_montar_controle_repasse_sede", return_value={
                    "saldo_pendente_anterior": 0,
                    "trinta_gerado_mes": 0,
                    "total_devido_mes": 0,
                    "valor_enviado_mes": 0,
                    "saldo_pendente_atual": 0,
                }), \
                patch.object(routes, "_obter_observacao_repasse_sede", return_value=("", "", False)), \
                patch.object(routes.db.session, "query", side_effect=query_side_effect), \
                patch.object(routes, "render_template", side_effect=lambda template, **ctx: captured.update({"template": template, "ctx": ctx}) or "OK"):
                resultado = routes.gerenciar_despesas_fixas.__wrapped__()

        self.assertEqual(resultado, "OK")
        self.assertEqual(captured["template"], "financeiro/gerenciar_despesas_fixas.html")
        self.assertEqual(captured["ctx"]["mes_ref"], 1)
        self.assertEqual(captured["ctx"]["ano_ref"], 2026)
        self.assertEqual(len(captured["ctx"]["obrigacoes_disponiveis"]), 2)
        self.assertTrue(any(item.status == "PARCIAL" and item.valor_pendente == Decimal("250.00") for item in captured["ctx"]["obrigacoes_disponiveis"]))
        self.assertTrue(any(item.status == "PAGO" and item.valor_pendente == Decimal("0.00") for item in captured["ctx"]["obrigacoes_disponiveis"]))

        filtros_compilados = [str(criterio.compile(compile_kwargs={"literal_binds": True})) for criterio in query_obrigacoes.filters]
        self.assertTrue(any("competencia_mes = 1" in criterio for criterio in filtros_compilados))
        self.assertTrue(any("competencia_ano = 2026" in criterio for criterio in filtros_compilados))
        self.assertTrue(any("status != 'CANCELADA'" in criterio or "status <> 'CANCELADA'" in criterio for criterio in filtros_compilados))

    def test_post_preserva_competencia_no_redirect(self):
        dados = MultiDict([
            ("acao", "registrar_pagamento_sede"),
            ("competencia_mes_ref", "1"),
            ("competencia_ano_ref", "2026"),
            ("competencia", "01/2026"),
            ("pagamento_historico_sem_movimentacao", "1"),
            ("alocacao_obrigacao_id[]", "101"),
            ("alocacao_valor[]", "250.00"),
        ])

        with self.app.test_request_context("/financeiro/despesas-fixas", method="POST", data=dados):
            with patch.object(routes, "_garantir_colunas_envio_sede_regularizacao"), \
                patch.object(routes, "registrar_repasse_sede_composto", return_value={"status": "criado"}), \
                patch.object(routes, "processar_upload_comprovante", return_value=None):
                resultado = routes.gerenciar_despesas_fixas.__wrapped__()

        self.assertEqual(resultado.status_code, 302)
        self.assertIn("mes=1", resultado.headers["Location"])
        self.assertIn("ano=2026", resultado.headers["Location"])


if __name__ == "__main__":
    unittest.main()