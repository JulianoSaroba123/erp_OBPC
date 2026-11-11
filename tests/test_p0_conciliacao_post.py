"""P0.2B: testes isolados com as funções reais extraídas por AST.

O ERP não é inicializado e nenhum dado financeiro real é carregado.
"""
import ast
import importlib.util
import io
import os
from datetime import datetime
from pathlib import Path

import pytest
from flask import Blueprint, Flask, flash, jsonify, redirect, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user
from werkzeug.utils import secure_filename

RAIZ = Path(__file__).resolve().parents[1]
ROTAS = RAIZ / "app/financeiro/routes_conciliacao.py"
AUTH = RAIZ / "app/utils/auth_decorators.py"

spec = importlib.util.spec_from_file_location("auth_obpc_p02b_isolado", AUTH)
auth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth)


class UsuarioFicticio(UserMixin):
    def __init__(self, perfil):
        self.id = perfil
        self.nome = "Usuario de teste"
        self.perfil = perfil

    def tem_acesso_financeiro(self):
        return self.perfil in ("master", "administrador", "tesoureiro", "Admin")


@pytest.fixture
def ambiente(tmp_path):
    arvore = ast.parse(ROTAS.read_text(encoding="utf-8-sig"), filename=str(ROTAS))
    nomes = {
        "_validar_acesso_financeiro_blueprint",
        "executar_conciliacao_auto",
        "upload_extrato",
    }
    funcoes = [
        no for no in arvore.body
        if isinstance(no, ast.FunctionDef) and no.name in nomes
    ]
    assert len(funcoes) == 3, "Guardas e funções reais devem ser únicos"
    auto = next(no for no in funcoes if no.name == "executar_conciliacao_auto")
    metodos = []
    for decorador in auto.decorator_list:
        if (isinstance(decorador, ast.Call)
                and ast.unparse(decorador.func) == "conciliacao_bp.route"):
            metodos.extend(
                ast.literal_eval(kw.value)
                for kw in decorador.keywords if kw.arg == "methods"
            )
    assert metodos == [["POST"], ["POST"]], "Ambas as rotas devem usar somente POST"

    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="chave-so-para-testes-p02b")
    usuarios = {}
    gerenciador = LoginManager(app)

    @gerenciador.user_loader
    def carregar_usuario(identificador):
        return usuarios.get(identificador)

    usuario_bp = Blueprint("usuario", __name__)

    @usuario_bp.route("/login")
    def login():
        return "Login fictício"

    app.register_blueprint(usuario_bp)

    @app.route("/simular-login/<perfil>")
    def simular_login(perfil):
        usuario = UsuarioFicticio(perfil)
        usuarios[perfil] = usuario
        login_user(usuario)
        return "OK"

    eventos = {"importacoes": [], "conciliacoes": [], "processados": 1}

    class ImportadorFicticio:
        def importar_arquivo(self, arquivo_path, banco, usuario):
            caminho = Path(arquivo_path)
            assert caminho.parent.resolve() == tmp_path.resolve()
            assert caminho.read_bytes() == b"movimento-ficticio"
            eventos["importacoes"].append((banco, usuario))
            return {
                "sucesso": True,
                "registros_processados": eventos["processados"],
                "registros_duplicados": 0,
                "registros_erro": 0,
                "importacao_id": 42,
            }

    class ConciliadorFicticio:
        def conciliar_automatico(self, usuario):
            eventos["conciliacoes"].append(usuario)
            return {"conciliados": 1, "tempo_execucao": 0.01}

    conciliacao_bp = Blueprint("conciliacao", __name__)

    @conciliacao_bp.route("/financeiro/conciliacao/dashboard")
    def dashboard_conciliacao():
        return "Dashboard fictício"

    @conciliacao_bp.route("/financeiro/conciliacao/importar-extrato")
    def importar_extrato():
        return "Página fictícia de importação"

    contexto = {
        "conciliacao_bp": conciliacao_bp,
        "requer_acesso_financeiro": auth.requer_acesso_financeiro,
        "login_required": login_required,
        "current_user": current_user,
        "request": request,
        "redirect": redirect,
        "url_for": url_for,
        "flash": flash,
        "jsonify": jsonify,
        "os": os,
        "datetime": datetime,
        "secure_filename": secure_filename,
        "UPLOAD_FOLDER": str(tmp_path),
        "allowed_file": lambda nome: nome.lower().endswith(".csv"),
        "ImportadorExtrato": ImportadorFicticio,
        "ConciliadorAvancado": ConciliadorFicticio,
    }
    exec(compile(ast.Module(body=funcoes, type_ignores=[]), str(ROTAS), "exec"), contexto)
    app.register_blueprint(conciliacao_bp)

    with app.test_client() as client:
        yield client, eventos, tmp_path


