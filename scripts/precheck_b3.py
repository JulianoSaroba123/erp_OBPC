from __future__ import annotations

import subprocess
import sys

from flask import Flask
from sqlalchemy import case, func, inspect

from app.config import Config
from app.extensoes import db
from app.financeiro.despesas_fixas_model import DespesaFixaConselho
from app.financeiro.envios_sede_model import EnvioSede
from app.financeiro.financeiro_model import Lancamento
from app.financeiro.financeiro_routes import _criar_obrigacao_despesa_fixa_sem_commit
from app.financeiro.obrigacoes_model import (
    ObrigacaoEvento,
    ObrigacaoFinanceira,
    PagamentoObrigacao,
    PagamentoObrigacaoItem,
)


DIAG_COMMITS = ["05d0137", "a241a7f", "6278e57"]
ARQUIVOS_OBRIGATORIOS = [
    "app/financeiro/financeiro_routes.py",
    "scripts/precheck_b3.py",
    "scripts/smoke_b3.py",
]
MES_TESTE = 12
ANO_TESTE = 2099


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


def commit_ancestral(target_commit: str) -> str:
    try:
        rc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", target_commit, "HEAD"],
            capture_output=True,
        ).returncode
        if rc == 0:
            return "SIM"
        if rc == 1:
            return "NAO"
        return "INDISPONIVEL"
    except Exception:
        return "INDISPONIVEL"


def arquivo_tracked_no_head(caminho: str) -> str:
    try:
        rc = subprocess.run(
            ["git", "ls-files", "--error-unmatch", caminho],
            capture_output=True,
        ).returncode
        return "SIM" if rc == 0 else "NAO"
    except Exception:
        return "NAO"


def avaliar_validacao_deploy(
    head: str,
    origin_main: str,
    arquivos_deploy_ok: str,
    helper_existe: str,
) -> dict[str, str]:
    head_igual_origin_main = "SIM" if (head != "INDEFINIDO" and origin_main != "INDEFINIDO" and head == origin_main) else "NAO"
    deploy_validado = "SIM" if (head_igual_origin_main == "SIM" and arquivos_deploy_ok == "SIM" and helper_existe == "SIM") else "NAO"
    return {
        "HEAD_IGUAL_ORIGIN_MAIN": head_igual_origin_main,
        "DEPLOY_VALIDADO": deploy_validado,
    }


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


def contar_envios_sede() -> int:
    return int(db.session.query(EnvioSede).count())


