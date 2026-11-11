import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest
from flask import Blueprint, Flask, flash, redirect, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user
from jinja2 import Environment


RAIZ = Path(__file__).resolve().parents[1]
ROTA = RAIZ / "app/financeiro/financeiro_routes.py"
PAGINA = (
    RAIZ / "app/financeiro/templates/financeiro/lista_lancamentos.html"
)

spec = importlib.util.spec_from_file_location(
    "obpc_auth_exclusao_p0",
    RAIZ / "app/utils/auth_decorators.py",
)
auth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth)


class UsuarioSimulado(UserMixin):
    def __init__(self, perfil):
        self.id = perfil
        self.perfil = perfil

    def tem_acesso_financeiro(self):
        return self.perfil in {
            "master", "administrador", "tesoureiro", "Admin"
        }


class SessaoSimulada:
    def __init__(self):
        self.exclusoes = []
        self.commits = 0

    def delete(self, lancamento):
        self.exclusoes.append(lancamento)

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass


class ConsultaSimulada:
    def __init__(self):
        self.consultas = []

    def get_or_404(self, identificador):
        self.consultas.append(identificador)
        return SimpleNamespace(
            descricao="Lancamento ficticio",
            tipo="Saida",
            valor_formatado="R$ 10,00",
        )


@pytest.fixture
def ambiente():
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SECRET_KEY="exclusiva-testes-obpc-p0",
    )

    login_manager = LoginManager(app)
    usuarios = {}
    sessao = SessaoSimulada()
    consulta = ConsultaSimulada()

    @login_manager.user_loader
    def carregar_usuario(identificador):
        return usuarios.get(identificador)

    usuario_bp = Blueprint("usuario", __name__)

    @usuario_bp.route("/login")
    def login():
        return "Login ficticio"

    app.register_blueprint(usuario_bp)

    @app.route("/simular-login/<perfil>")
    def simular_login(perfil):
        usuario = UsuarioSimulado(perfil)
        usuarios[perfil] = usuario
        login_user(usuario)
        return "ok"

    financeiro_bp = Blueprint("financeiro", __name__)

    @financeiro_bp.route("/financeiro/lancamentos")
    def lista_lancamentos():
        return "Lista ficticia"

    arvore = ast.parse(
        ROTA.read_text(encoding="utf-8-sig"),
        filename=str(ROTA),
    )

    nomes = {
        "_validar_acesso_financeiro_blueprint",
        "excluir_lancamento",
    }

    funcoes = [
        no for no in arvore.body
        if isinstance(no, ast.FunctionDef) and no.name in nomes
    ]

    assert len(funcoes) == 2

    ambiente_execucao = {
        "financeiro_bp": financeiro_bp,
        "requer_acesso_financeiro": auth.requer_acesso_financeiro,
        "login_required": login_required,
        "Lancamento": SimpleNamespace(query=consulta),
        "db": SimpleNamespace(session=sessao),
        "flash": flash,
        "redirect": redirect,
        "url_for": url_for,
        "obter_filtros_ativos": lambda: {},
    }

    modulo = ast.Module(body=funcoes, type_ignores=[])

    exec(
        compile(modulo, str(ROTA), "exec"),
        ambiente_execucao,
    )

    app.register_blueprint(financeiro_bp)

    with app.test_client() as cliente:
        yield cliente, sessao, consulta


def test_get_nao_exclui(ambiente):
    cliente, sessao, consulta = ambiente
    cliente.get("/simular-login/master")

    resposta = cliente.get("/financeiro/excluir/7")

    assert resposta.status_code == 405
    assert sessao.commits == 0
    assert sessao.exclusoes == []
    assert consulta.consultas == []


def test_head_nao_exclui(ambiente):
    cliente, sessao, consulta = ambiente
    cliente.get("/simular-login/master")

    resposta = cliente.head("/financeiro/excluir/7")

    assert resposta.status_code == 405
    assert sessao.commits == 0
    assert consulta.consultas == []


def test_post_autorizado_exclui(ambiente):
    cliente, sessao, consulta = ambiente
    cliente.get("/simular-login/master")

    resposta = cliente.post("/financeiro/excluir/7")

    assert resposta.status_code == 302
    assert sessao.commits == 1
    assert len(sessao.exclusoes) == 1
    assert consulta.consultas == [7]


def test_post_membro_bloqueado(ambiente):
    cliente, sessao, consulta = ambiente
    cliente.get("/simular-login/membro")

    resposta = cliente.post("/financeiro/excluir/7")

    assert resposta.status_code == 403
    assert sessao.commits == 0
    assert sessao.exclusoes == []
    assert consulta.consultas == []


def test_post_anonimo_bloqueado(ambiente):
    cliente, sessao, consulta = ambiente

    resposta = cliente.post("/financeiro/excluir/7")

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]
    assert sessao.commits == 0
    assert consulta.consultas == []


def test_template_usa_formulario_post():
    html = PAGINA.read_text(encoding="utf-8-sig")
    Environment().parse(html)

    assert html.count("financeiro.excluir_lancamento") == 1

    linhas = [
        linha for linha in html.splitlines()
        if "financeiro.excluir_lancamento" in linha
    ]

    assert len(linhas) == 1
    assert "<form" in linhas[0]
    assert 'method="POST"' in linhas[0]
    assert 'onsubmit="return confirm(' in linhas[0]
    assert 'class="d-inline"' in linhas[0]
