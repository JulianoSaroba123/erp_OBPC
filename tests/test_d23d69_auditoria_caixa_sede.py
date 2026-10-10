import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "auditar_d23d69_caixa_sede.py"


class D23D69AuditoriaCaixaSedeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("d23d69_audit", SCRIPT)
        cls.mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(cls.mod)

    def test_todas_as_queries_sao_read_only(self):
        self.assertTrue(self.mod.READ_ONLY_SQL)
        for sql in self.mod.READ_ONLY_SQL:
            self.assertTrue(self.mod.is_readonly_sql(sql), sql[:80])

    def test_nao_existe_modo_apply_no_script(self):
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("--apply", src)
        self.assertNotIn("UPDATE lancamentos", src)
        self.assertNotIn("DELETE FROM", src)
        self.assertNotIn("INSERT INTO", src)

    def test_classificacao_preserva_outros_gastos_da_sede(self):
        self.assertEqual(
            self.mod.classify_candidate(
                {"observacoes": "Parcela 3/10 Fachada da Sede", "descricao": "Igreja"}
            ),
            "OUTRO_GASTO_SEDE_FACHADA",
        )
        self.assertEqual(
            self.mod.classify_candidate(
                {"observacoes": "Projeto Filipe e Força para Viver", "descricao": "Igreja"}
            ),
            "CANDIDATO_DESPESA_FIXA_SEDE",
        )

    def test_simulacao_e_identificada_como_teorica(self):
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("comparativo_mensal_simulacao_teorica", src)
        self.assertIn("Nao deve ser aplicada", src)


if __name__ == "__main__":
    unittest.main()
