import unittest
from pathlib import Path
from unittest.mock import patch

from jinja2 import Environment, TemplateSyntaxError

from app.financeiro.relatorio_sede_d23d53 import (
    RELATORIO_SEDE_TEMPLATE,
    classificar_despesas_fixas_d23d53,
    corrigir_contexto_relatorio_sede_d23d53,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "app" / "financeiro" / "templates" / "financeiro"
TOOLBAR = TEMPLATES / "_relatorio_toolbar.html"
RELATORIO_SEDE = TEMPLATES / "relatorio_sede.html"
ADAPTER = ROOT / "app" / "financeiro" / "relatorio_sede_d23d53.py"


class D23D53RelatorioSedeTest(unittest.TestCase):
    def test_classifica_despesas_fixas_julho_2026(self):
        fixas = classificar_despesas_fixas_d23d53(
            [
                {"nome": "Contador", "valor": 100.00},
                {"nome": "Força para Viver", "valor": 50.00},
                {"nome": "Projeto Filipe", "valor": 10.00},
                {"nome": "Site", "valor": 20.00},
            ]
        )
        self.assertEqual(fixas["contador_sede"], 100.0)
        self.assertEqual(fixas["forca_para_viver"], 50.0)
        self.assertEqual(fixas["projeto_filipe"], 10.0)
        self.assertEqual(fixas["site"], 20.0)
        self.assertEqual(sum(fixas.values()), 180.0)

    def test_contexto_relatorio_recebe_valores_e_total_da_competencia(self):
        contexto = {
            "mes": 7,
            "ano": 2026,
            "envios": {
                "contador_sede": 0.0,
                "site": 0.0,
                "projeto_filipe": 0.0,
                "forca_para_viver": 0.0,
                "oferta_voluntaria_conchas": 0.0,
            },
            "despesas_fixas_lista": [],
            "totais_sede": {
                "valor_conselho": 1122.56,
                "despesas_fixas": 0.0,
                "total_envio_sede": 1122.56,
            },
        }
        itens = [
            {"nome": "Contador", "valor": 100},
            {"nome": "Força para Viver", "valor": 50},
            {"nome": "Projeto Filipe", "valor": 10},
            {"nome": "Site", "valor": 20},
        ]
        with patch("app.financeiro.relatorio_sede_d23d53._itens_obrigacoes_competencia", return_value=itens):
            corrigir_contexto_relatorio_sede_d23d53(contexto)

        self.assertEqual(contexto["envios"]["contador_sede"], 100.0)
        self.assertEqual(contexto["envios"]["site"], 20.0)
        self.assertEqual(contexto["envios"]["projeto_filipe"], 10.0)
        self.assertEqual(contexto["envios"]["forca_para_viver"], 50.0)
        self.assertEqual(contexto["totais_sede"]["despesas_fixas"], 180.0)
        self.assertAlmostEqual(contexto["totais_sede"]["total_envio_sede"], 1302.56, places=2)
        self.assertEqual(contexto["despesas_fixas_lista"], itens)

    def test_fallback_usa_lista_de_despesas_fixas(self):
        contexto = {
            "mes": 1,
            "ano": 2025,
            "envios": {},
            "despesas_fixas_lista": [
                {"nome": "Contador", "valor": 100},
                {"nome": "Site", "valor": 20},
            ],
        }
        with patch("app.financeiro.relatorio_sede_d23d53._itens_obrigacoes_competencia", return_value=[]):
            corrigir_contexto_relatorio_sede_d23d53(contexto)
        self.assertEqual(contexto["envios"]["contador_sede"], 100.0)
        self.assertEqual(contexto["envios"]["site"], 20.0)

    def test_adapter_e_read_only(self):
        src = ADAPTER.read_text(encoding="utf-8")
        self.assertIn(RELATORIO_SEDE_TEMPLATE, src)
        for token in ("db.session.add", "db.session.commit", "db.session.delete", "UPDATE ", "INSERT ", "DELETE FROM", "ALTER TABLE"):
            self.assertNotIn(token, src)

    def test_toolbar_adota_workspace_no_padrao_operacional(self):
        src = TOOLBAR.read_text(encoding="utf-8")
        for token in (
            "report-workspace__header",
            "report-controls",
            "report-type-grid",
            "report-period-grid",
            "report-note-card",
            "Gerar PDF",
            "Movimentações",
        ):
            self.assertIn(token, src)
        self.assertIn("width: min(1160px", src)

    def test_toolbar_nao_aparece_no_pdf(self):
        src = TOOLBAR.read_text(encoding="utf-8")
        self.assertTrue(src.lstrip().startswith("{% if not modo_pdf %}"))
        self.assertTrue(src.rstrip().endswith("{% endif %}"))

    def test_templates_relatorio_parseiam(self):
        env = Environment()
        failures = []
        for path in (TOOLBAR, RELATORIO_SEDE):
            try:
                env.parse(path.read_text(encoding="utf-8-sig"))
            except TemplateSyntaxError as exc:
                failures.append(f"{path.name}:{exc.lineno}: {exc.message}")
        self.assertEqual([], failures, "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
