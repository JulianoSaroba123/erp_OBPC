"""P0.3E1: fundacao CSRF isolada, sem importar a app real nem acessar DB."""
from pathlib import Path
import ast
import re
from flask import Flask, request
from flask_wtf.csrf import CSRFProtect, generate_csrf

ROOT = Path(__file__).resolve().parents[1]


def test_dependencia_fixada_no_requirements():
    req = (ROOT / 'requirements.txt').read_text(encoding='utf-8-sig')
    assert re.search(r'^Flask-WTF==1\.3\.0\s*$', req, re.M)


def test_extensao_csrf_registrada_sem_ativar_validacao_automatica():
    ext = (ROOT / 'app/extensoes.py').read_text(encoding='utf-8-sig')
    ini = (ROOT / 'app/__init__.py').read_text(encoding='utf-8-sig')
    ast.parse(ext)
    tree = ast.parse(ini)
    assert 'csrf = CSRFProtect()' in ext
    create = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'create_app')
    source = ast.get_source_segment(ini, create)
    assert "app.config['WTF_CSRF_CHECK_DEFAULT'] = False" in source
    assert 'csrf.init_app(app)' in source
    assert source.index("app.config['WTF_CSRF_CHECK_DEFAULT'] = False") < source.index('csrf.init_app(app)')


def _mini_app():
    app = Flask(__name__)
    app.config.update(SECRET_KEY='somente-para-testes-123456789', WTF_CSRF_CHECK_DEFAULT=False)
    csrf = CSRFProtect(app)

    @app.get('/token')
    def token():
        return generate_csrf()

    @app.post('/sem-protecao')
    def sem_protecao():
        return 'ok'

    @app.post('/com-protecao')
    def com_protecao():
        csrf.protect()
        return 'ok'

    return app


def test_sem_ativacao_global_post_continua_funcional():
    assert _mini_app().test_client().post('/sem-protecao').status_code == 200


def test_protecao_explicita_rejeita_post_sem_token():
    assert _mini_app().test_client().post('/com-protecao').status_code == 400


def test_protecao_explicita_rejeita_token_invalido():
    assert _mini_app().test_client().post('/com-protecao', data={'csrf_token': 'invalido'}).status_code == 400


def test_protecao_explicita_aceita_token_valido():
    client = _mini_app().test_client()
    token = client.get('/token').get_data(as_text=True)
    assert client.post('/com-protecao', data={'csrf_token': token}).status_code == 200
