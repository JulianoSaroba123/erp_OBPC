import importlib.util
from pathlib import Path

import pytest
from flask import Blueprint, Flask, jsonify
from flask_login import LoginManager, UserMixin, login_user


ARQUIVO = (
    Path(__file__).resolve().parents[1]
    / "app/utils/auth_decorators.py"
)

spec = importlib.util.spec_from_file_location(
    "obpc_auth_teste", ARQUIVO
)
auth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth)


class UsuarioSimulado(UserMixin):
    def __init__(self, perfil):
        self.id = perfil
        self.nivel_acesso = perfil

    def tem_acesso_financeiro(self):
        return self.nivel_acesso in (
            "master",
            "administrador",
            "tesoureiro",
            "Admin",
        )


@pytest.fixture
def cliente():
    app = Flask(__name__)

    app.config.update(
        TESTING=True,
        SECRET_KEY="chave-ficticia-exclusiva-para-testes",
    )

    gerenciador = LoginManager(app)
    usuarios = {}

    @gerenciador.user_loader
    def carregar_usuario(identificador):
        return usuarios.get(identificador)

    usuario_bp = Blueprint("usuario", __name__)

    @usuario_bp.route("/login")
    def login():
        return "Login de teste"

    app.register_blueprint(usuario_bp)

    @app.route("/simular-login/<perfil>")
    def simular_login(perfil):
        usuario = UsuarioSimulado(perfil)
        usuarios[perfil] = usuario
        login_user(usuario)
        return "ok"

    @app.route("/financeiro/protegido")
    @auth.requer_acesso_financeiro
    def protegido():
        return "acesso liberado"

    @app.route("/financeiro/api/protegido")
    @auth.requer_acesso_financeiro
    def protegido_api():
        return jsonify({"success": True})

    @app.route("/financeiro/erro")
    @auth.requer_acesso_financeiro
    def erro_proposital():
        raise RuntimeError("erro proposital do teste")

    with app.test_client() as client:
        yield client


@pytest.mark.parametrize(
    "perfil",
    ["master", "administrador", "tesoureiro", "Admin"],
)
def test_perfis_autorizados(cliente, perfil):
    cliente.get(f"/simular-login/{perfil}")

    resposta = cliente.get("/financeiro/protegido")

    assert resposta.status_code == 200


@pytest.mark.parametrize(
    "perfil",
    ["secretario", "midia", "membro"],
)
def test_perfis_sem_permissao(cliente, perfil):
    cliente.get(f"/simular-login/{perfil}")

    resposta = cliente.get("/financeiro/protegido")

    assert resposta.status_code == 403


def test_anonimo_redirecionado(cliente):
    resposta = cliente.get("/financeiro/protegido")

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_api_anonima_retorna_401(cliente):
    resposta = cliente.get(
        "/financeiro/api/protegido",
        headers={"Accept": "application/json"},
    )

    assert resposta.status_code == 401


def test_api_sem_permissao_retorna_403(cliente):
    cliente.get("/simular-login/membro")

    resposta = cliente.get(
        "/financeiro/api/protegido",
        headers={"Accept": "application/json"},
    )

    assert resposta.status_code == 403


def test_ajax_anonimo_retorna_401(cliente):
    resposta = cliente.get(
        "/financeiro/api/protegido",
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    assert resposta.status_code == 401


def test_excecao_nao_e_ocultada(cliente):
    cliente.get("/simular-login/master")

    with pytest.raises(
        RuntimeError,
        match="erro proposital do teste",
    ):
        cliente.get("/financeiro/erro")
