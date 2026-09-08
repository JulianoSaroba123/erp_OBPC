from datetime import date
from pathlib import Path
from types import SimpleNamespace
import unittest

from app.utils.relatorio_sede_oficial import gerar_relatorio_sede_oficial, montar_read_model_sede


class _RelatorioStub:
    def __init__(self):
        self.config = SimpleNamespace(
            percentual_conselho=30,
            nome_igreja="OBPC Teste",
            cidade="Tietê",
            bairro="São Pedro",
            presidente="Pr. Teste",
            primeiro_tesoureiro="Tesoureiro Teste",
            logo=None,
        )
        self.buffer = None

    @staticmethod
    def _formatar_moeda(valor):
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _lancamento(tipo, categoria, valor, impacta=True):
    return SimpleNamespace(tipo=tipo, categoria=categoria, valor=valor, impacta_financeiro=impacta)


def _pagamento(id_, competencia, admin, fixas, total):
    return SimpleNamespace(
        id=id_,
        data_pagamento=date(2026, 8, 28),
        competencia=competencia,
        competencia_mes=None,
        competencia_ano=None,
        competencia_mes_ref=None,
        competencia_ano_ref=None,
        valor_administrativo=admin,
        valor_despesas_fixas=fixas,
        valor_total=total,
        valor=total,
        pagamento_historico_sem_movimentacao=False,
        tipo_pagamento="PAGAMENTO_BANCARIO",
    )


def _fixture_agosto():
    lancamentos = [
        _lancamento("Entrada", "DÍZIMOS", 4403.97),
        _lancamento("Entrada", "OFERTAS ALÇADAS", 507.03),
        _lancamento("Entrada", "OFERTA OMN", 90.10),
        _lancamento("Entrada", "RENDIMENTOS FINANCEIROS", 1.04),
        _lancamento("Saída", "DESPESAS", 2358.19),
        _lancamento("Saída", "CONTRIB. SEDE", 2573.31),
        _lancamento("Saída", "CONTRIB. SEDE", 1292.56),
        _lancamento("Saída", "CONTRIB. SEDE", 30.00),
        _lancamento("Evidência", "BANCO", 3895.87, impacta=False),
    ]
    pagamentos = [
        _pagamento(26, "06/2026", 2403.31, 170.00, 2573.31),
        _pagamento(27, "07/2026", 1122.56, 170.00, 1292.56),
        _pagamento(28, "Projeto Filipe acumulado 05/2026 a 07/2026", 0.00, 30.00, 30.00),
    ]
    fixas = [
        {"nome": "Contador", "valor": 100.00},
        {"nome": "Força para Viver", "valor": 50.00},
        {"nome": "Projeto Filipe", "valor": 10.00},
        {"nome": "Site", "valor": 20.00},
    ]
    return lancamentos, pagamentos, fixas


class D23D49RelatorioSedeTest(unittest.TestCase):
    def setUp(self):
        lancamentos, pagamentos, fixas = _fixture_agosto()
        self.lancamentos = lancamentos
        self.pagamentos = pagamentos
        self.fixas = fixas
        self.dados = montar_read_model_sede(
            lancamentos,
            8,
            2026,
            832.24,
            30,
            pagamentos=pagamentos,
            obrigacoes_fixas=fixas,
        )

    def test_01_pdf_sede_renderiza(self):
        pdf = gerar_relatorio_sede_oficial(
            _RelatorioStub(),
            self.lancamentos,
            8,
            2026,
            832.24,
            pagamentos=self.pagamentos,
            obrigacoes_fixas=self.fixas,
        )
        conteudo = pdf.getvalue()
        self.assertTrue(conteudo.startswith(b"%PDF"))
        self.assertGreater(len(conteudo), 1500)

    def test_02_base_dos_30_porcento_correta(self):
        self.assertEqual(self.dados["base_30"], 4911.00)
        self.assertEqual(self.dados["valor_30"], 1473.30)

    def test_03_omn_nao_entra_na_base(self):
        self.assertEqual(self.dados["oferta_omn"], 90.10)
        self.assertEqual(self.dados["base_30"], 4403.97 + 507.03)

    def test_04_obrigacoes_fixas_separadas(self):
        self.assertEqual(self.dados["total_fixas_competencia"], 180.00)
        self.assertEqual([item["nome"] for item in self.dados["obrigacoes_fixas"]], [
            "Contador", "Força para Viver", "Projeto Filipe", "Site"
        ])

    def test_05_total_competencia_correto(self):
        self.assertEqual(self.dados["total_competencia"], 1653.30)

    def test_06_pagamentos_historicos_nao_alteram_obrigacao_corrente(self):
        self.assertEqual(self.dados["total_pago_sede"], 3895.87)
        self.assertEqual(self.dados["total_competencia"], 1653.30)

    def test_07_pagamentos_historicos_aparecem_uma_unica_vez(self):
        self.assertEqual(len(self.dados["pagamentos"]), 3)
        self.assertEqual(sum(item["total"] for item in self.dados["pagamentos"]), 3895.87)

    def test_08_evidencia_bancaria_nao_e_somada(self):
        self.assertEqual(self.dados["total_saidas"], 6254.06)

    def test_09_projeto_filipe_trinta_reais_uma_vez(self):
        ocorrencias = [p for p in self.dados["pagamentos"] if "Projeto Filipe" in p["competencia"]]
        self.assertEqual(len(ocorrencias), 1)
        self.assertEqual(ocorrencias[0]["total"], 30.00)

    def test_10_resultado_e_saldo_final_agosto(self):
        self.assertEqual(self.dados["total_entradas"], 5002.14)
        self.assertEqual(self.dados["resultado_mes"], -1251.92)
        self.assertEqual(self.dados["saldo_final"], -419.68)
        self.assertEqual(self.dados["despesas_gerais"], 2358.19)

    def test_11_justificativa_reflete_pagamentos_anteriores(self):
        self.assertEqual(
            self.dados["justificativa"],
            "Foram registrados pagamentos neste período referentes à quitação de competências anteriores junto à Sede.",
        )
        self.assertNotIn("Não houve pagamento", self.dados["justificativa"])

    def test_12_pdf_oficial_nao_contem_blocos_gerenciais_removidos(self):
        fonte = Path("app/utils/relatorio_sede_oficial.py").read_text(encoding="utf-8")
        proibidos = [
            "RESUMO EXECUTIVO",
            "DISTRIBUIÇÃO FINANCEIRA",
            "EVOLUÇÃO FINANCEIRA",
            "DETALHAMENTO DOS ENVIOS",
            "CONTADOR DE REGISTROS",
            "D23D48",
        ]
        for termo in proibidos:
            self.assertNotIn(termo, fonte)

    def test_13_tabela_html_nao_usa_overflow_horizontal_nem_coluna_forma(self):
        template = Path("app/financeiro/templates/financeiro/relatorio_sede.html").read_text(encoding="utf-8")
        self.assertNotIn("overflow-x", template)
        self.assertNotIn("min-width: 920", template)
        self.assertNotIn(">FORMA<", template)
        self.assertIn("table-layout:fixed", template.replace(" ", ""))

    def test_14_apresentacao_nao_muta_banco(self):
        fonte = Path("app/utils/relatorio_sede_oficial.py").read_text(encoding="utf-8")
        proibidos = ["db.session.add", "db.session.delete", "db.session.commit", "UPDATE ", "INSERT ", "DELETE "]
        for termo in proibidos:
            self.assertNotIn(termo, fonte)


if __name__ == "__main__":
    unittest.main()
