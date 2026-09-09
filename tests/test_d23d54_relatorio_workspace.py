import unittest
from pathlib import Path

from jinja2 import Environment, TemplateSyntaxError

from app.financeiro.relatorio_workspace_d23d54 import REPORT_TEMPLATES, WORKSPACE_TEMPLATE


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "app" / "financeiro" / "templates" / "financeiro" / "relatorio_workspace.html"
ADAPTER = ROOT / "app" / "financeiro" / "relatorio_workspace_d23d54.py"
NOTIFICACOES = ROOT / "app" / "notificacoes" / "__init__.py"


class D23D54RelatorioWorkspaceTest(unittest.TestCase):
    def test_workspace_usa_shell_canonico_do_erp(self):
        src = WORKSPACE.read_text(encoding="utf-8")
        self.assertIn('{% extends "base.html" %}', src)
        for token in (
            'class="obpc-page',
            'class="obpc-page-header"',
            'class="obpc-page-title"',
            'class="obpc-page-actions"',
            'class="obpc-card"',
            'class="obpc-section"',
        ):
            self.assertIn(token, src)

    def test_workspace_cobre_tres_publicos(self):
        src = WORKSPACE.read_text(encoding="utf-8")
        for valor in ('value="gerencial"', 'value="sede"', 'value="auditoria"'):
            self.assertIn(valor, src)
        self.assertIn("Relatório Oficial para a Sede", src)
        self.assertIn("Relatório de Auditoria", src)

    def test_workspace_preview_usa_pdf_oficial_existente(self):
        src = WORKSPACE.read_text(encoding="utf-8")
        self.assertIn("financeiro.relatorio_pdf", src)
        self.assertIn('class="report-preview-frame"', src)
        self.assertIn("Pré-visualização do documento", src)

    def test_justificativa_sede_permanece_disponivel(self):
        src = WORKSPACE.read_text(encoding="utf-8")
        self.assertIn("tipo_relatorio == 'sede'", src)
        self.assertIn("financeiro.salvar_justificativa_relatorio", src)
        self.assertIn('name="observacao_repasse_sede"', src)
        self.assertIn('name="acao" value="salvar"', src)
        self.assertIn('name="acao" value="restaurar"', src)

    def test_workspace_e_responsivo_sem_container_central_fixo(self):
        src = WORKSPACE.read_text(encoding="utf-8")
        self.assertIn("width: 100%; max-width: none", src)
        self.assertIn("@media (max-width: 980px)", src)
        self.assertNotIn("width: min(1160px", src)

    def test_adapter_intercepta_apenas_tela_web(self):
        src = ADAPTER.read_text(encoding="utf-8")
        self.assertEqual(3, len(REPORT_TEMPLATES))
        self.assertEqual("financeiro/relatorio_workspace.html", WORKSPACE_TEMPLATE)
        self.assertIn('not contexto.get("modo_pdf", False)', src)
        self.assertIn("report_template_original", src)
        for template in REPORT_TEMPLATES:
            self.assertIn(template, src)

    def test_adapter_nao_escreve_no_banco(self):
        src = ADAPTER.read_text(encoding="utf-8")
        for token in (
            "db.session.add",
            "db.session.commit",
            "db.session.delete",
            "UPDATE ",
            "INSERT ",
            "DELETE FROM",
            "ALTER TABLE",
        ):
            self.assertNotIn(token, src)

    def test_instalacao_d23d54_esta_encadeada(self):
        src = NOTIFICACOES.read_text(encoding="utf-8")
        self.assertIn("instalar_workspace_relatorios_d23d54", src)
        self.assertIn("D23D54", src)

    def test_template_parseia(self):
        env = Environment()
        try:
            env.parse(WORKSPACE.read_text(encoding="utf-8-sig"))
        except TemplateSyntaxError as exc:
            self.fail(f"relatorio_workspace.html:{exc.lineno}: {exc.message}")


if __name__ == "__main__":
    unittest.main()
