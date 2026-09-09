import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "app" / "static" / "css"
WRAPPER = CSS / "obpc-design-system.css"
THEME = CSS / "obpc-app-theme.css"
LEGACY = CSS / "obpc-app-legacy.css"
AUTH = CSS / "obpc-auth-theme.css"
BASE = ROOT / "app" / "templates" / "base.html"
LOGIN_BASE = ROOT / "app" / "templates" / "login_base.html"


class D23D52GlobalThemeContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wrapper = WRAPPER.read_text(encoding="utf-8")
        cls.theme = THEME.read_text(encoding="utf-8")
        cls.legacy = LEGACY.read_text(encoding="utf-8")
        cls.auth = AUTH.read_text(encoding="utf-8")
        cls.base = BASE.read_text(encoding="utf-8")
        cls.login_base = LOGIN_BASE.read_text(encoding="utf-8")

    def test_global_theme_and_legacy_layer_are_loaded_last(self):
        imports = [line.strip() for line in self.wrapper.splitlines() if line.strip().startswith("@import")]
        self.assertGreaterEqual(len(imports), 4)
        self.assertIn("obpc-app-theme.css", imports[-2])
        self.assertIn("obpc-app-legacy.css", imports[-1])

    def test_base_loads_design_system(self):
        self.assertIn("css/obpc-design-system.css", self.base)

    def test_login_base_loads_auth_theme(self):
        self.assertIn("css/obpc-auth-theme.css", self.login_base)

    def test_theme_matches_dashboard_palette(self):
        for token in ("#0f172a", "#1d4ed8", "#0ea5e9", "#16a34a", "#ff6b35"):
            self.assertIn(token, self.theme)

    def test_theme_covers_legacy_cards(self):
        for selector in (".content .card", ".content .card-header", ".content .card-body"):
            self.assertIn(selector, self.theme)

    def test_theme_covers_forms_and_filters(self):
        for selector in (".content .form-control", ".content .form-select", ".content fieldset"):
            self.assertIn(selector, self.theme)

    def test_theme_covers_tables(self):
        self.assertIn(".content .table-responsive", self.theme)
        self.assertIn(".content .table thead th", self.theme)
        self.assertIn(".content .table tbody tr:hover", self.theme)

    def test_theme_covers_buttons(self):
        for selector in (".content .btn-primary", ".content .btn-success", ".content .btn-warning", ".content .btn-danger"):
            self.assertIn(selector, self.theme)

    def test_theme_covers_feedback_and_navigation(self):
        for selector in (".content .alert", ".content .badge", ".content .nav-tabs", ".content .pagination", ".modal-content"):
            self.assertIn(selector, self.theme)

    def test_topbar_is_aligned_to_dashboard(self):
        self.assertIn(".navbar-top", self.theme)
        self.assertIn("linear-gradient(90deg, #ffffff", self.theme)

    def test_semantic_kpi_cards_keep_their_colors(self):
        for selector in (
            ".content .card.bg-primary",
            ".content .card.bg-success",
            ".content .card.bg-danger",
            ".content .card.bg-warning",
            ".content .card.bg-info",
            ".content .card.bg-secondary",
        ):
            self.assertIn(selector, self.legacy)

    def test_colored_cards_keep_heading_contrast(self):
        self.assertIn(".content .card.bg-primary h1", self.legacy)
        self.assertIn("color: #fff !important", self.legacy)
        self.assertIn(".content .card.bg-warning h1", self.legacy)
        self.assertIn("color: #172033 !important", self.legacy)

    def test_auth_theme_matches_same_visual_language(self):
        for token in ("#0f172a", "#1d4ed8", "#0ea5e9", "#16a34a", "#ff6b35"):
            self.assertIn(token, self.auth)
        self.assertIn(".login-container", self.auth)
        self.assertIn(".cadastro-container", self.auth)
        self.assertIn(".login-card", self.auth)
        self.assertIn(".cadastro-card", self.auth)

    def test_mobile_and_reduced_motion_are_preserved(self):
        self.assertIn("@media (max-width: 768px)", self.theme)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.theme)
        self.assertIn("@media (max-width: 576px)", self.auth)

    def test_css_braces_are_balanced(self):
        self.assertEqual(self.theme.count("{"), self.theme.count("}"))
        self.assertEqual(self.legacy.count("{"), self.legacy.count("}"))
        self.assertEqual(self.auth.count("{"), self.auth.count("}"))

    def test_visual_layer_contains_no_business_or_database_mutation(self):
        forbidden = (
            "db.session",
            "UPDATE ",
            "INSERT ",
            "DELETE ",
            "ObrigacaoFinanceira",
            "Lancamento.query",
            "PagamentoObrigacao",
        )
        combined = self.wrapper + "\n" + self.theme + "\n" + self.legacy + "\n" + self.auth + "\n" + self.login_base
        for token in forbidden:
            self.assertNotIn(token, combined)


if __name__ == "__main__":
    unittest.main()
