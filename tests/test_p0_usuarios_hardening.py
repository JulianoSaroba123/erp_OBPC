"""A7H.28: contratos do fluxo de usuarios, sem banco ou rede externos."""
import ast
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
POLITICA = ROOT / "app/usuario/politica_senhas.py"
ROTAS = ROOT / "app/usuario/usuario_routes.py"
TPL = ROOT / "app/usuario/templates/usuario"


def _modulo_politica():
    spec = importlib.util.spec_from_file_location("a7h28_politica_isolada", POLITICA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.mark.parametrize("senha", [
    None, "", "123456", "shortpass1", " " * 20,
    "a" * 129, "A" * 18 + "\x00",
])
def test_rejeita_senhas_insuficientes(senha):
    assert _modulo_politica().validar_nova_senha(senha) is not None


@pytest.mark.parametrize("senha", [
    "Uma-frase-longa-2026", "caracteres-1234", "A" * 128,
])
def test_aceita_novas_senhas_validas(senha):
    assert _modulo_politica().validar_nova_senha(senha) is None


@pytest.mark.parametrize("pagina", [
    "login.html", "cadastro.html", "perfil.html", "novo_usuario.html",
    "editar_usuario.html", "lista_usuarios.html",
])
def test_formularios_sensiveis_contem_token_csrf(pagina):
    html = (TPL / pagina).read_text(encoding="utf-8-sig")
    assert 'name="csrf_token"' in html
    assert "{{ csrf_token() }}" in html


def test_csrf_escopado_ao_blueprint_usuario_sem_globais():
    texto = ROTAS.read_text(encoding="utf-8-sig")
    arvore = ast.parse(texto)
    decoradores = {
        nome.name for node in arvore.body if isinstance(node, ast.FunctionDef)
        for nome in node.decorator_list if isinstance(nome, ast.Attribute)
    }
    assert "before_request" in decoradores
    assert "csrf.protect()" in texto
    for endpoint in (
        "usuario.login", "usuario.cadastro", "usuario.perfil",
        "usuario.novo_usuario", "usuario.editar_usuario",
        "usuario.toggle_status_usuario", "usuario.excluir_usuario",
    ):
        assert repr(endpoint) in texto or f'"{endpoint}"' in texto
    assert "WTF_CSRF_CHECK_DEFAULT" not in texto


def test_gates_sensiveis_no_servidor():
    codigo = ROTAS.read_text(encoding="utf-8-sig")
    assert "current_user.check_senha(" in codigo
    assert 'request.form.get("confirmar_senha_admin")' in codigo
    assert "Usuario.query.filter_by(nivel_acesso='master', ativo=True).count()" in codigo
    assert "validar_nova_senha(senha)" in codigo
    assert "validar_nova_senha(nova_senha)" in codigo
    assert "nivel_acesso=NivelAcesso.MEMBRO.value" in codigo
    assert "AUDIT_USUARIOS" in codigo


def test_antigas_senhas_nao_sao_invalidadas_no_login():
    codigo = ROTAS.read_text(encoding="utf-8-sig")
    inicio = codigo.index("def login():")
    final = codigo.index("# ---------- ROTA DE LOGOUT", inicio)
    assert "validar_nova_senha(" not in codigo[inicio:final]
    assert "usuario.check_senha(senha)" in codigo[inicio:final]
