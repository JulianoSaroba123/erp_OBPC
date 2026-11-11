"""A7H.5: regressao real de layout ReportLab sem Flask, banco nem rede.

Uso: python -B -X utf8 -m pytest -q tests/test_a7h5_pdf_visual.py
"""
from __future__ import annotations

import ast
import io
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

SOURCE = Path(__file__).resolve().parents[1] / 'app/utils/gerar_pdf_reportlab.py'


def metodo(nome):
    arvore = ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
    classes = [n for n in arvore.body if isinstance(n, ast.ClassDef) and n.name == 'RelatorioFinanceiro']
    assert len(classes) == 1
    funcoes = [n for n in classes[0].body if isinstance(n, ast.FunctionDef) and n.name == nome]
    assert len(funcoes) == 1, nome
    no = ast.Module(body=[funcoes[0]], type_ignores=[])
    ast.fix_missing_locations(no)
    globs = dict(Table=Table, TableStyle=TableStyle, Paragraph=Paragraph, Spacer=Spacer,
                 ParagraphStyle=ParagraphStyle, colors=colors, cm=cm, escape=escape,
                 TA_CENTER=TA_CENTER, TA_LEFT=TA_LEFT, TA_RIGHT=TA_RIGHT)
    exec(compile(no, str(SOURCE), 'exec'), globs)
    return globs[nome]


class FakeSelf:
    def __init__(self, assinatura1=None, assinatura2=None):
        styles = getSampleStyleSheet()
        self.styles = {
            'texto_normal': styles['Normal'],
            'cabecalho_secao': styles['Heading2'],
        }
        self.config = SimpleNamespace(campo_assinatura_1=assinatura1,
                                      campo_assinatura_2=assinatura2,
                                      fonte_relatorio='Helvetica')

    def _formatar_moeda(self, valor):
        return f'R$ {float(valor):.2f}'

    def _gerar_info_comprovante(self, lancamento):
        return '-'

    def _truncar_texto(self, texto, max_chars):
        return texto if len(texto) <= max_chars else texto[:max_chars - 3] + '...'


def movimento(tipo, valor, dia):
    return SimpleNamespace(data=date(2026, 7, dia), tipo=tipo, valor=valor,
                           descricao='Teste A7H5', categoria='Pagamento', conta='Pix')


class TesteA7H5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tabela = staticmethod(metodo('_criar_tabela_lancamentos'))
        cls.pagamentos = staticmethod(metodo('_criar_secao_pagamentos_repasse_mes'))
        cls.justificativa = staticmethod(metodo('_criar_secao_justificativa_repasse_sede'))
        cls.assinaturas = staticmethod(metodo('_criar_campos_assinatura'))

    def test_01_saldo_anterior_entra_no_acumulado(self):
        dados = [movimento('Saída', 120, 1), movimento('Entrada', 300, 2),
                 movimento('Evidência', 2426, 3)]
        tabela = self.tabela(FakeSelf(), dados, True, saldo_anterior=12136.21)[0]
        self.assertEqual([l[6] for l in tabela._cellvalues[1:]],
                         ['R$ 12016.21', 'R$ 12316.21', 'R$ 12316.21'])

    def test_02_saldo_anterior_padrao_preserva_compatibilidade(self):
        tb = self.tabela(FakeSelf(), [movimento('Entrada', 300, 2)], True)[0]
        self.assertEqual(tb._cellvalues[1][6], 'R$ 300.00')

    def test_03_agosto_saldo_inicial(self):
        tb = self.tabela(FakeSelf(), [movimento('Entrada', 300, 2)], True,
                         saldo_anterior=3429.32)[0]
        self.assertEqual(tb._cellvalues[1][6], 'R$ 3729.32')

    def test_04_pagamentos_zero_rotulos_sem_invasao(self):
        story = self.pagamentos(FakeSelf(), {})
        tabela = next(x for x in story[1]._content if isinstance(x, Table))
        self.assertTrue(all(isinstance(x, Paragraph) for x in tabela._cellvalues[0]))
        self.assertEqual(tabela.repeatRows, 1)
        self.assertTrue(all(isinstance(tabela._cellvalues[-j][0], Paragraph) for j in (1, 2, 3)))
        self.assertEqual(len(tabela._spanCmds), 3)
        self.assertLessEqual(sum(tabela._colWidths), 17 * cm)

    def test_05_pagamentos_com_dados_e_texto_longo_renderiza(self):
        pagamento = SimpleNamespace(
            data_pagamento=date(2026, 8, 28), competencia='08/2026',
            competencia_mes_ref=None, competencia_ano_ref=None,
            forma_pagamento='Pix e transferência bancária',
            valor_administrativo=1800.90, valor_despesas_fixas=100.15, valor_total=1901.05,
        )
        story = self.pagamentos(FakeSelf(), {'pagamentos_mes': [pagamento]})
        tabela = next(x for x in story[1]._content if isinstance(x, Table))
        self.assertIsInstance(tabela._cellvalues[1][2], Paragraph)
        self.assertIn('1', tabela._cellvalues[1][3])
        buff = io.BytesIO()
        doc = SimpleDocTemplate(buff, pagesize=A4, leftMargin=2 * cm,
                                rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
        doc.build(list(story))
        self.assertTrue(buff.getvalue().startswith(b'%PDF'))
        self.assertGreater(len(buff.getvalue()), 1800)

    def test_06_justificativa_integral_no_mesmo_bloco(self):
        story = self.justificativa(FakeSelf(), 'Linha 1\nLinha 2 ' + 'teste ' * 35)
        self.assertTrue(any(x.__class__.__name__ == 'KeepTogether' for x in story))
        buff = io.BytesIO()
        SimpleDocTemplate(buff, pagesize=A4).build(story)
        self.assertTrue(buff.getvalue().startswith(b'%PDF'))

    def test_07_sem_assinatura_nao_gera_espaco(self):
        self.assertEqual(self.assinaturas(FakeSelf()), [])

    def test_08_com_assinatura_mantem_o_bloco(self):
        result = self.assinaturas(FakeSelf(assinatura1='Pastor'))
        self.assertTrue(result)
        self.assertIsInstance(result[0], Spacer)

    def test_09_sumario_cabecalhos_solidarios(self):
        src = SOURCE.read_text(encoding='utf-8-sig')
        self.assertIn('KeepTogether([cabecalho_entradas, tabela_entradas])', src)
        self.assertIn('KeepTogether([cabecalho_saidas, tabela_saidas])', src)
        self.assertIn('tabela_saidas = Table(dados_saidas, colWidths=[9*cm, 4.5*cm, 2.5*cm], repeatRows=1)', src)
        self.assertIn('saldo_anterior=saldo_anterior))', src)

    def test_10_pagamentos_extensos_paginam_sem_estourar_layout(self):
        pagamentos = [SimpleNamespace(
            data_pagamento=date(2026, 8, 28), competencia='08/2026',
            competencia_mes_ref=None, competencia_ano_ref=None,
            forma_pagamento='Transferência bancária via Pix',
            valor_administrativo=1500.90, valor_despesas_fixas=100.15,
            valor_total=1601.05,
        ) for _ in range(40)]
        story = self.pagamentos(FakeSelf(), {'pagamentos_mes': pagamentos})
        buff = io.BytesIO()
        SimpleDocTemplate(buff, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                          topMargin=1.5*cm, bottomMargin=2*cm).build(story)
        self.assertTrue(buff.getvalue().startswith(b'%PDF'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
