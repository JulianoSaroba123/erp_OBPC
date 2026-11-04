# -*- coding: utf-8 -*-
"""Regressao HTTP real, em subprocesso isolado.

O processo pytest nunca importa app nem cria conexao ao banco.
O runner filho define DATABASE_URL e SECRET_KEY ficticios antes de
importar a aplicacao, desativa scheduler e bloqueia conexoes externas.
"""
import os
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "tests" / "_p0_http_integrado_runner.py"


def test_p0_http_autenticado_regressao_integrada():
    assert RUNNER.is_file(), "Runner de seguranca ausente"
    ambiente = os.environ.copy()
    for chave in (
        "DATABASE_URL", "SQLALCHEMY_DATABASE_URI", "SECRET_KEY", "FLASK_APP",
        "FLASK_ENV", "RENDER", "PYTHONPATH",
    ):
        ambiente.pop(chave, None)
    ambiente["PYTHONPATH"] = str(REPO)
    ambiente["PYTHONDONTWRITEBYTECODE"] = "1"
    ambiente["FLASK_ENV"] = "testing"
    ambiente["RENDER"] = "false"

    resultado = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(RUNNER)],
        cwd=str(REPO),
        env=ambiente,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=180,
    )
    assert resultado.returncode == 0, (
        "Regressao HTTP integrada falhou:\n" + resultado.stdout[-20000:]
    )
    assert "P0.6D-B: LOGIN REAL E HOMOLOGACAO HTTP APROVADOS." in resultado.stdout
    assert "OK: pasta temporaria excluida." in resultado.stdout
