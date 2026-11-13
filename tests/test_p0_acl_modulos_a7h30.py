"""A7H.30: contratos de ACL, CSRF e escopo departamental.

Inspeciona arquivos reais sem abrir banco ou acessar a rede.
O runner HTTP P0 tambem executa testes com perfis efemeros.
"""
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULES = [
    ("app/membros/membros_routes.py", "membros_bp", "tem_acesso_membros"),
    ("app/obreiros/obreiros_routes.py", "obreiros_bp", "tem_acesso_obreiros"),
    ("app/secretaria/atas/atas_routes.py", "atas_bp", "tem_acesso_secretaria"),
    ("app/secretaria/oficios/oficios_routes.py", "oficios_bp", "tem_acesso_secretaria"),
    ("app/secretaria/inventario/inventario_routes.py", "inventario_bp", "tem_acesso_secretaria"),
    ("app/secretaria/participacao/participacao_routes.py", "participacao_bp", "tem_acesso_secretaria"),
]
FORMS = [
    "app/membros/templates/membros/lista_membros.html",
    "app/membros/templates/membros/cadastro_membro.html",
    "app/obreiros/templates/obreiros/lista_obreiros.html",
    "app/obreiros/templates/obreiros/cadastro_obreiro.html",
    "app/secretaria/atas/templates/atas/lista_atas.html",
    "app/secretaria/atas/templates/atas/cadastro_ata.html",
    "app/secretaria/oficios/templates/oficios/lista_oficios.html",
    "app/secretaria/oficios/templates/oficios/cadastro_oficio.html",
    "app/secretaria/oficios/templates/oficios/editar_oficio.html",
    "app/secretaria/inventario/templates/inventario/lista_itens.html",
    "app/secretaria/inventario/templates/inventario/cadastro_item.html",
    "app/secretaria/inventario/templates/inventario/editar_item.html",
    "app/secretaria/participacao/templates/participacao/lista_participacao.html",
    "app/secretaria/participacao/templates/participacao/cadastro_participacao.html",
    "app/departamentos/templates/departamentos/lista_departamentos.html",
    "app/departamentos/templates/departamentos/cadastro_departamento.html",
]


@pytest.mark.parametrize("path,bp,permissao", MODULES)
def test_modulos_exigem_permissao_servidor(path, bp, permissao):
    source = (ROOT / path).read_text(encoding="utf-8-sig")
    assert f"@{bp}.before_request" in source
    assert f'proteger_modulo_legado("{permissao}")' in source


@pytest.mark.parametrize("path", FORMS)
def test_formularios_post_contam_token_csrf(path):
    source = (ROOT / path).read_text(encoding="utf-8-sig")
    assert 'name="csrf_token"' in source
    assert "{{ csrf_token() }}" in source


def test_helper_acl_e_csrf_negam_antes_da_mutacao():
    source = (ROOT / "app/utils/seguranca_modulos.py").read_text(encoding="utf-8-sig")
    assert "current_user.is_authenticated" in source
    assert "abort(403)" in source
    assert "csrf.protect()" in source
    assert "callable(verificador)" in source


def test_departamento_lider_verifica_recursos_e_nao_registra_form_completo():
    source = (ROOT / "app/departamentos/departamentos_routes.py").read_text(encoding="utf-8-sig")
    assert "@departamentos_bp.before_request" in source
    assert "current_user.departamento_id" in source
    assert "objeto.departamento_id != dept_id" in source
    assert "id_form != dept_id" in source
    assert "csrf.protect()" not in source  # helper central faz CSRF
    assert "proteger_modulo_legado('tem_acesso_departamentos')" in source
    assert "dict(request.form)" not in source


def test_departamento_ajax_envia_csrf_em_todas_mutacoes():
    template = (ROOT / "app/departamentos/templates/departamentos/cadastro_departamento.html").read_text(
        encoding="utf-8-sig"
    )
    assert "csrfDeptToken" in template
    assert "formData.append('csrf_token', csrfDeptToken)" in template
    assert template.count("'X-CSRFToken': csrfDeptToken") >= 3
