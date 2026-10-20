import importlib.util
import pathlib
import unittest
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "regularizar_d23d76_teste_613.py"


class D23D76NeutralizaTeste613Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("d23d76", SCRIPT)
        cls.mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(cls.mod)

    def test_alvo_exato(self):
        self.assertEqual(self.mod.TARGET_ID, 613)
        self.assertEqual(self.mod.EXPECTED_VALUE, Decimal("295.34"))
        self.assertEqual(self.mod.EXPECTED_DATE, "2026-07-31")

    def test_saldos_esperados(self):
        self.assertEqual(self.mod.EXPECTED_CURRENT_AUG_BALANCE, Decimal("1882.06"))
        self.assertEqual(self.mod.EXPECTED_FINAL_AUG_BALANCE, Decimal("2177.40"))
        self.assertEqual(self.mod.EXPECTED_JULY_OUTFLOWS, Decimal("12571.97"))
        self.assertEqual(self.mod.EXPECTED_JULY_ACCUMULATED, Decimal("3429.32"))

    def test_apply_preserva_registro_como_evidencia(self):
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("SET tipo='Evidência'", src)
        self.assertNotIn("DELETE FROM lancamentos", src)
        self.assertIn("D23D76_NEUTRALIZA_TESTE_613", src)

    def test_apply_exige_token_e_lock(self):
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("CONFIRMO_D23D76_TESTE_613", src)
        self.assertIn("pg_advisory_xact_lock(237376)", src)
        self.assertIn("with engine.begin()", src)


if __name__ == "__main__":
    unittest.main()