def main() -> int:
    print("=== PRE-CHECK B.3 ===")

    resultado = "OK"
    abortar_motivo = None

    app = novo_app()
    with app.app_context():
        head = obter_head()
        origin_main = obter_origin_main()
        shallow = repositorio_shallow()

        arquivos_tracked = {caminho: arquivo_tracked_no_head(caminho) for caminho in ARQUIVOS_OBRIGATORIOS}
        arquivos_deploy_ok = "SIM" if all(status == "SIM" for status in arquivos_tracked.values()) else "NAO"

        helper_existe = "SIM" if callable(_criar_obrigacao_despesa_fixa_sem_commit) else "NAO"
        deploy = avaliar_validacao_deploy(head, origin_main, arquivos_deploy_ok, helper_existe)

        print(f"HEAD: {head}")
        print(f"ORIGIN_MAIN: {origin_main}")
        print(f"HEAD_IGUAL_ORIGIN_MAIN: {deploy['HEAD_IGUAL_ORIGIN_MAIN']}")
        print(f"REPOSITORIO_SHALLOW: {shallow}")
        for caminho, status in arquivos_tracked.items():
            print(f"{caminho} TRACKED: {status}")
        print(f"ARQUIVOS_DEPLOY_OK: {arquivos_deploy_ok}")
        print(f"HELPER_EXISTE: {helper_existe}")

        if shallow == "NAO":
            for commit in DIAG_COMMITS:
                print(f"DIAG_COMMIT_{commit}_ANCESTRAL: {commit_ancestral(commit)}")

        print(f"DEPLOY_VALIDADO: {deploy['DEPLOY_VALIDADO']}")

        dialeto = (db.engine.dialect.name or "").lower()
        print(f"DIALETO: {dialeto}")

        insp = inspect(db.engine)
        tabelas = set(insp.get_table_names())
        tabelas_novas_ok = {
            "obrigacoes_financeiras",
            "pagamentos_obrigacao",
            "pagamentos_obrigacao_itens",
            "obrigacao_eventos",
            "lancamentos",
            "envios_sede",
            "despesas_fixas_conselho",
        }.issubset(tabelas)
        print(f"TABELAS_NOVAS_OK: {'SIM' if tabelas_novas_ok else 'NAO'}")

        obrigacoes = ObrigacaoFinanceira.query.count()
        eventos = ObrigacaoEvento.query.count()
        pagamentos = PagamentoObrigacao.query.count()
        itens = PagamentoObrigacaoItem.query.count()
        lancamentos = Lancamento.query.count()
        envios = contar_envios_sede()
        saldo = saldo_atual()

        print(f"OBRIGACOES: {obrigacoes}")
        print(f"EVENTOS: {eventos}")
        print(f"PAGAMENTOS: {pagamentos}")
        print(f"ITENS: {itens}")
        print(f"LANCAMENTOS: {lancamentos}")
        print(f"ENVIOS: {envios}")
        print(f"SALDO: {saldo}")

        despesas = DespesaFixaConselho.query.filter_by(ativo=True).order_by(DespesaFixaConselho.id.asc()).all()
        candidata = despesas[0] if despesas else None

        if candidata is None:
            print("DESPESA_CANDIDATA_ID: NONE")
            print("DESPESA_CANDIDATA_NOME: NONE")
            print("DESPESA_CANDIDATA_VALOR: NONE")
            print("DESPESA_CANDIDATA_CATEGORIA: NONE")
            print(f"COMPETENCIA: {MES_TESTE:02d}/{ANO_TESTE}")
            print("COMPETENCIA_LIVRE: NAO")
            resultado = "ABORTAR"
            abortar_motivo = "nenhuma despesa fixa ativa"
        else:
            print(f"DESPESA_CANDIDATA_ID: {candidata.id}")
            print(f"DESPESA_CANDIDATA_NOME: {candidata.nome}")
            print(f"DESPESA_CANDIDATA_VALOR: {float(candidata.valor_padrao or 0):.2f}")
            print(f"DESPESA_CANDIDATA_CATEGORIA: {(candidata.categoria or '').strip()}")
            print(f"COMPETENCIA: {MES_TESTE:02d}/{ANO_TESTE}")

            livre = not ObrigacaoFinanceira.query.filter(
                ObrigacaoFinanceira.tipo_obrigacao == "DESPESA_FIXA",
                ObrigacaoFinanceira.origem_obrigacao == "automatico",
                ObrigacaoFinanceira.referencia_origem_tipo == "DESPESA_FIXA_CONSELHO",
                ObrigacaoFinanceira.referencia_origem_id == candidata.id,
                ObrigacaoFinanceira.competencia_mes == MES_TESTE,
                ObrigacaoFinanceira.competencia_ano == ANO_TESTE,
            ).first()
            print(f"COMPETENCIA_LIVRE: {'SIM' if livre else 'NAO'}")
            if not livre:
                resultado = "ABORTAR"
                abortar_motivo = "competencia 12/2099 ocupada para a despesa candidata"

        if deploy["DEPLOY_VALIDADO"] != "SIM":
            resultado = "ABORTAR"
            abortar_motivo = (
                f"deploy invalido: head={head}, origin_main={origin_main}, "
                f"head_igual_origin_main={deploy['HEAD_IGUAL_ORIGIN_MAIN']}, "
                f"arquivos_deploy_ok={arquivos_deploy_ok}, helper_existe={helper_existe}"
            )
        elif helper_existe != "SIM":
            resultado = "ABORTAR"
            abortar_motivo = "helper ausente"
        elif dialeto != "postgresql":
            resultado = "ABORTAR"
            abortar_motivo = "dialeto nao e postgresql"
        elif not tabelas_novas_ok:
            resultado = "ABORTAR"
            abortar_motivo = "tabelas novas ausentes"

        print(f"RESULTADO_PRE_CHECK: {resultado}")
        if resultado == "ABORTAR" and abortar_motivo:
            print(f"ABORTAR_MOTIVO: {abortar_motivo}")

        db.session.rollback()

    print("=== FIM PRE-CHECK B.3 ===")
    return 0 if resultado == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())