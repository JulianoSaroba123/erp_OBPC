"""Regressao independente do Livro Caixa interno opcional A7H.8."""
from __future__ import annotations
import importlib.util
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import os
from types import SimpleNamespace
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None
from io import BytesIO
import pytest

SOURCE = ((Path(os.environ['A7H8_REPO']) / 'app/utils/livro_caixa_simplificado.py')
          if os.getenv('A7H8_REPO') else Path(__file__).resolve().parents[1] / 'app/utils/livro_caixa_simplificado.py')
spec = importlib.util.spec_from_file_location('obpc_livro_simples', SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def l(i, tipo, valor, conta, dia, categoria='Geral', descricao='Lancamento de controle'):
    return SimpleNamespace(id=i, tipo=tipo, valor=valor, conta=conta,
                           data=date(2026, 7, dia), categoria=categoria,
                           descricao=descricao)


def dados_exemplo():
    return [l(1,'Entrada','100','Pix',1,'Dízimo','Dízimo via Pix'),
            l(2,'Saída','20.50','Dinheiro',2,'Material','Compra material'),
            l(3,'Evidência','100','Pix',3,'Importação','Extrato conciliado'),
            l(4,'Entrada','40.00','Dinheiro',4,'Oferta','Oferta espécie'),
            l(5,'Saída','8.45','Banco',5,'Tarifa','Tarifa bancária')]


def test_evidencia_neutra_e_saldo_consolidado():
    a=mod.apurar_livro_caixa(dados_exemplo(), Decimal('1000.00'))
    assert len(a['movimentos']) == 4
    assert a['evidencias_qtd'] == 1
    assert a['evidencias_valor'] == Decimal('100.00')
    assert a['entradas'] == Decimal('140.00')
    assert a['saidas'] == Decimal('28.95')
    assert a['saldo_final'] == Decimal('1111.05')
    assert [x['saldo'] for x in a['movimentos']] == [
        Decimal('1100.00'),Decimal('1079.50'),Decimal('1119.50'),Decimal('1111.05')]


def test_pix_e_banco_mesma_classificacao_bancaria():
    a=mod.apurar_livro_caixa(dados_exemplo(), 0)
    assert a['contas']['Banco/Pix'] == {'entradas': Decimal('100.00'), 'saidas':Decimal('8.45')}
    assert a['contas']['Dinheiro'] == {'entradas': Decimal('40.00'), 'saidas':Decimal('20.50')}


def test_saida_sem_acento_e_estado_desconhecido_nao_vira_despesa():
    a=mod.apurar_livro_caixa([l(1,'saida','10','Banco',1),l(2,'Pendente','1000','Banco',2)], 5)
    assert a['saldo_final'] == Decimal('-5.00')
    assert len(a['movimentos']) == 1


def test_ordem_data_id_nao_modifica_entrada():
    d=dados_exemplo()[::-1]
    b=list(d)
    a=mod.apurar_livro_caixa(d,0)
    assert d == b
    assert [m['data'].day for m in a['movimentos']] == [1,2,4,5]


def test_pdf_meses_e_titulos_sem_obrigacoes_sede():
    conf=SimpleNamespace(logo=None,cidade='Tietê')
    pdf=mod.gerar_livro_caixa_simplificado(dados_exemplo(),7,2026,1000,conf,'SIMULACAO TESTE')
    assert pdf.getvalue().startswith(b'%PDF')
    if PdfReader is not None:
        reader=PdfReader(BytesIO(pdf.getvalue()))
        text='\n'.join(page.extract_text() for page in reader.pages)
        assert 'LIVRO CAIXA INTERNO' in text
        assert 'SALDO FINAL' in text
        assert '1.111,05' in text
        assert 'FECHAMENTO DO MÊS' in text
        assert 'MOVIMENTAÇÃO POR CONTA' in text
        assert 'JUSTIFICATIVA CONTÁBIL' not in text
        assert 'OBRIGAÇÕES' not in text
    else:
        assert len(pdf.getvalue()) > 1800


def test_mais_de_100_linhas_pagina_sem_extravasar():
    dados=[]
    for i in range(1,115):
        dados.append(SimpleNamespace(id=i,tipo='Entrada' if i%3 else 'Saída',
            valor='5.35',conta='Pix' if i%2 else 'Dinheiro',
            data=date(2026,7,1)+timedelta(days=(i-1)%30),
            descricao='Oferta voluntária mensal ou despesa de manutenção registrada na tesouraria',categoria='Movimentações'))
    buff=mod.gerar_livro_caixa_simplificado(dados,7,2026,0,None)
    if PdfReader is not None:
        reader=PdfReader(BytesIO(buff.getvalue()))
        assert 3 <= len(reader.pages) <= 10
        txt='\n'.join(p.extract_text() for p in reader.pages)
        assert txt.count('HISTÓRICO / CATEGORIA') == len(reader.pages) - (0 if 'FECHAMENTO DO MÊS' in reader.pages[-1].extract_text() else 1)
        assert 'SALDO FINAL' in txt
    else:
        assert buff.getvalue().startswith(b'%PDF') and len(buff.getvalue()) > 4000


def test_competencia_invalida_bloqueada():
    with pytest.raises(ValueError):
        mod.gerar_livro_caixa_simplificado([],13,2026)


def test_rota_optin_retorna_pdf_sem_modificar_rota_legada():
    if not os.getenv('A7H8_REPO'):
        pytest.skip('Teste de integracao da rota apenas dentro da worktree do ERP')
    from unittest.mock import MagicMock, patch
    from flask import Flask
    from app.financeiro import financeiro_routes

    app = Flask('obpc_a7h8_rota_teste')
    app.config.update(TESTING=True, SECRET_KEY='a7h8-rota')
    app.register_blueprint(financeiro_routes.financeiro_bp)
    query = MagicMock()
    query.filter.return_value.order_by.return_value.all.return_value = dados_exemplo()
    config = SimpleNamespace(cidade='Tietê', logo=None)

    with app.test_request_context('/financeiro/relatorio-caixa/pdf?mes=7&ano=2026&formato=livro_caixa'):
        with patch.object(financeiro_routes.Lancamento, 'query', query), \
             patch.object(financeiro_routes.Lancamento, 'calcular_saldo_ate_mes_anterior', return_value=1000), \
             patch.object(financeiro_routes.Configuracao, 'obter_configuracao', return_value=config), \
             patch.object(financeiro_routes, '_montar_controle_repasse_sede', side_effect=AssertionError('Nao deve chamar Sede')):
            response = financeiro_routes.relatorio_caixa_pdf.__wrapped__()
    assert response.mimetype == 'application/pdf'
    assert response.status_code == 200
    response.direct_passthrough = False
    pdf_bytes=response.get_data()
    assert pdf_bytes.startswith(b'%PDF') and len(pdf_bytes)>1800
    if PdfReader is not None:
        pdf=PdfReader(BytesIO(pdf_bytes))
        txt='\n'.join(p.extract_text() for p in pdf.pages)
        assert 'LIVRO CAIXA INTERNO' in txt
        assert 'SALDO FINAL' in txt


def test_classificacao_ofertas_e_omn_sem_duplicidade():
    data = [
        l(1, 'Entrada', '150.00', 'Pix', 1, 'DÍZIMO'),
        l(2, 'Entrada', '20.00', 'Dinheiro', 2, 'OFERTA'),
        l(3, 'Entrada', '25.00', 'Pix', 3, 'OUTRAS OFERTAS'),
        l(4, 'Entrada', '15.00', 'Dinheiro', 4, 'Oferta Especial'),
        l(5, 'Entrada', '35.00', 'Banco', 5, 'OFERTA OMN'),
        l(6, 'Entrada', '10.00', 'Pix', 6, 'Oferta Missionária'),
        l(7, 'Entrada', '5.00', 'Pix', 7, 'RENDIMENTOS'),
    ]
    a = mod.apurar_livro_caixa(data, 0)
    assert a['entradas_por_natureza'] == {
        'Dízimos': Decimal('150.00'),
        'Ofertas de culto': Decimal('20.00'),
        'Outras ofertas': Decimal('40.00'),
        'OMN - Oferta Missionária': Decimal('45.00'),
        'Outras entradas': Decimal('5.00'),
    }
    assert sum(a['entradas_por_natureza'].values()) == a['entradas'] == Decimal('260.00')


def test_envio_sede_e_apenas_saida_efetiva_sem_dupla_subtracao():
    data = [
        l(1, 'Saída', '300.00', 'Pix', 1, 'CONTRIB. SEDE'),
        l(2, 'Saída', '70.00', 'Banco', 2, 'REPASSE À SEDE'),
        l(3, 'Saída', '45.00', 'Dinheiro', 3, 'Material'),
        l(4, 'Entrada', '12.00', 'Banco', 4, 'REPASSE À SEDE'),
        l(5, 'Evidência', '300.00', 'Pix', 5, 'CONTRIB. SEDE'),
    ]
    a=mod.apurar_livro_caixa(data, 1000)
    assert a['enviado_sede'] == Decimal('370.00')
    assert a['demais_saidas'] == Decimal('45.00')
    assert a['saidas'] == Decimal('415.00')
    assert a['saldo_final'] == Decimal('597.00')
    assert a['evidencias_valor'] == Decimal('300.00')


def test_livro_caixa_pdf_exibe_secao_e_nao_recalcula_obrigacoes():
    data = [
        l(1, 'Entrada', '50.00', 'Dinheiro', 1, 'OUTRAS OFERTAS'),
        l(2, 'Entrada', '20.00', 'Pix', 2, 'OFERTA OMN'),
        l(3, 'Saída', '10.00', 'Banco', 3, 'CONTRIB. SEDE'),
    ]
    p=mod.gerar_livro_caixa_simplificado(data, 7, 2026, 100, None, 'TESTE')
    assert p.getvalue().startswith(b'%PDF')
    if PdfReader is not None:
        text='\n'.join(page.extract_text() for page in PdfReader(BytesIO(p.getvalue())).pages)
        assert 'Outras ofertas' in text
        assert 'OMN - Oferta Missionária' in text
        assert 'Envios à Sede (pagamentos efetivos)' in text
        assert 'TOTAL DE SAÍDAS' in text
        assert '160,00' in text # 100 + 50 + 20 - 10
        assert 'OBRIGAÇÕES' not in text
