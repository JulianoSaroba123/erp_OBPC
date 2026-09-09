import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "app" / "financeiro" / "templates" / "financeiro"

FILES = {
    "movimentacoes": TEMPLATES / "lista_lancamentos.html",
    "projetos": TEMPLATES / "lista_projetos.html",
    "destinacoes": TEMPLATES / "caixa_destinacoes.html",
    "conciliacao": TEMPLATES / "conciliacao.html",
}


class D23D52FinanceiroPadraoMembrosTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = {name: path.read_text(encoding="utf-8") for name, path in FILES.items()}

    def test_telas_financeiras_usam_obpc_page(self):
        for name, src in self.src.items():
            with self.subTest(name=name):
                self.assertIn('class="obpc-page"', src)
                self.assertIn('class="obpc-page-header"', src)
                self.assertIn('obpc-page-title', src)
                self.assertIn('obpc-page-subtitle', src)

    def test_kpis_usam_mesmo_componente_de_membros(self):
        for name in ("movimentacoes", "projetos", "destinacoes", "conciliacao"):
            self.assertIn("obpc-ops", self.src[name])
            self.assertIn("obpc-ops__label", self.src[name])
            self.assertIn("obpc-ops__value", self.src[name])

    def test_cards_e_tabelas_usam_design_system(self):
        for name, src in self.src.items():
            with self.subTest(name=name):
                self.assertIn("obpc-card", src)
        for name in ("movimentacoes", "destinacoes", "conciliacao"):
            self.assertIn("obpc-table", self.src[name])

    def test_filtros_usam_filter_bar_quando_aplicavel(self):
        self.assertIn("obpc-filter-bar", self.src["movimentacoes"])
        self.assertIn("obpc-filter-bar", self.src["destinacoes"])
        self.assertIn("obpc-filter-bar", self.src["conciliacao"])

    def test_acoes_criticas_foram_preservadas(self):
        movimentacoes = self.src["movimentacoes"]
        for token in (
            "financeiro.novo_lancamento",
            "financeiro.importar_extrato",
            "financeiro.conciliacao",
            "financeiro.editar_lancamento",
            "financeiro.excluir_lancamento",
        ):
            self.assertIn(token, movimentacoes)

        projetos = self.src["projetos"]
        for token in ("financeiro.novo_projeto", "financeiro.editar_projeto", "financeiro.excluir_projeto"):
            self.assertIn(token, projetos)

        conciliacao = self.src["conciliacao"]
        for token in (
            "financeiro.conciliacao_auto",
            "financeiro.conciliacao_sugerir",
            "financeiro.conciliacao_aceitar",
            "financeiro.conciliacao_aceitar_todos",
            "financeiro.conciliacao_export_pairs",
            "financeiro.conciliacao_undo",
        ):
            self.assertIn(token, conciliacao)

    def test_templates_nao_contêm_mutacao_de_banco(self):
        forbidden = ("db.session", "UPDATE ", "INSERT ", "DELETE FROM", "ALTER TABLE")
        for name, src in self.src.items():
            for token in forbidden:
                with self.subTest(name=name, token=token):
                    self.assertNotIn(token, src)


if __name__ == "__main__":
    unittest.main()
