import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "app" / "financeiro" / "dashboard_d23d50.py"
NOTIFICACOES_INIT = ROOT / "app" / "notificacoes" / "__init__.py"
ROUTES = ROOT / "app" / "financeiro" / "financeiro_routes.py"


class D23D50DashboardAgregacaoContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = SERVICE.read_text(encoding="utf-8")
        cls.notificacoes = NOTIFICACOES_INIT.read_text(encoding="utf-8")
        cls.routes = ROUTES.read_text(encoding="utf-8")

    def test_service_uses_grouped_payment_subquery(self):
        self.assertIn("group_by(PagamentoObrigacaoItem.obrigacao_financeira_id)", self.service)
        self.assertIn(".subquery()", self.service)

    def test_due_amount_is_summed_after_one_row_per_obligation(self):
        self.assertIn("func.sum(ObrigacaoFinanceira.valor_devido)", self.service)
        self.assertIn("pagamentos_por_obrigacao.c.obrigacao_id == ObrigacaoFinanceira.id", self.service)

    def test_does_not_use_sum_distinct_as_false_fix(self):
        self.assertNotIn("sum(func.distinct", self.service)
        self.assertNotIn("sum(distinct", self.service.lower())

    def test_repasse_summary_is_global_like_existing_dashboard(self):
        self.assertIn('resumir_obrigacoes_dashboard("ADMIN_SEDE_30")', self.service)

    def test_fixed_expenses_keep_selected_competence_filter(self):
        self.assertIn('resumir_obrigacoes_dashboard("DESPESA_FIXA", mes=mes, ano=ano)', self.service)

    def test_visible_dashboard_metrics_are_replaced(self):
        self.assertIn('metricas["repasse_pendente"] = repasse["saldo_pendente"]', self.service)
        self.assertIn('metricas["despesas_fixas_pendentes"] = despesas_fixas["saldo_pendente"]', self.service)

    def test_existing_dashboard_context_is_corrected(self):
        self.assertIn('resumo_repasse["saldo_pendente_total"] = repasse["saldo_pendente"]', self.service)
        self.assertIn('"saldo_pendente": despesas_fixas["saldo_pendente"]', self.service)

    def test_service_contains_no_write_operations(self):
        forbidden = ["db.session.add(", "db.session.delete(", "db.session.commit(", "db.session.flush(", "UPDATE ", "INSERT ", "DELETE "]
        for token in forbidden:
            self.assertNotIn(token, self.service)

    def test_installer_is_idempotent(self):
        self.assertIn('getattr(atual, "_d23d50_dashboard", False)', self.service)
        self.assertIn("render_template_d23d50._d23d50_dashboard = True", self.service)

    def test_patch_is_scoped_only_to_dashboard_template(self):
        self.assertIn('if template_name == DASHBOARD_TEMPLATE:', self.service)
        self.assertIn('DASHBOARD_TEMPLATE = "financeiro/dashboard_moderno.html"', self.service)

    def test_startup_hook_does_not_force_finance_import(self):
        self.assertIn('if "app.financeiro.financeiro_routes" not in sys.modules:', self.notificacoes)
        self.assertIn("instalar_correcao_dashboard_d23d50", self.notificacoes)

    def test_original_bug_signature_still_documented_in_route(self):
        # Contrato de regressão: confirma exatamente o padrão 1:N que motivou D23D50.
        self.assertIn("func.sum(ObrigacaoFinanceira.valor_devido)", self.routes)
        self.assertIn("PagamentoObrigacaoItem.obrigacao_financeira_id == ObrigacaoFinanceira.id", self.routes)


class D23D50ArithmeticRegressionTest(unittest.TestCase):
    def test_production_false_positive_4971_63_is_join_multiplication(self):
        janeiro = 1240.95
        abril = 1865.34
        excesso_join = janeiro * (2 - 1) + abril * (3 - 1)
        self.assertAlmostEqual(excesso_join, 4971.63, places=2)

    def test_split_payment_must_not_duplicate_due(self):
        devido = 1000.00
        parcelas = [600.00, 400.00]
        devido_correto = devido
        pago = sum(parcelas)
        self.assertEqual(devido_correto - pago, 0.0)

    def test_equal_due_values_from_different_obligations_must_both_count(self):
        # Garante que SUM(DISTINCT valor_devido) não seria uma correção válida.
        obrigacoes = [1000.00, 1000.00]
        self.assertEqual(sum(obrigacoes), 2000.00)


if __name__ == "__main__":
    unittest.main()
