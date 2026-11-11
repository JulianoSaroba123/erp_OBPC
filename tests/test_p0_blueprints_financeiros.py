import ast
import importlib.util
from pathlib import Path

import pytest
from flask import Blueprint, Flask, jsonify
from flask_login import LoginManager, UserMixin, login_user


RAIZ = Path(__file__).resolve().parents[1]

ARQUIVOS = [
    (
        "app/financeiro/financeiro_routes.py",
        "financeiro_bp",
        50,
    ),
    (
        "app/financeiro/routes_conciliacao.py",
        "conciliacao_bp",
        10,
    ),
]

spec = importlib.util.spec_from_file_location(
    "obpc_auth_p0",
    RAIZ / "app/utils/auth_decorators.py",
)

auth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth)


class UsuarioSimulado(UserMixin):
    def __init__(self, perfil):
        self.id = perfil
        self.nivel_acesso = perfil

    def tem_acesso_financeiro(self):
        return self.nivel_acesso in {
            "master",
            "administrador",
            "tesoureiro",
            "Admin",
        }


@pytest.fixture(params=ARQUIVOS, ids=["financeiro", "conciliacao"])
def cliente_protegido(request):
    relativo, nome_blueprint, minimo_rotas = request.param

    caminho = RAIZ / relativo
    arvore = ast.parse(
        caminho.read_text(encoding="utf-8-sig"),
        filename=str(caminho),
    )

    guardas = [
        node
        for node in arvore.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_validar_acesso_financeiro_blueprint"
    ]

    assert len(guardas) == 1, (
        f"Guarda ausente ou duplicada: {relativo}"
    )

    guarda = guardas[0]

    decoradores = {
        ast.unparse(node)
        for node in guarda.decorator_list
    }

    assert f"{nome_blueprint}.before_request" in decoradores
    assert "requer_acesso_financeiro" in decoradores

    rotas = [
        node
        for node in arvore.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        if any(
            isinstance(decorador, ast.Call)
            and isinstance(decorador.func, ast.Attribute)
            and isinstance(decorador.func.value, ast.Name)
            and decorador.func.value.id == nome_blueprint
            and decorador.func.attr == "route"
            for decorador in node.decorator_list
        )
    ]

    assert len(rotas) >= minimo_rotas, (
        f"Cobertura de rotas inesperada: {relativo}"
    )

    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SECRET_KEY="chave-exclusiva-dos-testes-p0",
    )

    login_manager = LoginManager(app)
    usuarios = {}

    @login_manager.user_loader
    def carregar_usuario(identificador):
        return usuarios.get(identificador)

    @app.route("/login", endpoint="usuario.login")
    def login():
        return "Login ficticio"

    @app.route("/simular-login/<perfil>")
    def simular_login(perfil):
        usuario = UsuarioSimulado(perfil)
        usuarios[perfil] = usuario
        login_user(usuario)
        return "ok"

    blueprint = Blueprint(nome_blueprint, __name__)

    ambiente = {
        nome_blueprint: blueprint,
        "requer_acesso_financeiro": auth.requer_acesso_financeiro,
    }

    modulo = ast.Module(
        body=[guarda],
        type_ignores=[],
    )

    exec(
        compile(modulo, str(caminho), "exec"),
        ambiente,
    )

    @blueprint.route("/teste", methods=["GET", "POST"])
    def teste():
        return "rota protegida"

    @blueprint.route("/api/teste")
    def teste_api():
        return jsonify({"success": True})

    app.register_blueprint(
        blueprint,
        url_prefix="/__p0__",
    )

    with app.test_client() as cliente:
        yield cliente


@pytest.mark.parametrize(
    "perfil",
    ["master", "administrador", "tesoureiro", "Admin"],
)
def test_perfil_autorizado(cliente_protegido, perfil):
    cliente_protegido.get(f"/simular-login/{perfil}")

    resposta = cliente_protegido.get("/__p0__/teste")

    assert resposta.status_code == 200


@pytest.mark.parametrize(
    "perfil",
    ["membro", "secretario", "midia"],
)
def test_perfil_sem_permissao(cliente_protegido, perfil):
    cliente_protegido.get(f"/simular-login/{perfil}")

    resposta = cliente_protegido.get("/__p0__/teste")

    assert resposta.status_code == 403


def test_anonimo_redirecionado(cliente_protegido):
    resposta = cliente_protegido.get("/__p0__/teste")

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_api_anonima_retorna_401(cliente_protegido):
    resposta = cliente_protegido.get(
        "/__p0__/api/teste",
        headers={"Accept": "application/json"},
    )

    assert resposta.status_code == 401


def test_api_sem_permissao_retorna_403(cliente_protegido):
    cliente_protegido.get("/simular-login/membro")

    resposta = cliente_protegido.get(
        "/__p0__/api/teste",
        headers={"Accept": "application/json"},
    )

    assert resposta.status_code == 403


def test_post_sem_permissao_retorna_403(cliente_protegido):
    cliente_protegido.get("/simular-login/membro")

    resposta = cliente_protegido.post("/__p0__/teste")

    assert resposta.status_code == 403
