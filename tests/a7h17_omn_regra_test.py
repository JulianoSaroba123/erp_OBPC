"""A7H.17: regressao OMN e boleto sem ORM, rede ou acesso ao banco."""
from __future__ import annotations

import ast
import importlib.util
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
MODULO = ROOT / 'app' / 'utils' / 'livro_caixa_simplificado.py'
ROTAS = ROOT / 'app' / 'financeiro' / 'financeiro_routes.py'
DOC = ROOT / 'PADRONIZACAO_OFERTAS.md'

spec = importlib.util.spec_from_file_location('obpc_omn_a7h17', MODULO)
assert spec and spec.loader
livro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(livro)


def mov(id, tipo, valor, conta, dia, categoria, descricao):
    return SimpleNamespace(
        id=id, tipo=tipo, valor=Decimal(valor), conta=conta,
        data=date(2026, 7, dia), categoria=categoria, descricao=descricao,
    )


def dados_base():
    return [
        mov(1, 'Entrada', '100.00', 'Pix', 1, 'DÍZIMO', 'Dízimo Pix'),
        mov(2, 'Entrada', '50.00', 'Dinheiro', 2, 'OFERTA', 'Oferta do culto'),
        mov(3, 'Entrada', '20.00', 'Pix', 3, 'OFERTA OMN', 'OMN recebida Pix'),
        mov(4, 'Entrada', '30.00', 'Dinheiro', 4, 'OFERTA OMN', 'OMN recebida em espécie'),
        mov(5, 'Saída', '45.00', 'Banco', 5, 'DESP. VARIAVEIS', 'Convenção - boleto pago'),
        mov(6, 'Evidência', '45.00', 'Banco', 6, 'Conciliação', 'Comprovante de boleto'),
    ]


def calculador_sede_real():
    """Extrai a funcao REAL sem iniciar Flask nem abrir sessao de banco."""
    arvore = ast.parse(ROTAS.read_text(encoding='utf-8-sig'), filename=str(ROTAS))
    nomes = {'_decimal_monetario', '_calcular_totais_relatorio_sede'}
    funcoes = [n for n in arvore.body if isinstance(n, ast.FunctionDef) and n.name in nomes]
    assert {n.name for n in funcoes} == nomes, 'Funcoes de calculo Sede nao encontradas'
    codigo = ast.Module(body=funcoes, type_ignores=[])
    ast.fix_missing_locations(codigo)
    namespace = {'Decimal': Decimal}
    exec(compile(codigo, str(ROTAS), 'exec'), namespace)
    return namespace['_calcular_totais_relatorio_sede']


def test_recebimento_omn_em_pix_e_dinheiro_aumenta_caixa():
    a = livro.apurar_livro_caixa(dados_base(), Decimal('200.00'))
    assert a['entradas'] == Decimal('200.00')
    assert a['entradas_por_natureza']['OMN - Oferta Missionária'] == Decimal('50.00')
    assert a['contas']['Banco/Pix']['entradas'] == Decimal('120.00')
    assert a['contas']['Dinheiro']['entradas'] == Decimal('80.00')
    assert a['saldo_final'] == Decimal('355.00')


def test_boleto_convenção_reduz_saldo_somente_uma_vez():
    a = livro.apurar_livro_caixa(dados_base(), Decimal('200.00'))
    assert a['saidas'] == Decimal('45.00')
    assert a['contas']['Banco/Pix']['saidas'] == Decimal('45.00')
    assert a['evidencias_qtd'] == 1
    assert a['evidencias_valor'] == Decimal('45.00')
    assert len(a['movimentos']) == 5
    assert a['movimentos'][-1]['saldo'] == Decimal('355.00')
    assert a['enviado_sede'] == Decimal('0.00')
    assert a['demais_saidas'] == Decimal('45.00')


def test_omn_nao_compõe_base_30_porcento_sede():
    calc = calculador_sede_real()
    a = calc(dados_base())
    assert a['total_geral'] == Decimal('200.00')
    assert a['dizimos'] == Decimal('100.00')
    assert a['ofertas_alcadas'] == Decimal('50.00')
    assert a['oferta_omn'] == Decimal('50.00')
    assert a['total_dizimos_ofertas'] == Decimal('150.00')
    assert a['valor_conselho'] == Decimal('45.0000')
    assert a['saldo_mes'] == Decimal('155.00')


def test_aumento_omn_nao_altera_valor_administrativo_30():
    calc = calculador_sede_real()
    base = calc(dados_base())
    adicional = mov(7, 'Entrada', '500.00', 'Pix', 7, 'OFERTA OMN', 'OMN extra')
    novo = calc(dados_base() + [adicional])
    assert novo['valor_conselho'] == base['valor_conselho'] == Decimal('45.00')
    assert novo['oferta_omn'] == Decimal('550.00')
    assert novo['total_geral'] - base['total_geral'] == Decimal('500.00')


def test_documentacao_vigente_preserva_regra_e_alerta_boleto():
    texto = DOC.read_text(encoding='utf-8-sig')
    assert '**OMN NÃO integra**' in texto
    assert 'o valor efetivamente recebido aumenta o saldo financeiro' in texto.lower()
    assert 'pode conter outras' in texto
    assert 'não cria, altera ou exclui' in texto
    assert 'Última revisão da regra:** 10/11/2026' in texto
