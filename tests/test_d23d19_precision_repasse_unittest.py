from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import unittest

from flask import Flask

from app.config import Config
from app.extensoes import db
from app.financeiro.envios_sede_model import EnvioSede
from app.financeiro.financeiro_model import Lancamento
from app.financeiro.obrigacoes_model import ObrigacaoFinanceira, PagamentoObrigacao, PagamentoObrigacaoItem, ObrigacaoEvento
from app.financeiro.financeiro_routes import _montar_controle_repasse_sede


Q2 = Decimal("0.01")


def _q2(valor) -> Decimal:
    if isinstance(valor, Decimal):
        return valor.quantize(Q2, rounding=ROUND_HALF_UP)
    return Decimal(str(valor or 0)).quantize(Q2, rounding=ROUND_HALF_UP)


class TestD23D19PrecisionRepasse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__)
        cls.app.config.from_object(Config)
        cls.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(cls.app)

    def test_saldos_e_fluxo_julho_exatos(self):
        with self.app.app_context():
            controle_05 = _montar_controle_repasse_sede(5, 2026, 30)
            controle_06 = _montar_controle_repasse_sede(6, 2026, 30)
            controle_07 = _montar_controle_repasse_sede(7, 2026, 30)

        self.assertEqual(controle_05["saldo_pendente_atual"], Decimal("2357.39"))
        self.assertEqual(controle_06["saldo_pendente_atual"], Decimal("4760.70"))
        self.assertEqual(controle_07["saldo_pendente_atual"], Decimal("5883.26"))
        self.assertEqual(controle_07["valor_enviado_mes"], Decimal("3043.60"))
        self.assertEqual(controle_07["total_devido_mes"], Decimal("5883.26"))

    def test_leitura_nao_altera_persistencia(self):
        with self.app.app_context():
            snapshot_antes = {
                "TOTAL_LANCAMENTOS": db.session.query(Lancamento).count(),
                "TOTAL_ENVIOS_SEDE": db.session.query(EnvioSede).count(),
                "TOTAL_OBRIGACOES": db.session.query(ObrigacaoFinanceira).count(),
                "TOTAL_PAGAMENTOS": db.session.query(PagamentoObrigacao).count(),
                "TOTAL_ITENS": db.session.query(PagamentoObrigacaoItem).count(),
                "TOTAL_EVENTOS": db.session.query(ObrigacaoEvento).count(),
            }

            _montar_controle_repasse_sede(7, 2026, 30)

            snapshot_depois = {
                "TOTAL_LANCAMENTOS": db.session.query(Lancamento).count(),
                "TOTAL_ENVIOS_SEDE": db.session.query(EnvioSede).count(),
                "TOTAL_OBRIGACOES": db.session.query(ObrigacaoFinanceira).count(),
                "TOTAL_PAGAMENTOS": db.session.query(PagamentoObrigacao).count(),
                "TOTAL_ITENS": db.session.query(PagamentoObrigacaoItem).count(),
                "TOTAL_EVENTOS": db.session.query(ObrigacaoEvento).count(),
            }

        self.assertEqual(snapshot_antes, snapshot_depois)


if __name__ == "__main__":
    unittest.main()