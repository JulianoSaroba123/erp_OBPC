"""Regressoes isoladas: importar run.py nunca inicia Flask nem cria admin."""

import runpy
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "run.py"


def _fake_flask(monkeypatch):
    calls = []
    app = SimpleNamespace(run=lambda **kwargs: calls.append(kwargs))
    monkeypatch.setitem(sys.modules, "app", SimpleNamespace(create_app=lambda: app))
    return app, calls


def test_importacao_wsgi_nao_inicia_servidor(monkeypatch):
    fake_app, calls = _fake_flask(monkeypatch)
    exported = runpy.run_path(str(RUN), run_name="gunicorn_import")
    assert exported["app"] is fake_app
    assert calls == []


def test_execucao_local_usa_loopback_sem_debug(monkeypatch):
    fake_app, calls = _fake_flask(monkeypatch)
    monkeypatch.setenv("PORT", "5017")
    exported = runpy.run_path(str(RUN), run_name="__main__")
    assert exported["app"] is fake_app
    assert calls == [{"host": "127.0.0.1", "port": 5017, "debug": False}]


def test_run_nao_provisiona_banco_nem_senha_administrativa():
    code = RUN.read_text(encoding="utf-8-sig")
    for unsafe in ("db.create_all(", "Usuario(", ".set_senha(", "db.session.commit(", "admin123", "app.app_context("):
        assert unsafe not in code
