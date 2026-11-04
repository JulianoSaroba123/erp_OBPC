"""P0.3F: exercita guards extraidos do codigo real, sem iniciar o ERP ou banco."""
import ast
import importlib.util
from pathlib import Path
import pytest
from flask import Blueprint, Flask, request
from flask_login import LoginManager, UserMixin, login_user
from flask_wtf.csrf import CSRFProtect, generate_csrf

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    'financeiro': ROOT / 'app/financeiro/financeiro_routes.py',
    'conciliacao': ROOT / 'app/financeiro/routes_conciliacao.py',
}
AUTH = ROOT / 'app/utils/auth_decorators.py'

spec = importlib.util.spec_from_file_location('auth_obpc_p03f_isolado', AUTH)
auth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth)


class UsuarioTeste(UserMixin):
    def __init__(self, perfil):
        self.id = perfil
        self.perfil = perfil

    def tem_acesso_financeiro(self):
        return self.perfil in ('master', 'administrador', 'tesoureiro', 'Admin')


def extrair_guardas(nome):
    source = FILES[nome].read_text(encoding='utf-8-sig')
    tree = ast.parse(source)
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)
             and n.name in ('_validar_acesso_financeiro_blueprint','_validar_csrf_financeiro_blueprint')]
    assert len(funcs) == 2
    assert [n.name for n in funcs] == ['_validar_acesso_financeiro_blueprint', '_validar_csrf_financeiro_blueprint']
    for fn in funcs:
        assert any(isinstance(d, ast.Attribute) and d.attr == 'before_request' and
                   isinstance(d.value, ast.Name) and d.value.id == f'{nome}_bp'
                   for d in fn.decorator_list)
    csrf_fn = funcs[1]
    assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and isinstance(n.func.value, ast.Name) and n.func.value.id == 'csrf'
               and n.func.attr == 'protect' for n in ast.walk(csrf_fn))
    return funcs


@pytest.fixture(params=['financeiro', 'conciliacao'])
def app_isolada(request):
    nome = request.param
    app = Flask('csrf_p03f_' + nome)
    app.config.update(TESTING=True, SECRET_KEY='chave-exclusiva-somente-testes-p03f',
                      WTF_CSRF_CHECK_DEFAULT=False)
    csrf = CSRFProtect(app)
    usuarios = {}
    lm = LoginManager(app)

    @lm.user_loader
    def load_user(uid):
        return usuarios.get(uid)

    usuario_bp = Blueprint('usuario', __name__)
    @usuario_bp.get('/login')
    def login():
        return 'login ficticio'
    app.register_blueprint(usuario_bp)

    @app.get('/simular-login/<perfil>')
    def simular_login(perfil):
        usuario = UsuarioTeste(perfil)
        usuarios[perfil] = usuario
        login_user(usuario)
        return 'autenticado'

    @app.post('/fora-do-financeiro')
    def fora():
        return 'fora sem bloqueio', 200

    bp = Blueprint(nome, __name__)
    contexto = {
        f'{nome}_bp': bp,
        'requer_acesso_financeiro': auth.requer_acesso_financeiro,
        'csrf': csrf,
        'request': request_flask,
    }
    funcs = extrair_guardas(nome)
    exec(compile(ast.Module(body=funcs, type_ignores=[]), str(FILES[nome]), 'exec'), contexto)

    eventos = []
    @bp.get('/token')
    def token():
        return generate_csrf()
    @bp.get('/consulta')
    def consulta():
        return 'consulta', 200
    @bp.post('/mutacao')
    def mutacao():
        eventos.append('gravou-somente-ficticio')
        return 'gravou', 200

    app.register_blueprint(bp)
    with app.test_client() as cliente:
        yield nome, cliente, eventos


from flask import request as request_flask


def caminho(nome, parte):
    return '/' + parte


def test_consulta_get_autorizada_sem_token(app_isolada):
    _, client, eventos = app_isolada
    client.get('/simular-login/tesoureiro')
    assert client.get('/consulta').status_code == 200
    assert eventos == []


def test_post_sem_token_rejeitado_antes_de_mutar(app_isolada):
    _, client, eventos = app_isolada
    client.get('/simular-login/tesoureiro')
    assert client.post('/mutacao').status_code == 400
    assert eventos == []


def test_post_com_token_invalido_rejeitado(app_isolada):
    _, client, eventos = app_isolada
    client.get('/simular-login/master')
    assert client.post('/mutacao', data={'csrf_token': 'incorreto'}).status_code == 400
    assert eventos == []


def test_post_com_token_formulario_valido(app_isolada):
    _, client, eventos = app_isolada
    client.get('/simular-login/tesoureiro')
    token = client.get('/token').get_data(as_text=True)
    assert client.post('/mutacao', data={'csrf_token': token}).status_code == 200
    assert len(eventos) == 1


def test_post_com_header_ajax_valido(app_isolada):
    _, client, eventos = app_isolada
    client.get('/simular-login/administrador')
    token = client.get('/token').get_data(as_text=True)
    assert client.post('/mutacao', headers={'X-CSRFToken': token}).status_code == 200
    assert len(eventos) == 1


def test_perfil_sem_permissao_retorna_403_antes_de_csrf(app_isolada):
    _, client, eventos = app_isolada
    client.get('/simular-login/membro')
    assert client.post('/mutacao').status_code == 403
    assert eventos == []


def test_anonimo_redirecionado_antes_de_csrf(app_isolada):
    _, client, eventos = app_isolada
    assert client.post('/mutacao').status_code == 302
    assert eventos == []


def test_fora_do_financeiro_nao_exige_token(app_isolada):
    _, client, eventos = app_isolada
    assert client.post('/fora-do-financeiro').status_code == 200
    assert eventos == []


def test_csrf_nao_foi_habilitado_globalmente():
    source = (ROOT / 'app/__init__.py').read_text(encoding='utf-8-sig')
    assert "app.config['WTF_CSRF_CHECK_DEFAULT'] = False" in source
    assert 'csrf.init_app(app)' in source


def test_importacao_requirements_preservada():
    req = (ROOT / 'requirements.txt').read_text(encoding='utf-8-sig')
    assert 'Flask-WTF==1.3.0' in req
