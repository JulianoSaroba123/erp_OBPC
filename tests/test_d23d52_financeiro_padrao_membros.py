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
AUXILIARY = {
    "form_lancamento": TEMPLATES / "cadastro_lancamento.html",
    "form_projeto": TEMPLATES / "cadastro_projeto.html",
    "emitir_recibo": TEMPLATES / "emitir_recibo.html",
    "editar_recibo": TEMPLATES / "editar_recibo.html",
    "visualizar_recibo": TEMPLATES / "visualizar_recibo.html",
}


class D23D52FinanceiroPadraoMembrosTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = {name: path.read_text(encoding="utf-8") for name, path in FILES.items()}
        cls.aux = {name: path.read_text(encoding="utf-8") for name, path in AUXILIARY.items()}

    def test_telas_financeiras_usam_obpc_page(self):
        for name, src in {**self.src, **self.aux}.items():
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
        self.assertIn("obpc-ops", self.aux["visualizar_recibo"])

    def test_cards_e_tabelas_usam_design_system(self):
        for name, src in {**self.src, **self.aux}.items():
            with self.subTest(name=name):
                self.assertIn("obpc-card", src)
        for name in ("movimentacoes", "destinacoes", "conciliacao", "conciliacao_moderno", "repasse", "recibos"):
            self.assertIn("obpc-table", self.src[name])

    def test_filtros_usam_filter_bar_quando_aplicavel(self):
        for name in ("movimentacoes", "destinacoes", "conciliacao", "recibos"):
            self.assertIn("obpc-filter-bar", self.src[name])

    def test_form_lancamento_preserva_campos_e_fluxos(self):
        src = self.aux["form_lancamento"]
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
            self.assertIn(token, src)
        for component in ("obpc-input", "obpc-select", "obpc-textarea", "btn-submit-lancamento"):
            self.assertIn(component, src)

    def test_form_projeto_preserva_campos(self):
        src = self.aux["form_projeto"]
        for token in ('name="nome"', 'name="tipo"', 'name="status"', 'name="meta_valor"', 'name="descricao"', "financeiro.novo_projeto", "financeiro.editar_projeto"):
            self.assertIn(token, src)

    def test_fluxo_recibos_preserva_campos_e_acoes(self):
        emitir = self.aux["emitir_recibo"]
        editar = self.aux["editar_recibo"]
        visualizar = self.aux["visualizar_recibo"]
        for token in ('name="nome_doador"', 'name="cpf_cnpj"', 'name="valor"', 'name="data_doacao"', 'name="tipo_doacao"', 'name="forma_pagamento"', 'name="observacoes"'):
            self.assertIn(token, emitir)
            self.assertIn(token, editar)
        for token in ("financeiro.gerar_pdf_recibo", "financeiro.editar_recibo", "financeiro.excluir_recibo", "financeiro.lista_recibos"):
            self.assertIn(token, visualizar)

    def test_acoes_criticas_foram_preservadas(self):
        movimentacoes = self.src["movimentacoes"]
        for token in ("financeiro.novo_lancamento", "financeiro.importar_extrato", "financeiro.conciliacao", "financeiro.editar_lancamento", "financeiro.excluir_lancamento"):
            self.assertIn(token, movimentacoes)

        projetos = self.src["projetos"]
        for token in ("financeiro.novo_projeto", "financeiro.editar_projeto", "financeiro.excluir_projeto"):
            self.assertIn(token, projetos)

        for name in ("conciliacao", "conciliacao_moderno"):
            conciliacao = self.src[name]
            for token in ("financeiro.conciliacao_auto", "financeiro.conciliacao_sugerir", "financeiro.conciliacao_aceitar", "financeiro.conciliacao_aceitar_todos", "financeiro.conciliacao_export_pairs", "financeiro.conciliacao_undo"):
                self.assertIn(token, conciliacao)

        repasse = self.src["repasse"]
        for token in ("financeiro.envio_sede", "financeiro.gerenciar_despesas_fixas", "financeiro.gerar_lancamentos_despesas_fixas", "financeiro.gerar_lancamento_administrativo", "financeiro.toggle_despesa_fixa", "form_pagamento_composto", "alocacao_obrigacao_id[]", "pagamento_historico_sem_movimentacao"):
            self.assertIn(token, repasse)

        recibos = self.src["recibos"]
        for token in ("financeiro.novo_recibo", "financeiro.visualizar_recibo", "financeiro.editar_recibo", "financeiro.gerar_pdf_recibo", "financeiro.excluir_recibo"):
            self.assertIn(token, recibos)

    def test_templates_nao_contem_mutacao_de_banco(self):
        forbidden = ("db.session", "UPDATE ", "INSERT ", "DELETE FROM", "ALTER TABLE")
        for name, src in {**self.src, **self.aux}.items():
            for token in forbidden:
                with self.subTest(name=name, token=token):
                    self.assertNotIn(token, src)


if __name__ == "__main__":
    unittest.main()
