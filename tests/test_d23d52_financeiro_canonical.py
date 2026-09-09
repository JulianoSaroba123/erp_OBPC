import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEMBROS = ROOT / "app" / "membros" / "templates" / "membros" / "lista_membros.html"
FINANCEIRO = ROOT / "app" / "financeiro" / "templates" / "financeiro" / "lista_lancamentos.html"


class D23D52FinanceiroCanonicalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.membros = MEMBROS.read_text(encoding="utf-8-sig")
        cls.financeiro = FINANCEIRO.read_text(encoding="utf-8-sig")

    def test_financeiro_uses_same_page_shell_as_membros(self):
        for token in ("obpc-page", "obpc-page-header", "obpc-page-title", "obpc-page-actions"):
            self.assertIn(token, self.membros)
            self.assertIn(token, self.financeiro)

    def test_financeiro_uses_same_white_kpi_component(self):
        self.assertIn("obpc-ops", self.membros)
        self.assertGreaterEqual(self.financeiro.count("obpc-ops"), 7)
        self.assertNotIn("card bg-primary", self.financeiro)
        self.assertNotIn("card bg-success", self.financeiro)
        self.assertNotIn("card bg-danger", self.financeiro)
        self.assertNotIn("card bg-warning", self.financeiro)

    def test_financeiro_filters_follow_canonical_component(self):
        for token in ("obpc-card", "obpc-filter-bar", "obpc-field", "obpc-label", "obpc-input", "obpc-select"):
            self.assertIn(token, self.financeiro)

    def test_financeiro_tables_follow_canonical_component(self):
        self.assertIn("obpc-table-wrap", self.financeiro)
        self.assertIn("obpc-table", self.financeiro)
        self.assertIn("obpc-table-actions", self.financeiro)
        self.assertNotIn("table-dark", self.financeiro)

    def test_financeiro_preserves_business_actions(self):
        for endpoint in (
            "financeiro.novo_lancamento",
            "financeiro.importar_extrato",
            "financeiro.conciliacao",
            "financeiro.editar_lancamento",
            "financeiro.excluir_lancamento",
            "financeiro.relatorio_sede",
        ):
            self.assertIn(endpoint, self.financeiro)

    def test_financeiro_preserves_filter_fields(self):
        for field in (
            'name="categoria"', 'name="tipo"', 'name="conta"', 'name="busca_texto"',
            'name="mes_ref"', 'name="ano_ref"', 'name="data_inicial"', 'name="data_final"',
            'name="valor_min"', 'name="valor_max"'
        ):
            self.assertIn(field, self.financeiro)

    def test_financeiro_keeps_no_data_mutation_in_template(self):
        for token in ("db.session", "UPDATE ", "INSERT ", "DELETE FROM", "commit("):
            self.assertNotIn(token, self.financeiro)


if __name__ == "__main__":
    unittest.main()
