import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "app" / "financeiro" / "templates" / "financeiro"

FILES = {
    "movimentacoes": TEMPLATES / "lista_lancamentos.html",
    "projetos": TEMPLATES / "lista_projetos.html",
    "destinacoes": TEMPLATES / "caixa_destinacoes.html",
    "conciliacao": TEMPLATES / "conciliacao.html",
    "conciliacao_moderno": TEMPLATES / "conciliacao_moderno.html",
    "repasse": TEMPLATES / "gerenciar_despesas_fixas.html",
    "recibos": TEMPLATES / "lista_recibos.html",
}
FORM_LANCAMENTO = TEMPLATES / "cadastro_lancamento.html"


class D23D52FinanceiroPadraoMembrosTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = {name: path.read_text(encoding="utf-8") for name, path in FILES.items()}
        cls.form_lancamento = FORM_LANCAMENTO.read_text(encoding="utf-8")

    def test_telas_financeiras_usam_obpc_page(self):
        for name, src in {**self.src, "form_lancamento": self.form_lancamento}.items():
            with self.subTest(name=name):
                self.assertIn('class="obpc-page"', src)
                self.assertIn('class="obpc-page-header"', src)
                self.assertIn('obpc-page-title', src)
                self.assertIn('obpc-page-subtitle', src)

    def test_kpis_usam_mesmo_componente_de_membros(self):
        for name in FILES:
            self.assertIn("obpc-ops", self.src[name])
            self.assertIn("obpc-ops__label", self.src[name])
            self.assertIn("obpc-ops__value", self.src[name])

    def test_cards_e_tabelas_usam_design_system(self):
        for name, src in self.src.items():
            with self.subTest(name=name):
                self.assertIn("obpc-card", src)
        self.assertIn("obpc-card", self.form_lancamento)
        for name in ("movimentacoes", "destinacoes", "conciliacao", "conciliacao_moderno", "repasse", "recibos"):
            self.assertIn("obpc-table", self.src[name])

    def test_filtros_usam_filter_bar_quando_aplicavel(self):
        for name in ("movimentacoes", "destinacoes", "conciliacao", "recibos"):
            self.assertIn("obpc-filter-bar", self.src[name])

    def test_form_lancamento_preserva_campos_e_fluxos(self):
        for token in (
            'id="form-lancamento"',
            "financeiro.salvar_lancamento",
            'name="data"',
            'name="tipo"',
            'name="categoria"',
            'name="projeto_id"',
            'name="valor"',
            'name="conta"',
            'name="descricao"',
            'name="observacoes"',
            'name="comprovante"',
            "financeiro.excluir_comprovante",
            "financeiro.excluir_comprovante_multiplo",
            "financeiro.upload_comprovantes",
            'name="comprovantes[]"',
            "OUTRAS OFERTAS",
            "DESTINAÇÃO",
            "GASTO PROJETO",
        ):
            self.assertIn(token, self.form_lancamento)
        self.assertIn("obpc-input", self.form_lancamento)
        self.assertIn("obpc-select", self.form_lancamento)
        self.assertIn("obpc-textarea", self.form_lancamento)
        self.assertIn("btn-submit-lancamento", self.form_lancamento)

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

        for name in ("conciliacao", "conciliacao_moderno"):
            conciliacao = self.src[name]
            for token in (
                "financeiro.conciliacao_auto",
                "financeiro.conciliacao_sugerir",
                "financeiro.conciliacao_aceitar",
                "financeiro.conciliacao_aceitar_todos",
                "financeiro.conciliacao_export_pairs",
                "financeiro.conciliacao_undo",
            ):
                self.assertIn(token, conciliacao)

        repasse = self.src["repasse"]
        for token in (
            "financeiro.envio_sede",
            "financeiro.gerenciar_despesas_fixas",
            "financeiro.gerar_lancamentos_despesas_fixas",
            "financeiro.gerar_lancamento_administrativo",
            "financeiro.toggle_despesa_fixa",
            "form_pagamento_composto",
            "alocacao_obrigacao_id[]",
            "pagamento_historico_sem_movimentacao",
        ):
            self.assertIn(token, repasse)

        recibos = self.src["recibos"]
        for token in (
            "financeiro.novo_recibo",
            "financeiro.visualizar_recibo",
            "financeiro.editar_recibo",
            "financeiro.gerar_pdf_recibo",
            "financeiro.excluir_recibo",
        ):
            self.assertIn(token, recibos)

    def test_templates_nao_contem_mutacao_de_banco(self):
        forbidden = ("db.session", "UPDATE ", "INSERT ", "DELETE FROM", "ALTER TABLE")
        all_sources = {**self.src, "form_lancamento": self.form_lancamento}
        for name, src in all_sources.items():
            for token in forbidden:
                with self.subTest(name=name, token=token):
                    self.assertNotIn(token, src)


if __name__ == "__main__":
    unittest.main()
