"""A7H.27: testes isolados de revogacao Flask-Login, sem banco externo."""
import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parents[1]
HELPER = RAIZ / "app" / "usuario" / "sessao_segura.py"
MODELO = RAIZ / "app" / "usuario" / "usuario_model.py"


def importar_helper():
    spec = importlib.util.spec_from_file_location("obpc_a7h27_sessao", HELPER)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def testar_loader_real_em_isolamento(manager, usuarios, helper):
    """Compila o callback REAL de usuario_model, com banco ficticio em memoria."""
    from flask import current_app

    arvore = ast.parse(MODELO.read_text(encoding="utf-8-sig"))
    callback = next(
        node for node in arvore.body
        if isinstance(node, ast.FunctionDef) and node.name == "load_user"
    )
    escopo = {
        "login_manager": manager,
        "db": SimpleNamespace(session=SimpleNamespace(
            get=lambda modelo, uid: usuarios.get(uid)
        )),
        "Usuario": object,
        "current_app": current_app,
        "extrair_usuario_id": helper.extrair_usuario_id,
        "validar_id_sessao": helper.validar_id_sessao,
    }
    exec(compile(ast.Module(body=[callback], type_ignores=[]), str(MODELO), "exec"), escopo)
    return escopo["load_user"]


def test_id_hmac_revogado_por_troca_de_hash():
    helper = importar_helper()
    original = helper.gerar_id_sessao(17, "hash-da-senha-antiga", "chave-ficticia")
    novo = helper.gerar_id_sessao(17, "hash-da-senha-nova", "chave-ficticia")
    assert original != novo
    assert helper.extrair_usuario_id(original) == 17
    assert helper.validar_id_sessao(original, "hash-da-senha-antiga", "chave-ficticia")
    assert not helper.validar_id_sessao(original, "hash-da-senha-nova", "chave-ficticia")
    assert not helper.validar_id_sessao(original, "hash-da-senha-antiga", "outra-chave")
    assert "hash-da-senha" not in original


@pytest.mark.parametrize("identificador", [
    None, "", "17", "0", "v1:0:" + "a" * 64,
    "v1:17:abc", "v2:17:" + "a" * 64,
    "v1:99999999999999999999:" + "a" * 64,
    "v1:17:" + "a" * 64 + "invalido",
])
def test_sessoes_antigas_ou_adulteradas_rejeitadas(identificador):
    helper = importar_helper()
    assert helper.extrair_usuario_id(identificador) is None
    assert not helper.validar_id_sessao(identificador, "hash", "chave-ficticia")


def test_identificador_de_usuario_e_loader_compativeis():
    helper = importar_helper()
    from flask import Flask, current_app
    from flask_login import LoginManager, UserMixin, current_user, login_required, login_user
    from flask import session

    app = Flask("obpc_a7h27_isolado")
    app.secret_key = "segredo-efemero-exclusivo-teste"
    app.config.update(TESTING=True, REMEMBER_COOKIE_DURATION=__import__("datetime").timedelta(days=7))
    manager = LoginManager(app)
    manager.login_view = "entrar"

    class UsuarioFicticio(UserMixin):
        def __init__(self):
            self.id = 1
            self.senha_hash = "hash-original"
            self.ativo = True

        def get_id(self):
            return helper.gerar_id_sessao(self.id, self.senha_hash, current_app.secret_key)

        @property
        def is_active(self):
            return self.ativo

    usuario = UsuarioFicticio()
    testar_loader_real_em_isolamento(manager, {1: usuario}, helper)

    @app.get("/entrar")
    def entrar():
        lembrar = __import__("flask").request.args.get("lembrar") == "1"
        login_user(usuario, remember=lembrar)
        session.permanent = lembrar
        return "ok"

    @app.get("/restrito")
    @login_required
    def restrito():
        return "permitido:" + str(current_user.id)

    sem_remember = app.test_client()
    com_remember = app.test_client()

    resposta_sem = sem_remember.get("/entrar?lembrar=0")
    resposta_com = com_remember.get("/entrar?lembrar=1")
    assert resposta_sem.status_code == resposta_com.status_code == 200
    assert not any("remember_token=" in cookie for cookie in resposta_sem.headers.getlist("Set-Cookie"))
    assert any("remember_token=" in cookie for cookie in resposta_com.headers.getlist("Set-Cookie"))
    assert sem_remember.get("/restrito").status_code == 200
    assert com_remember.get("/restrito").status_code == 200

    # O cookie remember antigo recupera autenticacao antes da troca.
    with com_remember.session_transaction() as sessao:
        sessao.clear()
    assert com_remember.get("/restrito").status_code == 200

    # Revoga TODAS as sessoes, inclusive a que foi reconstituida por remember.
    usuario.senha_hash = "hash-trocado"
    assert sem_remember.get("/restrito").status_code == 302
    assert com_remember.get("/restrito").status_code == 302
    with com_remember.session_transaction() as sessao:
        sessao.clear()
    assert com_remember.get("/restrito").status_code == 302

    # Novo login com credencial atual volta a funcionar.
    assert sem_remember.get("/entrar?lembrar=0").status_code == 200
    assert sem_remember.get("/restrito").status_code == 200

    # Uma conta desativada perde o acesso mesmo com cookie valido.
    usuario.ativo = False
    assert sem_remember.get("/restrito").status_code == 302


def test_integracao_no_codigo_real_sem_bootstrap_de_banco():
    modelo = MODELO.read_text(encoding="utf-8-sig")
    rotas = (RAIZ / "app/usuario/usuario_routes.py").read_text(encoding="utf-8-sig")
    init = (RAIZ / "app/__init__.py").read_text(encoding="utf-8-sig")
    assert "def get_id(self):" in modelo
    assert "gerar_id_sessao(self.id, self.senha_hash, current_app.secret_key)" in modelo
    assert "db.session.get(Usuario, usuario_id)" in modelo
    assert "validar_id_sessao(user_id, usuario.senha_hash, current_app.secret_key)" in modelo
    assert "login_user(usuario, remember=lembrar)" in rotas
    assert "session.permanent = lembrar" in rotas
    assert "logout_user()" in rotas
    assert "ensure_session_permanent" not in init
