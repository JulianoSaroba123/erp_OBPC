import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS_DIR = ROOT / "app" / "static" / "css"
WRAPPER = CSS_DIR / "obpc-design-system.css"
CORE = CSS_DIR / "obpc-design-system-core.css"
SIDEBAR = CSS_DIR / "obpc-sidebar-dashboard.css"


class D23D51SidebarPremiumContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wrapper = WRAPPER.read_text(encoding="utf-8")
        cls.sidebar = SIDEBAR.read_text(encoding="utf-8")

    def test_wrapper_keeps_core_and_sidebar_separated(self):
        self.assertIn('obpc-design-system-core.css', self.wrapper)
        self.assertIn('obpc-sidebar-dashboard.css', self.wrapper)
        self.assertTrue(CORE.exists())

    def test_sidebar_uses_dashboard_palette(self):
        for token in ("#0f172a", "#1d4ed8", "#0ea5e9"):
            self.assertIn(token, self.sidebar)

    def test_green_is_supporting_institutional_accent(self):
        self.assertIn("--obpc-sidebar-green: #16a34a", self.sidebar)
        self.assertIn("var(--obpc-sidebar-green)", self.sidebar)

    def test_active_item_preserves_obpc_orange_focus(self):
        self.assertIn("--obpc-sidebar-orange: #ff6b35", self.sidebar)
        self.assertIn("var(--obpc-sidebar-orange)", self.sidebar)

    def test_sidebar_keeps_submenus_and_expanded_state(self):
        self.assertIn(".sidebar .submenu", self.sidebar)
        self.assertIn('[aria-expanded="true"]', self.sidebar)
        self.assertIn(".submenu-arrow", self.sidebar)

    def test_collapsed_mode_is_preserved(self):
        self.assertIn(".sidebar.collapsed .logo", self.sidebar)
        self.assertIn(".sidebar-toggle.collapsed", self.sidebar)

    def test_mobile_mode_is_preserved(self):
        self.assertIn("@media (max-width: 768px)", self.sidebar)
        self.assertIn(".mobile-toggle", self.sidebar)

    def test_focus_visible_is_available(self):
        self.assertIn(":focus-visible", self.sidebar)

    def test_panel_does_not_compete_with_active_submenu(self):
        self.assertIn(":has(.submenu-item.active)", self.sidebar)

    def test_visual_layer_contains_no_data_or_financial_mutations(self):
        forbidden = (
            "db.session",
            "UPDATE ",
            "INSERT ",
            "DELETE ",
            "ObrigacaoFinanceira",
            "Lancamento.query",
        )
        combined = self.wrapper + "\n" + self.sidebar
        for token in forbidden:
            self.assertNotIn(token, combined)

    def test_css_braces_are_balanced(self):
        self.assertEqual(self.sidebar.count("{"), self.sidebar.count("}"))


if __name__ == "__main__":
    unittest.main()
