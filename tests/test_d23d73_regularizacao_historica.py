import importlib.util
import pathlib
import unittest
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "regularizar_d23d73_caixa_sede.py"
ENVIO_MODEL = ROOT / "app" / "financeiro" / "envios_sede_model.py"
ROUTES = ROOT / "app" / "financeiro" / "financeiro_routes.py"


class D23D73RegularizacaoHistoricaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("d23d73_regularizacao", SCRIPT)
        cls.mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(cls.mod)

    def test_ponte_de_saldo_fecha(self):
        final = (
            self.mod.CURRENT_BALANCE
            + self.mod.EXPECTED_LEGACY_TOTAL
            - self.mod.EXPECTED_CASH_TOTAL
        )
        self.assertEqual(final, Decimal("1882.06"))
        self.assertEqual(final, self.mod.EXPECTED_FINAL_BALANCE)

    def test_total_legado_configurado_fecha(self):
        self.assertEqual(
            sum(self.mod.LEGACY.values(), Decimal("0.00")),
            Decimal("8718.15"),
        )
        self.assertEqual(len(self.mod.LEGACY), 30)

    def test_total_dinheiro_confirmado_fecha(self):
        self.assertEqual(
            sum(
                (item["valor"] for item in self.mod.CASH_ENVIOS.values()),
                Decimal("0.00"),
            ),
            Decimal("6416.41"),
        )
        for item in self.mod.CASH_ENVIOS.values():
            self.assertEqual(self.mod.CASH_DATE.isoformat(), "2026-07-04")

    def test_pix_confirmados(self):
        self.assertEqual(self.mod.PIX_ENVIOS[23]["importado_id"], 601)
        self.assertEqual(self.mod.PIX_ENVIOS[23]["valor"], Decimal("1000.00"))
        self.assertEqual(self.mod.PIX_ENVIOS[25]["importado_id"], 600)
        self.assertEqual(self.mod.PIX_ENVIOS[25]["valor"], Decimal("1426.00"))
        self.assertEqual(
            self.mod.PIX_ENVIOS[25]["valor_devido_competencia"],
            Decimal("1415.59"),
        )

    def test_apply_exige_confirmacao_explicita(self):
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("CONFIRM_TOKEN", src)
        self.assertIn("--confirm", src)
        self.assertIn("with engine.begin()", src)

    def test_controle_competencia_usa_somente_caixa_real(self):
        model_src = ENVIO_MODEL.read_text(encoding="utf-8")
        route_src = ROUTES.read_text(encoding="utf-8")
        self.assertIn("def somar_pagamentos_reais_mes", model_src)
        self.assertIn("tipo_pagamento == 'PAGAMENTO_BANCARIO'", model_src)
        self.assertIn("pagamento_historico_sem_movimentacao.is_(False)", model_src)
        self.assertIn("EnvioSede.somar_pagamentos_reais_mes", route_src)

    def test_apply_nao_roda_por_padrao(self):
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("return executar(url, bool(args.apply), args.confirm)", src)
        self.assertIn("if not apply:", src)


if __name__ == "__main__":
    unittest.main()
