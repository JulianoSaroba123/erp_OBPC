"""P0: o startup nao deve publicar listagens de usuarios nos logs."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_startup_nao_expoe_listagem_de_usuarios():
    source = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8-sig")
    assert "DEBUG: USUARIOS E PERMISSOES NO BANCO:" not in source
    assert "Usuario.query.all()" not in source


def test_run_sem_provisionamento_de_master():
    source = (ROOT / "run.py").read_text(encoding="utf-8-sig")
    assert "admin123" not in source
    assert ".set_senha(" not in source
    assert "db.create_all(" not in source
