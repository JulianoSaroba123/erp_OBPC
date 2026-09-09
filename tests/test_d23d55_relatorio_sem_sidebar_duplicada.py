import unittest
from pathlib import Path

from jinja2 import Environment, TemplateSyntaxError

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "app" / "financeiro" / "templates" / "financeiro" / "relatorio_workspace.html"


class D23D55RelatorioSemSidebarDuplicadaTest(unittest.TestCase):
    def test_workspace_nao_embute_aplicacao_em_iframe(self):
        src = WORKSPACE.read_text(encoding="utf-8")
        self.assertNotIn("<iframe", src)
        self.assertNotIn('class="report-preview-frame"', src)
        self.assertNotIn("Pré-visualização do documento", src)

    def test_pdf_sede_usa_rota_oficial_dedicada(self):
        src = WORKSPACE.read_text(encoding="utf-8")
        self.assertIn("financeiro.relatorio_sede_pdf", src)

    def test_pdf_gerencial_usa_rota_reportlab_dedicada(self):
        src = WORKSPACE.read_text(encoding="utf-8")
        self.assertIn("financeiro.relatorio_caixa_pdf", src)

    def test_workspace_mantem_shell_canonico(self):
        src = WORKSPACE.read_text(encoding="utf-8")
        self.assertIn('{% extends "base.html" %}', src)
        self.assertIn('class="obpc-page', src)
        self.assertIn('class="obpc-page-header"', src)
        self.assertIn('class="obpc-card"', src)

    def test_template_parseia(self):
        env = Environment()
        try:
            env.parse(WORKSPACE.read_text(encoding="utf-8-sig"))
        except TemplateSyntaxError as exc:
            self.fail(f"relatorio_workspace.html:{exc.lineno}: {exc.message}")


if __name__ == "__main__":
    unittest.main()
