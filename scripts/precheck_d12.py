from __future__ import annotations

import inspect as py_inspect
import subprocess

from flask import Flask
from sqlalchemy import case, func, inspect

from app.config import Config
from app.extensoes import db
from app.financeiro.envios_sede_model import EnvioSede
from app.financeiro.financeiro_model import Lancamento
from app.financeiro.financeiro_routes import _registrar_pagamento_obrigacao_sem_commit
from app.financeiro.obrigacoes_model import (
    ObrigacaoEvento,
    ObrigacaoFinanceira,
    PagamentoObrigacao,
    PagamentoObrigacaoItem,
)


ARQUIVOS_OBRIGATORIOS = [
    "app/financeiro/financeiro_routes.py",
    "scripts/precheck_d12.py",
    "scripts/smoke_d12.py",
]


def novo_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app


def obter_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "INDEFINIDO"


def obter_origin_main() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "origin/main"], text=True).strip()
    except Exception:
        return "INDEFINIDO"


def repositorio_shallow() -> str:
    try:
        shallow_raw = subprocess.check_output(["git", "rev-parse", "--is-shallow-repository"], text=True).strip().lower()
        return "SIM" if shallow_raw == "true" else "NAO"
    except Exception:
        return "NAO"


def arquivo_tracked_no_head(caminho: str) -> str:
    try:
        rc = subprocess.run(["git", "ls-files", "--error-unmatch", caminho], capture_output=True).returncode
        return "SIM" if rc == 0 else "NAO"
    except Exception:
        return "NAO"


def saldo_atual() -> float:
    entradas = db.session.query(
        func.coalesce(
            func.sum(
                case(
                    (func.lower(Lancamento.tipo) == "entrada", Lancamento.valor),
                    else_=0.0,
                )
            ),
            0.0,
        )
    ).scalar()
    saidas = db.session.query(
        func.coalesce(
            func.sum(
                case(
                    (func.lower(Lancamento.tipo).in_(["saída", "saida"]), Lancamento.valor),
                    else_=0.0,
                )
            ),
            0.0,
        )
    ).scalar()
    return round(float(entradas or 0.0) - float(saidas or 0.0), 2)


def helper_callable() -> str:
    return "SIM" if callable(_registrar_pagamento_obrigacao_sem_commit) else "NAO"


def helper_usa_lock_pessimista() -> str:
    try:
        source = py_inspect.getsource(_registrar_pagamento_obrigacao_sem_commit)
    except Exception:
        return "NAO"
    return "SIM" if "with_for_update" in source and "_carregar_obrigacao_para_pagamento" in source else "NAO"


def avaliar_gate_postgresql(dialeto: str) -> tuple[bool, str | None]:
    if (dialeto or "").strip().lower() == "postgresql":
        return True, None
    return False, "dialeto nao e postgresql"


def obrigacao_teste_disponivel() -> str:
    return "SIM" if ObrigacaoFinanceira.query.filter(
        ObrigacaoFinanceira.status.in_(["PENDENTE", "PARCIAL"]),
        ObrigacaoFinanceira.tipo_obrigacao.in_(["DESPESA_FIXA", "ADMIN_SEDE_30"]),
    ).first() is not None else "NAO"


