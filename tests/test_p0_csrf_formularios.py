"""P0.3E2: tokens nos formulários, cabeçalhos AJAX; testes sem banco real."""
from html.parser import HTMLParser
from pathlib import Path
import re

from flask import Flask, render_template_string
from flask_wtf.csrf import CSRFProtect

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'app/financeiro/templates/financeiro'
FORM_RE = re.compile(r'<form\b[^>]*>', re.I | re.S)
POST_RE = re.compile(r'\bmethod\s*=\s*([\'\"])post\1', re.I)
HIDDEN = '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'
EXPECTED = {
    '_relatorio_toolbar.html': 1, 'cadastro_lancamento.html': 2,
    'cadastro_projeto.html': 1, 'conciliacao.html': 5,
    'conciliacao_moderno.html': 4, 'editar_recibo.html': 1,
    'emitir_recibo.html': 1, 'gerenciar_despesas_fixas.html': 10,
    'import_preview.html': 1, 'importar_extrato.html': 1,
    'lista_lancamentos.html': 1, 'lista_lancamentos_moderno.html': 1,
    'lista_projetos.html': 1, 'lista_recibos.html': 1,
    'visualizar_recibo.html': 1,
}


def html_files():
    return {
        p.name: p.read_text(encoding='utf-8-sig')
        for p in FOLDER.glob('*.html')
    }


def post_tags(text):
    return [m for m in FORM_RE.finditer(text) if POST_RE.search(m.group(0))]


def test_distribuicao_dos_32_formularios():
    result = {
        filename: len(post_tags(content))
        for filename, content in html_files().items() if post_tags(content)
    }
    assert result == EXPECTED
    assert sum(result.values()) == 32


def test_todos_os_post_tem_token_imediatamente_apos_abertura():
    total = 0
    for name, source in html_files().items():
        for tag in post_tags(source):
            assert source.startswith(HIDDEN, tag.end()), f'{name}: token ausente apos form'
            total += 1
    assert total == 32


def test_forms_get_nao_receberam_token_acidentalmente():
    for name, source in html_files().items():
        for tag in FORM_RE.finditer(source):
            if not POST_RE.search(tag.group(0)):
                assert not source.startswith(HIDDEN, tag.end()), name


def test_token_especifico_nas_exclusoes_e_uploads():
    for name in ('lista_lancamentos.html', 'lista_lancamentos_moderno.html',
                 'importar_extrato.html', 'cadastro_lancamento.html',
                 'visualizar_recibo.html'):
        source = html_files()[name]
        assert post_tags(source)
        assert all(source.startswith(HIDDEN, tag.end()) for tag in post_tags(source))


def test_despesas_fixas_tem_dez_tokens():
    source = html_files()['gerenciar_despesas_fixas.html']
    assert len(post_tags(source)) == 10
    assert source.count(HIDDEN) == 10


def test_chamadas_ajax_post_recebem_header_csrf():
    expected = {'conciliacao_manual.html': 2, 'dashboard_conciliacao.html': 1}
    for name, count in expected.items():
        text = html_files()[name]
        assert text.count("headers: {'X-CSRFToken': '{{ csrf_token() }}'},") == count
        assert len(re.findall(r"type\s*:\s*['\"]POST['\"]\s*,\s*\n\s*headers:\s*\{'X-CSRFToken':", text)) == count


def test_ajax_get_somente_consulta_nao_exige_token():
    for name in ('conciliacao_manual.html', 'dashboard_conciliacao.html'):
        text = html_files()[name]
        assert len(re.findall(r"type\s*:\s*['\"]GET['\"]", text)) == 1
        assert not re.search(r"type\s*:\s*['\"]GET['\"],\s*\n\s*headers:\s*\{'X-CSRFToken':", text)


def test_token_jinja_renderiza_em_aplicacao_isolada():
    app = Flask(__name__)
    app.config.update(SECRET_KEY='teste-local-nao-producao', WTF_CSRF_CHECK_DEFAULT=False)
    CSRFProtect(app)
    with app.test_request_context('/'):
        rendered = render_template_string('<form method="POST">' + HIDDEN + '</form>')
        assert 'name="csrf_token"' in rendered
        assert 'value="{{' not in rendered
        assert re.search(r'name="csrf_token" value="[A-Za-z0-9._-]+"', rendered)


def test_csrf_automatico_ainda_desativado():
    source = (ROOT / 'app/__init__.py').read_text(encoding='utf-8-sig')
    assert "app.config['WTF_CSRF_CHECK_DEFAULT'] = False" in source
    assert 'csrf.init_app(app)' in source
