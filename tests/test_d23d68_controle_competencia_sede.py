import unittest
from pathlib import Path

from jinja2 import Environment, TemplateSyntaxError

ROOT = Path(__file__).resolve().parents[1]
ROTAS = ROOT / "app" / "financeiro" / "financeiro_routes.py"
TPL = ROOT / "app" / "financeiro" / "templates" / "financeiro" / "gerenciar_despesas_fixas.html"


class D23D68ControleCompetenciaSedeTest(unittest.TestCase):
    def test_controle_operacional_separa_competencia_de_caixa(self):
        src = ROTAS.read_text(encoding="utf-8-sig")
        self.assertIn("def _montar_controle_competencia_sede", src)
        self.assertIn("'devido_competencia'", src)
        self.assertIn("'pago_competencia'", src)
        self.assertIn("'pagamentos_realizados_mes'", src)
        self.assertIn("'administrativo_materializado'", src)

    def test_tela_exibe_30_fixas_e_pagamentos_em_linhas_distintas(self):
        src = TPL.read_text(encoding="utf-8-sig")
        for token in (
            "30% da competência",
            "Despesas fixas da competência",
            "Total devido da competência",
            "Pagamento desta competência",
            "Pagamentos realizados no mês",
            "(caixa)",
        ):
            self.assertIn(token, src)

    def test_tela_avisa_quando_30_ainda_nao_foi_materializado(self):
        src = TPL.read_text(encoding="utf-8-sig")
        self.assertIn("administrativo_materializado", src)
        self.assertIn("Gerar 30%", src)
        self.assertIn("gerar_lancamento_administrativo", src)

    def test_relatorio_sede_nao_foi_alterado_por_esta_tela(self):
        src = ROTAS.read_text(encoding="utf-8-sig")
        self.assertIn("controle_competencia_sede = _montar_controle_competencia_sede", src)
        self.assertIn("controle_repasse_sede = _montar_controle_repasse_sede", src)

    def test_template_parseia(self):
        env = Environment()
        try:
            env.parse(TPL.read_text(encoding="utf-8-sig"))
        except TemplateSyntaxError as exc:
            self.fail(f"Template inválido na linha {exc.lineno}: {exc.message}")


if __name__ == "__main__":
    unittest.main()
