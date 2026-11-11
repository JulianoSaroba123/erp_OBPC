"""P0.4B: testes HTTP isolados do handler 500, sem importar create_app ou DB."""
import ast
import copy
from pathlib import Path
from unittest.mock import patch

from flask import Flask

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'app/__init__.py'
SENTINEL = 'SEGREDO_INTERNO_500_NAO_PODE_APARECER'


def _handler_source():
    text = SOURCE.read_text(encoding='utf-8-sig')
    tree = ast.parse(text)
    factory = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'create_app')
    handler = next(n for n in factory.body if isinstance(n, ast.FunctionDef) and n.name == 'internal_error')
    assert len(handler.decorator_list) == 1
    return handler, text


def _mini_app():
    # Extrai o handler de dentro do factory: importar o ERP ou abrir BD e proibido.
    function, _ = _handler_source()
    app = Flask(__name__)
    app.config.update(TESTING=False, PROPAGATE_EXCEPTIONS=False)
    context = {'app': app}
    body = ast.Module(body=[copy.deepcopy(function)], type_ignores=[])
    ast.fix_missing_locations(body)
    exec(compile(body, str(SOURCE), 'exec'), context)

    @app.get('/falha-controlada')
    def erro_html():
        raise RuntimeError(SENTINEL)

    @app.get('/usuarios/falha-controlada')
    def erro_json():
        raise RuntimeError(SENTINEL)

    @app.get('/funcionando')
    def funcionando():
        return 'ok'

    return app


def test_handler_registrado_para_500():
    handler, _ = _handler_source()
    assert any(isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
               and d.func.attr == 'errorhandler' and ast.literal_eval(d.args[0]) == 500
               for d in handler.decorator_list)


def test_html_retorna_500_sem_detalhes_internos():
    app = _mini_app()
    with patch.object(app.logger, 'error'):
        r = app.test_client().get('/falha-controlada')
    text = r.get_data(as_text=True)
    assert r.status_code == 500
    assert 'Erro Interno' in text
    assert SENTINEL not in text
    assert 'Traceback' not in text
    assert '<pre>' not in text


def test_json_usuarios_retorna_500_sem_detalhes_internos():
    app = _mini_app()
    with patch.object(app.logger, 'error'):
        r = app.test_client().get('/usuarios/falha-controlada')
    assert r.status_code == 500
    assert r.is_json
    payload = r.get_json()
    assert payload == {'error': 'Erro interno do servidor.'}
    assert SENTINEL not in r.get_data(as_text=True)
    assert 'traceback' not in payload
    assert 'path' not in payload


def test_logs_de_diagnostico_continuam_ativos():
    app = _mini_app()
    with patch.object(app.logger, 'error') as log:
        r = app.test_client().get('/falha-controlada')
    assert r.status_code == 500
    assert log.call_count >= 1
    assert any('ERRO 500' in str(c.args[0]) for c in log.call_args_list)


def test_requisicoes_normais_nao_sao_modificadas():
    assert _mini_app().test_client().get('/funcionando').status_code == 200


def test_nao_altera_secret_key_ou_protecao_de_sessao():
    _, text = _handler_source()
    assert "app.config['WTF_CSRF_CHECK_DEFAULT'] = False" in text
    assert 'csrf.init_app(app)' in text
    assert 'login_manager.session_protection = None' in text
    config = (ROOT / 'app/config.py').read_text(encoding='utf-8-sig')
    assert "SECRET_KEY = os.environ.get('SECRET_KEY') or None" in config
    assert "chave-secreta-obpc-2025-igreja-brasil-para-cristo" not in config
