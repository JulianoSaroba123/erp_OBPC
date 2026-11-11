"""A7H.7B: regressao portavel do layout ReportLab do caixa completo.

Nao acessa banco, repositorio remoto, backups ou rede.
"""
from __future__ import annotations

import ast
from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table

SOURCE = Path(__file__).resolve().parents[1] / 'app/utils/gerar_pdf_reportlab.py'


def _method(name: str) -> ast.FunctionDef:
    tree = ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
    klass = [n for n in tree.body if isinstance(n, ast.ClassDef)
             and n.name == 'RelatorioFinanceiro']
    assert len(klass) == 1
    found = [n for n in klass[0].body
             if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(found) == 1
    return found[0]


def test_resumo_final_e_tabela_sem_titulo_orfao():
    source = ast.unparse(_method('_criar_resumo_financeiro'))
    assert 'cabecalho_resumo_final = Paragraph' in source
    assert 'KeepTogether([cabecalho_resumo_final, tabela_resumo])' in source


def test_blocos_de_repasses_da_sede_agrupados_e_ordenados():
    source = ast.unparse(_method('gerar_relatorio_caixa'))
    chunks = [
        'elementos_sede.extend(self._criar_secao_controle_repasse_sede(',
        'elementos_sede.extend(self._criar_secao_pagamentos_repasse_mes(',
        'elementos_sede.extend(self._criar_secao_justificativa_repasse_sede(',
    ]
    positions = [source.index(chunk) for chunk in chunks]
    assert positions == sorted(positions)
    assert 'elementos.append(KeepTogether(elementos_sede))' in source


def test_saldo_acumulado_inicializado_com_saldo_anterior():
    source = ast.unparse(_method('_criar_tabela_lancamentos'))
    assert 'saldo_anterior=0' in source
    assert 'saldo_acumulado = saldo_anterior or 0' in source


def test_blocos_reportlab_compostos_suportam_quebra_de_pagina():
    buffer = BytesIO()
    style = getSampleStyleSheet()['Normal']
    sections = [
        Paragraph('CONTROLE REPASSE', style),
        Table([['a', 'b']]*6, rowHeights=[25]*6),
        Spacer(1, 10),
        KeepTogether([Paragraph('PAGAMENTOS', style),
                      Table([['c', 'd']]*5, rowHeights=[24]*5)]),
        Spacer(1, 10),
        KeepTogether([Paragraph('JUSTIFICATIVA', style),
                      Paragraph('Texto de teste ' * 25, style)]),
    ]
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=1.5*cm, bottomMargin=2*cm)
    doc.build([Spacer(1, 450), KeepTogether(sections), Paragraph('RODAPE', style)])
    assert buffer.getvalue().startswith(b'%PDF')
    assert len(buffer.getvalue()) > 1500
