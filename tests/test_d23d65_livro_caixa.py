import unittest
from pathlib import Path

from jinja2 import Environment, TemplateSyntaxError

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "app" / "financeiro" / "templates" / "financeiro"
LIVRO = TEMPLATES / "relatorio_livro_caixa.html"
TOOLBAR = TEMPLATES / "_relatorio_toolbar.html"
BASE = ROOT / "app" / "templates" / "base.html"
ROTAS = ROOT / "app" / "financeiro" / "financeiro_routes.py"


class D23D65LivroCaixaTest(unittest.TestCase):
    def test_tipo_livro_caixa_esta_habilitado(self):
        src = ROTAS.read_text(encoding="utf-8")
        self.assertIn("'livro_caixa'", src)
        self.assertIn("relatorio_{tipo_relatorio}.html", src)

    def test_livro_caixa_usa_logo_oficial_do_sistema(self):
        src = LIVRO.read_text(encoding="utf-8")
        self.assertIn("logo_pdf_src", src)
        self.assertIn("dados_igreja.logo", src)
        self.assertIn("logo_obpc_novo.jpg", src)

    def test_livro_caixa_e_preparado_para_a4_paisagem(self):
        src = LIVRO.read_text(encoding="utf-8")
        self.assertIn("size: A4 landscape", src)
        self.assertIn('class="movement-table"', src)
        self.assertIn("display: table-header-group", src)

    def test_livro_caixa_exibe_naturezas_e_meios_financeiros(self):
        src = LIVRO.read_text(encoding="utf-8")
        for token in (
            "Dízimos",
            "Ofertas",
            "Outras Ofertas",
            "OMN",
            "Outras Entradas",
            "Entradas Banco / PIX",
            "Entradas Dinheiro",
            "Saídas Banco / PIX",
            "Saídas Dinheiro",
            "Conta / Meio",
        ):
            self.assertIn(token, src)

    def test_livro_caixa_nao_exibe_contagem_de_comprovantes(self):
        src = LIVRO.read_text(encoding="utf-8")
        self.assertNotIn("total_comprovantes", src)
        self.assertNotIn("Comprovantes no período", src)

    def test_relatorio_sede_nao_foi_reaproveitado_como_livro_caixa(self):
        livro = LIVRO.read_text(encoding="utf-8")
        sede = (TEMPLATES / "relatorio_sede.html").read_text(encoding="utf-8-sig")
        self.assertIn("Livro Caixa", livro)
        self.assertIn("Prestacao de Contas Oficial", sede)
        self.assertNotEqual(livro, sede)

    def test_menu_expoe_livro_caixa(self):
        src = BASE.read_text(encoding="utf-8")
        self.assertIn("tipo_relatorio='livro_caixa'", src)
        self.assertIn("<span>Livro Caixa</span>", src)

    def test_toolbar_so_adiciona_card_do_livro_no_proprio_contexto(self):
        src = TOOLBAR.read_text(encoding="utf-8")
        self.assertIn("{% if tipo_relatorio == 'livro_caixa' %}", src)
        self.assertIn('value="livro_caixa"', src)
        self.assertIn("{% if tipo_relatorio != 'livro_caixa' %}", src)

    def test_template_parseia(self):
        env = Environment()
        try:
            env.parse(LIVRO.read_text(encoding="utf-8-sig"))
            env.parse(TOOLBAR.read_text(encoding="utf-8-sig"))
        except TemplateSyntaxError as exc:
            self.fail(f"Template inválido na linha {exc.lineno}: {exc.message}")


if __name__ == "__main__":
    unittest.main()
