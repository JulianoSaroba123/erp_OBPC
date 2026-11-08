"""A7G | Testes isolados dos métodos originais por AST, sem iniciar Flask.

Executar diretamente: python -B -X utf8 tests/test_a7g_pdf_caixa.py
"""
from __future__ import annotations

import ast
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'app' / 'utils' / 'gerar_pdf_reportlab.py'


class FakeTable:
    def __init__(self, data, **kwargs):
        self.data = data
        self.kwargs = kwargs
        self.style = None

    def setStyle(self, style):
        self.style = style


class FakeTableStyle(list):
    pass


class FakeSelf:
    styles = {'texto_normal': 'dummy'}

    @staticmethod
    def _formatar_moeda(valor):
        return f'R$ {float(valor):.2f}'

    @staticmethod
    def _gerar_info_comprovante(lancamento):
        return '-'

    @staticmethod
    def _truncar_texto(texto, limite):
        return texto[:limite]


def obter_metodo(nome):
    arquivo = SOURCE.read_text(encoding='utf-8-sig')
    arvore = ast.parse(arquivo, filename=str(SOURCE))
    classe = [n for n in arvore.body if isinstance(n, ast.ClassDef)
              and n.name == 'RelatorioFinanceiro']
    if len(classe) != 1:
        raise AssertionError('Classe ReportLab não encontrada de forma única')
    metodos = [n for n in classe[0].body if isinstance(n, ast.FunctionDef)
               and n.name == nome]
    if len(metodos) != 1:
        raise AssertionError(f'Método {nome} não encontrado de forma única')

    modulo = ast.Module(body=[metodos[0]], type_ignores=[])
    ast.fix_missing_locations(modulo)
    namespace = {
        'Table': FakeTable,
        'TableStyle': FakeTableStyle,
        'Paragraph': lambda *args: ('paragraph', args),
        'cm': 1,
        'colors': SimpleNamespace(
            green='green', red='red', grey='grey', white='white',
            black='black', whitesmoke='whitesmoke', HexColor=lambda code: code
        ),
    }
    exec(compile(modulo, str(SOURCE), 'exec'), namespace)
    return namespace[nome]


def movimento(tipo, valor, conta, categoria='Pagamento', dia=1):
    return SimpleNamespace(
        data=date(2026, 7, dia), tipo=tipo, valor=valor, conta=conta,
        categoria=categoria, descricao='A7G teste controlado'
    )


ENTRADA = 'Entrada'
SAIDA = 'Sa\u00edda'
EVIDENCIA = 'Evid\u00eancia'


class A7GFinanceiroCaixaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.categorias = staticmethod(obter_metodo('_calcular_totais_por_categoria'))
        cls.contas = staticmethod(obter_metodo('_calcular_totais_por_conta'))
        cls.tabela = staticmethod(obter_metodo('_criar_tabela_lancamentos'))

    def test_01_evidencia_nao_e_saida_por_categoria(self):
        data = [movimento(ENTRADA,50,'Banco','Dizimos'),
                movimento(SAIDA,100,'Pix'),
                movimento(EVIDENCIA,40,'Extrato')]
        totals = self.categorias(None,data)
        self.assertEqual(sum(totals['entradas'].values()),50)
        self.assertEqual(sum(totals['saidas'].values()),100)

    def test_02_evidencia_neutra_independente_da_origem(self):
        data = [movimento(EVIDENCIA,40,'Dinheiro'),
                movimento(EVIDENCIA,2426,'Extrato'),
                movimento('EVIDENCIA',10,'Banco'),
                movimento(SAIDA,20,'Dinheiro')]
        self.assertEqual(sum(self.categorias(None,data)['saidas'].values()),20)

    def test_03_pix_e_conta_corrente_sao_banco(self):
        data = [movimento(SAIDA,100,'Pix'),
                movimento(SAIDA,80,'Banco'),
                movimento(ENTRADA,30,'Conta Corrente'),
                movimento(SAIDA,60,'Dinheiro')]
        accounts = self.contas(None,data)
        self.assertEqual(accounts['banco']['saidas'],180)
        self.assertEqual(accounts['banco']['entradas'],30)
        self.assertEqual(accounts['dinheiro']['saidas'],60)

    def test_04_evidencia_nao_altera_totais_por_conta(self):
        data = [movimento(EVIDENCIA,1000,'Pix'),
                movimento(EVIDENCIA,40,'Dinheiro'),
                movimento(SAIDA,20,'Pix')]
        accounts = self.contas(None,data)
        self.assertEqual(accounts['banco']['saidas'],20)
        self.assertEqual(accounts['dinheiro']['saidas'],0)

    def test_05_saldo_linha_evidencia_neutro(self):
        data = [movimento(ENTRADA,50,'Banco',dia=1),
                movimento(SAIDA,100,'Pix',dia=2),
                movimento(EVIDENCIA,40,'Extrato',dia=3),
                movimento(SAIDA,20,'Dinheiro',dia=4)]
        tb = self.tabela(FakeSelf(),data,True)[0]
        self.assertEqual([r[6] for r in tb.data[1:]],
                         ['R$ 50.00','R$ -50.00','R$ -50.00','R$ -70.00'])
        self.assertEqual(tb.data[3][4],'R$ 40.00')
        self.assertEqual(tb.data[3][3],EVIDENCIA.upper())
        styles = list(tb.style)
        self.assertIn(('TEXTCOLOR',(4,3),(4,3),'grey'),styles)

    def test_06_tabela_sem_saldo_mantem_evidencia(self):
        tb = self.tabela(FakeSelf(),[movimento(EVIDENCIA,40,'Extrato')],False)[0]
        self.assertEqual(len(tb.data[1]),6)
        self.assertEqual(tb.data[1][4],'R$ 40.00')

    def test_07_cenario_financeiro_e_resumo_categorias(self):
        data = [movimento(ENTRADA,50,'Banco','Dizimos'),
                movimento(SAIDA,100,'Pix'),
                movimento(SAIDA,80,'Banco'),
                movimento(SAIDA,60,'Dinheiro'),
                movimento(EVIDENCIA,40,'Extrato')]
        totals = self.categorias(None,data)
        self.assertEqual(sum(totals['entradas'].values()) - sum(totals['saidas'].values()),-190)

    def test_08_resumo_final_usa_totais_categorias(self):
        source = SOURCE.read_text(encoding='utf-8-sig')
        self.assertIn("total_saidas_final = sum(totais_categoria['saidas'].values())",source)
        self.assertIn("total_entradas_final = sum(totais_categoria['entradas'].values())",source)


if __name__ == '__main__':
    unittest.main(verbosity=2)
