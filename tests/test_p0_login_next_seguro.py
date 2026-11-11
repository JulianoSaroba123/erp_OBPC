import ast
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

RAIZ = Path(__file__).resolve().parents[1]


def validar(destino):
    arquivo = RAIZ / "app/usuario/usuario_routes.py"
    arvore = ast.parse(arquivo.read_text(encoding="utf-8-sig"))
    funcao = next(
        n for n in arvore.body
        if isinstance(n, ast.FunctionDef)
        and n.name == "_destino_login_seguro"
    )
    modulo = ast.Module(body=[funcao], type_ignores=[])
    escopo = {
        "unquote": unquote,
        "urlsplit": urlsplit,
        "unicodedata": unicodedata,
    }
    exec(compile(modulo, str(arquivo), "exec"), escopo)
    return escopo["_destino_login_seguro"](destino)


@pytest.mark.parametrize("destino", [
    "/financeiro/lista",
    "/financeiro/conciliacao?mes=11&ano=2026",
    "/usuario/painel",
])
def test_destinos_internos(destino):
    assert validar(destino) is True


@pytest.mark.parametrize("destino", [
    None, "", "financeiro/lista",
    "https://exemplo-externo.test/login",
    "http://exemplo-externo.test",
    "//exemplo-externo.test",
    "///exemplo-externo.test",
    "/\\exemplo-externo.test",
    "/%2fexemplo-externo.test",
    "/%5cexemplo-externo.test",
    "/%252fexemplo-externo.test",
    "/%255cexemplo-externo.test",
    "/\r\nLocation: https://exemplo-externo.test",
])
def test_destinos_inseguros(destino):
    assert validar(destino) is False


def test_login_preserva_next_no_formulario():
    html = (
        RAIZ / "app/usuario/templates/usuario/login.html"
    ).read_text(encoding="utf-8-sig")
    assert "url_for('usuario.login', next=request.args.get('next'))" in html


def test_decoradores_usam_caminho_interno():
    codigo = (
        RAIZ / "app/utils/auth_decorators.py"
    ).read_text(encoding="utf-8-sig")
    assert codigo.count("next=request.full_path.rstrip('?')") == 3
