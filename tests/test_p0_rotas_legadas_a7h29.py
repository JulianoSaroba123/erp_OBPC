"""A7H.29: contrato de seguranca das rotas legadas (sem banco externo)."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USER = ROOT / "app/usuario/usuario_routes.py"
EVENTS = ROOT / "app/eventos/eventos_routes.py"
NOTIFICATIONS = ROOT / "app/notificacoes/notificacoes_routes.py"


def _routes(source):
    tree = ast.parse(source)
    routes = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            for deco in node.decorator_list:
                if not isinstance(deco, ast.Call):
                    continue
                if not isinstance(deco.func, ast.Attribute) or deco.func.attr != "route":
                    continue
                path = deco.args[0].value if deco.args and isinstance(deco.args[0], ast.Constant) else None
                methods = None
                for kw in deco.keywords:
                    if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                        methods = [elt.value for elt in kw.value.elts]
                routes[path] = (node.name, methods)
    return routes


def test_mutacoes_get_antigas_fechadas():
    eventos = _routes(EVENTS.read_text(encoding="utf-8-sig"))
    usuario = _routes(USER.read_text(encoding="utf-8-sig"))
    assert eventos["/excluir/<int:evento_id>"] == ("excluir_evento", ["POST"])
    assert usuario["/admin/atualizar-atividades-painel"] == (
        "atualizar_atividades_painel", ["POST"],
    )
    source = USER.read_text(encoding="utf-8-sig")
    assert "usuario.atualizar_atividades_painel" in source
    assert "@requer_nivel_acesso('master', 'administrador')" in source


def test_notificacoes_verificam_perfil_e_csrf():
    code = NOTIFICATIONS.read_text(encoding="utf-8-sig")
    assert "@notificacoes_bp.before_request" in code
    assert "csrf.protect()" in code
    assert "current_user.tem_acesso_configuracoes()" in code
    assert "abort(403)" in code
    template = (
        ROOT / "app/notificacoes/templates/notificacoes/configurar_notificacoes.html"
    ).read_text(encoding="utf-8-sig")
    assert 'name="csrf_token"' in template
    assert template.count("'X-CSRFToken':") == 2


def test_eventos_somente_gestores_podem_mutar():
    code = EVENTS.read_text(encoding="utf-8-sig")
    assert "@eventos_bp.before_request" in code
    assert "current_user.pode_gerenciar_eventos()" in code
    assert "csrf.protect()" in code
    for page in (
        "lista_eventos.html", "detalhes_evento.html",
        "calendario_eventos.html", "cadastro_evento.html",
    ):
        template = (
            ROOT / "app/eventos/templates/eventos" / page
        ).read_text(encoding="utf-8-sig")
        assert 'name="csrf_token"' in template
    lista = (
        ROOT / "app/eventos/templates/eventos/lista_eventos.html"
    ).read_text(encoding="utf-8-sig")
    assert '<form method="POST" action="{{ url_for(\'eventos.excluir_evento\'' in lista
    calendario = (
        ROOT / "app/eventos/templates/eventos/calendario_eventos.html"
    ).read_text(encoding="utf-8-sig")
    assert 'id="formExcluirEvento" method="POST"' in calendario


def test_debug_usuario_nao_exibe_informacoes_operacionais():
    code = USER.read_text(encoding="utf-8-sig")
    inicio = code.index("def debug_info():")
    fim = code.index("@usuario_bp.route(\"/usuarios/novo\"", inicio)
    funcao = code[inicio:fim]
    assert 'if not current_app.config.get("TESTING")' in funcao
    assert "abort(404)" in funcao
    for proibido in ("traceback", "user_email", "usuario.email", "Usuario.query"):
        assert proibido not in funcao
