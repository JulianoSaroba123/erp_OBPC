from __future__ import annotations

import subprocess

from flask import Flask
from sqlalchemy import case, func, inspect

from app.config import Config
from app.configuracoes.configuracoes_model import Configuracao
from app.extensoes import db
from app.financeiro.envios_sede_model import EnvioSede
from app.financeiro.financeiro_model import Lancamento
from app.financeiro.financeiro_routes import (
    _calcular_admin_sede_30_legado,
    _criar_obrigacao_admin_sede_sem_commit,
)
from app.financeiro.obrigacoes_model import (
    ObrigacaoEvento,
    ObrigacaoFinanceira,
    PagamentoObrigacao,
    PagamentoObrigacaoItem,
)


ARQUIVOS_OBRIGATORIOS = [
    "app/financeiro/financeiro_routes.py",
    "scripts/precheck_c1.py",
    "scripts/smoke_c1.py",
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


def arquivo_tracked_no_head(caminho: str) -> str:
    try:
        rc = subprocess.run(["git", "ls-files", "--error-unmatch", caminho], capture_output=True).returncode
        return "SIM" if rc == 0 else "NAO"
    except Exception:
        return "NAO"


def avaliar_validacao_deploy(head: str, origin_main: str, arquivos_deploy_ok: str, helper_existe: str) -> dict[str, str]:
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


def percentual_conselho_sem_escrita() -> float:
    cfg = Configuracao.query.filter_by(id=1).first()
    if cfg and getattr(cfg, "percentual_conselho", None):
        return float(cfg.percentual_conselho)
    return 30.0


def main() -> int:
    print("=== PRE-CHECK C.1 ===")

    resultado = "OK"
    abortar_motivo = None

    app = novo_app()
    with app.app_context():
        head = obter_head()
        origin_main = obter_origin_main()
        shallow = repositorio_shallow()

        arquivos_tracked = {caminho: arquivo_tracked_no_head(caminho) for caminho in ARQUIVOS_OBRIGATORIOS}
        arquivos_deploy_ok = "SIM" if all(status == "SIM" for status in arquivos_tracked.values()) else "NAO"
        helper_existe = "SIM" if callable(_criar_obrigacao_admin_sede_sem_commit) else "NAO"

        deploy = avaliar_validacao_deploy(head, origin_main, arquivos_deploy_ok, helper_existe)

        print(f"HEAD: {head}")
        print(f"ORIGIN_MAIN: {origin_main}")
        print(f"HEAD_IGUAL_ORIGIN_MAIN: {deploy['HEAD_IGUAL_ORIGIN_MAIN']}")
        print(f"REPOSITORIO_SHALLOW: {shallow}")
        print(f"ARQUIVOS_DEPLOY_OK: {arquivos_deploy_ok}")
        print(f"HELPER_EXISTE: {helper_existe}")
        print(f"DEPLOY_VALIDADO: {deploy['DEPLOY_VALIDADO']}")

        dialeto = (db.engine.dialect.name or "").lower()
        print(f"DIALETO: {dialeto}")

        insp = inspect(db.engine)
        required = {
            "obrigacoes_financeiras",
            "obrigacao_eventos",
            "pagamentos_obrigacao",
            "pagamentos_obrigacao_itens",
            "lancamentos",
            "envios_sede",
        }
        tabelas_novas_ok = required.issubset(set(insp.get_table_names()))
        print(f"TABELAS_NOVAS_OK: {'SIM' if tabelas_novas_ok else 'NAO'}")

        obrigacoes = ObrigacaoFinanceira.query.count()
        eventos = ObrigacaoEvento.query.count()
        pagamentos = PagamentoObrigacao.query.count()
        itens = PagamentoObrigacaoItem.query.count()
        lancamentos = Lancamento.query.count()
        envios = int(db.session.query(EnvioSede).count())
        saldo = saldo_atual()

        print(f"OBRIGACOES: {obrigacoes}")
        print(f"EVENTOS: {eventos}")
        print(f"PAGAMENTOS: {pagamentos}")
        print(f"ITENS: {itens}")
        print(f"LANCAMENTOS: {lancamentos}")
        print(f"ENVIOS: {envios}")
        print(f"SALDO: {saldo}")

        percentual = percentual_conselho_sem_escrita()
        calculo = _calcular_admin_sede_30_legado(MES_TESTE, ANO_TESTE, percentual)
        valor_30 = float(calculo.get("valor_conselho", 0.0) or 0.0)
        base_calculo_disponivel = "SIM" if valor_30 > 0 else "NAO"

        admin_existente = ObrigacaoFinanceira.query.filter(
            ObrigacaoFinanceira.tipo_obrigacao == "ADMIN_SEDE_30",
            ObrigacaoFinanceira.origem_obrigacao == "automatico",
            ObrigacaoFinanceira.competencia_mes == MES_TESTE,
            ObrigacaoFinanceira.competencia_ano == ANO_TESTE,
        ).first() is not None

        print(f"COMPETENCIA: {MES_TESTE:02d}/{ANO_TESTE}")
        print(f"OBRIGACAO_ADMIN_EXISTENTE: {'SIM' if admin_existente else 'NAO'}")
        print(f"VALOR_30_CALCULADO: {round(valor_30, 2)}")
        print(f"BASE_CALCULO_DISPONIVEL: {base_calculo_disponivel}")

        if deploy["DEPLOY_VALIDADO"] != "SIM":
            resultado = "ABORTAR"
            abortar_motivo = "deploy nao validado"
        elif dialeto != "postgresql":
            resultado = "ABORTAR"
            abortar_motivo = "dialeto nao e postgresql"
        elif not tabelas_novas_ok:
            resultado = "ABORTAR"
            abortar_motivo = "tabelas necessarias ausentes"
        elif admin_existente:
            resultado = "ABORTAR"
            abortar_motivo = "obrigacao ADMIN_SEDE_30 ja existe para 12/2099"
        elif base_calculo_disponivel != "SIM":
            resultado = "ABORTAR"
            abortar_motivo = "valor 30 calculado igual a zero para competencia de teste"

        print("RESULTADO_PRE_CHECK:")
        print(resultado)
        if resultado == "ABORTAR" and abortar_motivo:
            print("ABORTAR_MOTIVO:")
            print(abortar_motivo)

        db.session.rollback()
        db.session.remove()

    print("=== FIM PRE-CHECK C.1 ===")
    return 0 if resultado == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())