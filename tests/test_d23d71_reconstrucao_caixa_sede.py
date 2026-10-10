import importlib.util
import pathlib
import unittest
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "reconstruir_d23d71_caixa_sede.py"


class D23D71ReconstrucaoCaixaSedeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("d23d71_reconstrucao", SCRIPT)
        cls.mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(cls.mod)

    def test_todas_as_queries_sao_read_only(self):
        self.assertTrue(self.mod.READ_ONLY_SQL)
        for sql in self.mod.READ_ONLY_SQL:
            self.assertTrue(self.mod.is_readonly_sql(sql), sql[:120])

    def test_script_nao_tem_apply_nem_escrita(self):
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("--apply", src)
        self.assertNotIn("INSERT INTO", src)
        self.assertNotIn("UPDATE lancamentos", src)
        self.assertNotIn("DELETE FROM", src)

    def test_total_pagamentos_dinheiro_sem_lancamento(self):
        total = sum(
            (item["valor"] for item in self.mod.UNPOSTED_CASH_PAYMENTS),
            Decimal("0.00"),
        )
        self.assertEqual(total, Decimal("6416.41"))

    def test_saldo_reconstruido_fecha(self):
        saldo = (
            self.mod.EXPECTED_CURRENT_BALANCE
            + self.mod.EXPECTED_LEGACY_TOTAL
            - self.mod.EXPECTED_UNPOSTED_CASH_TOTAL
        )
        self.assertEqual(saldo, Decimal("1882.06"))

    def test_pix_reais_nao_viram_nova_saida(self):
        self.assertEqual(
            self.mod.CONFIRMED_BANK_PAYMENTS[601]["valor"],
            Decimal("1000.00"),
        )
        self.assertEqual(
            self.mod.CONFIRMED_BANK_PAYMENTS[600]["valor"],
            Decimal("1426.00"),
        )

    def test_maio_sem_projeto_filipe(self):
        self.assertEqual(
            self.mod.MAY_DUE_WITHOUT_PROJETO_FILIPE,
            Decimal("1415.59"),
        )
        self.assertEqual(
            self.mod.MAY_UNALLOCATED_CREDIT,
            Decimal("10.41"),
        )


if __name__ == "__main__":
    unittest.main()
