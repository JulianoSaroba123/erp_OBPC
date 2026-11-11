"""CI-only smoke: Gunicorn real com banco SQLite efemero e sem rede externa."""

import os
import subprocess
import sys
import time
from pathlib import Path

import requests


def main():
    if os.environ.get("GITHUB_ACTIONS", "").lower() != "true":
        raise RuntimeError("Executar exclusivamente no runner isolado do GitHub Actions.")
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url.startswith("sqlite:////tmp/erp_obpc_p0_ci.sqlite"):
        raise RuntimeError("DATABASE_URL deve apontar para o SQLite descartavel do CI.")
    if os.environ.get("RENDER") != "false":
        raise RuntimeError("RENDER precisa ser false no CI.")
    if not os.environ.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY de teste ausente.")

    cwd = Path(__file__).resolve().parents[1]
    url = "http://127.0.0.1:18763"
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "gunicorn", "run:app",
            "--workers", "1", "--bind", "127.0.0.1:18763",
            "--timeout", "30", "--access-logfile", "-"
        ],
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    session = requests.Session()
    session.trust_env = False
    passed = False
    try:
        for _ in range(40):
            if proc.poll() is not None:
                raise RuntimeError("Gunicorn encerrou antes de responder.")
            try:
                login = session.get(url + "/login", timeout=2, allow_redirects=False)
                if login.status_code != 200:
                    raise AssertionError(f"Login inesperado HTTP {login.status_code}")
                report = session.get(
                    url + "/financeiro/relatorio?tipo_relatorio=livro_caixa",
                    timeout=2, allow_redirects=False
                )
                if report.status_code not in (302, 401, 403):
                    raise AssertionError(f"Relatorio anonimo liberado HTTP {report.status_code}")
                pdf = session.get(
                    url + "/financeiro/relatorio-caixa/pdf?mes=7&ano=2026&formato=livro_caixa",
                    timeout=2, allow_redirects=False
                )
                if pdf.status_code not in (302, 401, 403):
                    raise AssertionError(f"PDF anonimo liberado HTTP {pdf.status_code}")
                print("Gunicorn: login HTTP 200; relatorio e PDF anonimos bloqueados.")
                passed = True
                break
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                time.sleep(0.5)
        if not passed:
            raise RuntimeError("Gunicorn nao respondeu em 20s.")
    finally:
        session.close()
        if proc.poll() is None:
            proc.terminate()
        try:
            logs = proc.communicate(timeout=8)[0] or ""
        except subprocess.TimeoutExpired:
            proc.kill()
            logs = proc.communicate(timeout=5)[0] or ""
        if "This is a development server" in logs:
            raise AssertionError("Servidor de desenvolvimento detectado no startup WSGI.")
        if not passed:
            print("Trecho final dos logs do Gunicorn:", logs[-3500:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
