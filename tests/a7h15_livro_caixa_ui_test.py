"""A7H.15A: teste independente do acesso ao Livro Caixa simplificado pela UI."""
from pathlib import Path
from urllib.parse import urlencode

from jinja2 import Environment, StrictUndefined

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'app' / 'financeiro' / 'templates' / 'financeiro' / '_relatorio_toolbar.html'
ROUTE = ROOT / 'app' / 'financeiro' / 'financeiro_routes.py'


def _render_cabecalho(tipo, mes=7, ano=2026):
    source = TEMPLATE.read_text(encoding='utf-8-sig')
    assert '    <form method="get"' in source
    header = source.split('    <form method="get"', 1)[0] + '\n{% endif %}\n'
    jinja = Environment(autoescape=True, undefined=StrictUndefined)
    jinja.globals['url_for'] = lambda endpoint, **kw: '/' + endpoint + '?' + urlencode(kw)
    return jinja.from_string(header).render(modo_pdf=False, tipo_relatorio=tipo, mes=mes, ano=ano)


def test_livro_caixa_possui_dois_pdfs_sem_substituir_original():
    html = _render_cabecalho('livro_caixa')
    assert 'PDF Simplificado' in html
    assert 'Gerar PDF' in html
    assert 'financeiro.relatorio_caixa_pdf?mes=7&amp;ano=2026&amp;formato=livro_caixa' in html
    assert 'financeiro.relatorio_pdf?tipo_relatorio=livro_caixa&amp;mes=7&amp;ano=2026' in html
    assert 'target="_blank"' in html
    assert 'rel="noopener"' in html


def test_botao_nao_aparece_em_outros_relatorios():
    for tipo in ('gerencial', 'sede', 'auditoria'):
        html = _render_cabecalho(tipo)
        assert 'PDF Simplificado' not in html
        assert 'Gerar PDF' in html


def test_rota_autenticada_aceita_formato_opt_in():
    src = ROUTE.read_text(encoding='utf-8-sig')
    assert "@financeiro_bp.route('/financeiro/relatorio-caixa/pdf')\n@login_required\ndef relatorio_caixa_pdf():" in src
    assert "request.args.get('formato', '').strip().lower() == 'livro_caixa'" in src
    assert 'from app.utils.livro_caixa_simplificado import gerar_livro_caixa_simplificado' in src


def test_arquivo_jinja_completo_continua_sintaticamente_valido():
    src = TEMPLATE.read_text(encoding='utf-8-sig')
    Environment().parse(src)
    assert src.count('PDF Simplificado') == 1
