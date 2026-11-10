"""A7H.10B independent tests; no ORM, database, network or filesystem mutations.
Can run with A7H8_REPO pointed to the user's isolated worktree.
"""
from __future__ import annotations
import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace
from datetime import date,timedelta
from decimal import Decimal
from io import BytesIO
import pytest
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

path=(Path(os.environ['A7H8_REPO'])/'app/utils/livro_caixa_simplificado.py'
      if os.environ.get('A7H8_REPO') else Path(__file__).resolve().parents[1]/'app/utils/livro_caixa_simplificado.py')
spec=importlib.util.spec_from_file_location('obpc_a7h10b',path)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def row(i, tipo='Entrada', valor='5.35', categoria='DÍZIMO', descricao='Contribuicao mensal'):
    return SimpleNamespace(id=i,tipo=tipo,valor=valor,conta='Pix',
                           categoria=categoria, descricao=descricao,
                           data=date(2026,7,1)+timedelta(days=(i-1)%30))


def test_quebra_historia_completa_sem_palavra_orfa():
    hist='Convencao Das Ig Ev Pent O Brasil Para Cristo Do'
    s=mod._historico_para_pdf(hist, 6.35*cm-8)
    assert s.replace('<br/>',' ') == hist
    assert s.count('<br/>') == 1
    partes=s.split('<br/>')
    assert all(len(p.split()) >= 2 for p in partes)
    assert all(stringWidth(p,'Helvetica',8) <= 6.35*cm-8 for p in partes)


def test_escapamento_html_seguro_e_sem_truncar():
    hist='Lancamento administrativo da igreja & contribuicao <sem alterar>'
    s=mod._historico_para_pdf(hist,6.35*cm-8)
    assert '&amp;' in s and '&lt;' in s and '&gt;' in s
    assert s.replace('<br/>',' ').replace('&amp;','&').replace('&lt;','<').replace('&gt;','>') == hist


def test_apuracao_e_pdfs_sem_duplo_desconto():
    ls=[row(1,'Entrada','150','DÍZIMO'),
        row(2,'Entrada','15','OFERTA OMN'),
        row(3,'Saída','55','CONTRIB. SEDE','Repasse a sede'),
        row(4,'Evidência','55','Importacao','Extrato conciliado')]
    dados=mod.apurar_livro_caixa(ls, Decimal('400.00'))
    assert dados['saldo_final']==Decimal('510.00')
    assert dados['enviado_sede']==Decimal('55.00')
    assert dados['evidencias_qtd']==1
    pdf=mod.gerar_livro_caixa_simplificado(ls,7,2026,400,None,'SIMULACAO')
    assert pdf.getvalue().startswith(b'%PDF')
    if PdfReader:
        t='\n'.join(p.extract_text() for p in PdfReader(BytesIO(pdf.getvalue())).pages)
        assert '510,00' in t and 'OMN' in t and 'Envios à Sede' in t


def test_compactacao_em_amostra_equivalente_nao_corta_resumo():
    descricoes=[
        'Contribuicao de membro da comunidade em dia de culto',
        'Material utilizado nas atividades religiosas',
        'Convencao Das Ig Ev Pent O Brasil Para Cristo Do',
        'Oferta de culto semanal',
        'Rendimento liquido da conta',
    ]
    ls=[row(i, tipo=('Saída' if i%4==0 else 'Entrada'),
            categoria=('OFERTA OMN' if i%7==0 else 'DÍZIMO'),
            descricao=descricoes[i%len(descricoes)]) for i in range(1,81)]
    pdf=mod.gerar_livro_caixa_simplificado(ls,7,2026,0,None,'SIMULACAO')
    if PdfReader:
        pages=PdfReader(BytesIO(pdf.getvalue())).pages
        assert 3 <= len(pages) <= 5
        full='\n'.join(p.extract_text() for p in pages)
        assert 'FECHAMENTO DO MÊS' in full
        assert 'DETALHAMENTO DE ENTRADAS E REPASSES' in full
        assert 'SALDO FINAL' in full
    else:
        assert len(pdf.getvalue())>4000
