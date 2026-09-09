import unittest
from pathlib import Path

from jinja2 import Environment, TemplateSyntaxError

ROOT = Path(__file__).resolve().parents[1]
TOOLBAR = ROOT / "app" / "financeiro" / "templates" / "financeiro" / "_relatorio_toolbar.html"
NOTIFICACOES = ROOT / "app" / "notificacoes" / "__init__.py"
FINANCEIRO = ROOT / "app" / "financeiro"
TEMPLATES = FINANCEIRO / "templates" / "financeiro"


class D23D56RelatorioFluxoOriginalVisualTest(unittest.TestCase):
    def test_workspace_substituto_foi_aposentado(self):
        self.assertFalse((FINANCEIRO / "relatorio_workspace_d23d54.py").exists())
        self.assertFalse((TEMPLATES / "relatorio_workspace.html").exists())

    def test_notificacoes_mantem_apenas_adaptadores_financeiros_necessarios(self):
        src = NOTIFICACOES.read_text(encoding="utf-8")
        self.assertIn("instalar_correcao_dashboard_d23d50", src)
        self.assertIn("instalar_correcao_relatorio_sede_d23d53", src)
        self.assertNotIn("relatorio_workspace_d23d54", src)
        self.assertNotIn("instalar_workspace_relatorios_d23d54", src)

    def test_toolbar_preserva_fluxo_original(self):
        src = TOOLBAR.read_text(encoding="utf-8")
        for token in (
            "financeiro.gerar_relatorio",
            "financeiro.relatorio_pdf",
            "financeiro.salvar_justificativa_relatorio",
            "financeiro.lista_lancamentos",
            'name="tipo_relatorio"',
            'name="mes"',
            'name="ano"',
            'name="acao" value="salvar"',
            'name="acao" value="restaurar"',
        ):
            self.assertIn(token, src)

    def test_toolbar_e_apenas_visual_sem_iframe_ou_scroll_lock(self):
        src = TOOLBAR.read_text(encoding="utf-8")
        self.assertNotIn("<iframe", src)
        self.assertNotIn("position: fixed", src)
        self.assertNotIn("height: 100vh", src)
        self.assertNotIn("overflow-y: hidden", src)
        self.assertIn("overflow: visible", src)
        self.assertIn("max-width: 1480px", src)
        self.assertIn("D23D56: somente apresentação", src)

    def test_templates_originais_continuam_com_estrutura_propria(self):
        esperados = {
            "relatorio_gerencial.html": 'class="hero"',
            "relatorio_sede.html": 'class="document"',
            "relatorio_auditoria.html": 'class="document"',
        }
        for nome, token_estrutura in esperados.items():
            src = (TEMPLATES / nome).read_text(encoding="utf-8-sig")
            self.assertIn("_relatorio_toolbar.html", src)
            self.assertIn(token_estrutura, src)

    def test_toolbar_parseia(self):
        env = Environment()
        try:
            env.parse(TOOLBAR.read_text(encoding="utf-8-sig"))
        except TemplateSyntaxError as exc:
            self.fail(f"_relatorio_toolbar.html:{exc.lineno}: {exc.message}")


if __name__ == "__main__":
    unittest.main()