def main() -> int:
    print("=== PRE-CHECK D.1.2 ===")

    resultado = "OK"
    abortar_motivo = None

    app = novo_app()
    with app.app_context():
        head = obter_head()
        origin_main = obter_origin_main()
        shallow = repositorio_shallow()
        arquivos_tracked = {caminho: arquivo_tracked_no_head(caminho) for caminho in ARQUIVOS_OBRIGATORIOS}
        arquivos_deploy_ok = "SIM" if all(status == "SIM" for status in arquivos_tracked.values()) else "NAO"
        helper_ok = helper_callable()
        deploy_validado = "SIM" if (head != "INDEFINIDO" and origin_main != "INDEFINIDO" and head == origin_main and arquivos_deploy_ok == "SIM" and helper_ok == "SIM") else "NAO"
        dialeto = (db.engine.dialect.name or "").lower()

        print(f"HEAD: {head}")
        print(f"ORIGIN_MAIN: {origin_main}")
        print(f"HEAD_IGUAL_ORIGIN_MAIN: {'SIM' if head != 'INDEFINIDO' and origin_main != 'INDEFINIDO' and head == origin_main else 'NAO'}")
        print(f"REPOSITORIO_SHALLOW: {shallow}")
        print(f"ARQUIVOS_DEPLOY_OK: {arquivos_deploy_ok}")
        print(f"HELPER_EXISTE: {helper_ok}")
        print(f"DEPLOY_VALIDADO: {deploy_validado}")
        print(f"DIALETO: {dialeto}")

        gate_ok, gate_motivo = avaliar_gate_postgresql(dialeto)
        if not gate_ok:
            resultado = "ABORTAR"
            abortar_motivo = gate_motivo

        insp = inspect(db.engine)
        tabelas = set(insp.get_table_names())
        tabelas_ok = {
            "obrigacoes_financeiras",
            "pagamentos_obrigacao",
            "pagamentos_obrigacao_itens",
            "obrigacao_eventos",
            "lancamentos",
            "envios_sede",
        }.issubset(tabelas)
        lock_ativo = helper_usa_lock_pessimista() if resultado != "ABORTAR" else "NAO"

        obrigacoes = ObrigacaoFinanceira.query.count()
        pagamentos = PagamentoObrigacao.query.count()
        itens = PagamentoObrigacaoItem.query.count()
        eventos = ObrigacaoEvento.query.count()
        lancamentos = Lancamento.query.count()
        envios = EnvioSede.query.count()
        saldo = saldo_atual()

        print(f"TABELAS_OK: {'SIM' if tabelas_ok else 'NAO'}")
        print(f"OBRIGACOES: {obrigacoes}")
        print(f"PAGAMENTOS: {pagamentos}")
        print(f"ITENS: {itens}")
        print(f"EVENTOS: {eventos}")
        print(f"LANCAMENTOS: {lancamentos}")
        print(f"ENVIOS: {envios}")
        print(f"SALDO: {saldo}")
        print(f"LOCK_PESSIMISTA_ATIVO: {lock_ativo}")
        obrigacao_disponivel = obrigacao_teste_disponivel() if resultado != "ABORTAR" else "NAO"
        estrategia_obrigacao_teste = "EXISTENTE" if obrigacao_disponivel == "SIM" else "TEMPORARIA"
        print(f"OBRIGACAO_TESTE_DISPONIVEL: {obrigacao_disponivel}")
        print(f"ESTRATEGIA_OBRIGACAO_TESTE: {estrategia_obrigacao_teste}")

        if resultado == "ABORTAR":
            print(f"RESULTADO_PRE_CHECK: {resultado}")
            print(f"ABORTAR_MOTIVO: {abortar_motivo or 'NENHUM'}")
            print("=== FIM PRE-CHECK D.1.2 ===")
            return 1

        if head == "INDEFINIDO" or origin_main == "INDEFINIDO" or shallow == "NAO" or arquivos_deploy_ok != "SIM" or helper_ok != "SIM" or not tabelas_ok:
            resultado = "ABORTAR"
            if head == "INDEFINIDO" or origin_main == "INDEFINIDO":
                abortar_motivo = "repositorio sem refs git validas"
            elif arquivos_deploy_ok != "SIM":
                abortar_motivo = "arquivos obrigatorios nao tracked"
            elif helper_ok != "SIM":
                abortar_motivo = "helper nao callable"
            elif not tabelas_ok:
                abortar_motivo = "tabelas obrigatorias ausentes"
            elif shallow != "SIM":
                abortar_motivo = "repositorio nao shallow"

        print(f"RESULTADO_PRE_CHECK: {resultado}")
        print(f"ABORTAR_MOTIVO: {abortar_motivo or 'NENHUM'}")

    print("=== FIM PRE-CHECK D.1.2 ===")
    return 0 if resultado == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())