@pytest.mark.parametrize("caminho", [
    "/financeiro/conciliacao/executar-automatica",
    "/financeiro/conciliacao/executar-automatica/42",
])
@pytest.mark.parametrize("verbo", ["get", "head"])
def test_get_head_bloqueados_sem_conciliar(ambiente, caminho, verbo):
    cliente, eventos, _ = ambiente
    cliente.get("/simular-login/master")
    resposta = getattr(cliente, verbo)(caminho)
    assert resposta.status_code == 405
    assert eventos["conciliacoes"] == []
    assert eventos["importacoes"] == []


@pytest.mark.parametrize("caminho", [
    "/financeiro/conciliacao/executar-automatica",
    "/financeiro/conciliacao/executar-automatica/42",
])
def test_post_autorizado_concilia_uma_vez(ambiente, caminho):
    cliente, eventos, _ = ambiente
    cliente.get("/simular-login/tesoureiro")
    resposta = cliente.post(caminho)
    assert resposta.status_code == 302
    assert len(eventos["conciliacoes"]) == 1
    assert eventos["importacoes"] == []
    assert "/financeiro/conciliacao/dashboard" in resposta.headers["Location"]


def test_post_perfil_sem_permissao_nao_concilia(ambiente):
    cliente, eventos, _ = ambiente
    cliente.get("/simular-login/membro")
    resposta = cliente.post("/financeiro/conciliacao/executar-automatica")
    assert resposta.status_code == 403
    assert eventos["conciliacoes"] == []


def test_post_anonimo_nao_concilia(ambiente):
    cliente, eventos, _ = ambiente
    resposta = cliente.post("/financeiro/conciliacao/executar-automatica")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]
    assert eventos["conciliacoes"] == []


def _arquivo_ficticio():
    return {"arquivo": (io.BytesIO(b"movimento-ficticio"), "extrato-teste.csv"), "banco": "generico"}


def test_upload_processado_executa_conciliacao_sem_get(ambiente):
    cliente, eventos, pasta_temporaria = ambiente
    cliente.get("/simular-login/master")
    resposta = cliente.post(
        "/financeiro/conciliacao/upload-extrato",
        data=_arquivo_ficticio(), content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert resposta.status_code == 302
    assert len(eventos["importacoes"]) == 1
    assert len(eventos["conciliacoes"]) == 1
    assert "/financeiro/conciliacao/dashboard" in resposta.headers["Location"]
    assert "executar-automatica" not in resposta.headers["Location"]
    assert list(pasta_temporaria.iterdir()) == []


def test_upload_vazio_nao_concilia(ambiente):
    cliente, eventos, pasta_temporaria = ambiente
    eventos["processados"] = 0
    cliente.get("/simular-login/master")
    resposta = cliente.post(
        "/financeiro/conciliacao/upload-extrato",
        data=_arquivo_ficticio(), content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert resposta.status_code == 302
    assert len(eventos["importacoes"]) == 1
    assert eventos["conciliacoes"] == []
    assert list(pasta_temporaria.iterdir()) == []


def test_upload_sem_permissao_nao_importa(ambiente):
    cliente, eventos, _ = ambiente
    cliente.get("/simular-login/midia")
    resposta = cliente.post(
        "/financeiro/conciliacao/upload-extrato",
        data=_arquivo_ficticio(), content_type="multipart/form-data",
    )
    assert resposta.status_code == 403
    assert eventos["importacoes"] == []
    assert eventos["conciliacoes"] == []


def test_upload_anonimo_nao_importa(ambiente):
    cliente, eventos, _ = ambiente
    resposta = cliente.post(
        "/financeiro/conciliacao/upload-extrato",
        data=_arquivo_ficticio(), content_type="multipart/form-data",
    )
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]
    assert eventos["importacoes"] == []
    assert eventos["conciliacoes"] == []
