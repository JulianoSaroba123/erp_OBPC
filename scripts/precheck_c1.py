from __future__ import annotations

import subprocess
from datetime import datetime

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
MAX_COMPETENCIAS_RETROATIVAS = 24


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


def iterar_competencias_retroativas(limite: int):
    agora = datetime.now()
    mes = agora.month - 1
    ano = agora.year
    if mes == 0:
        mes = 12
        ano -= 1

    for _ in range(limite):
        yield mes, ano
        mes -= 1
        if mes == 0:
            mes = 12
            ano -= 1


def selecionar_competencia_historica_segura(limite: int = MAX_COMPETENCIAS_RETROATIVAS) -> dict[str, object]:
    percentual = percentual_conselho_sem_escrita()
    analisadas = 0

    for mes, ano in iterar_competencias_retroativas(limite):
        analisadas += 1
        calculo_legacy = _calcular_admin_sede_30_legado(mes, ano, percentual)
        valor_30 = round(float(calculo_legacy.get("valor_conselho", 0.0) or 0.0), 2)

        if valor_30 <= 0:
            continue

        admin_existente = ObrigacaoFinanceira.query.filter(
            ObrigacaoFinanceira.tipo_obrigacao == "ADMIN_SEDE_30",
            ObrigacaoFinanceira.origem_obrigacao == "automatico",
            ObrigacaoFinanceira.competencia_mes == mes,
            ObrigacaoFinanceira.competencia_ano == ano,
        ).first() is not None

        if admin_existente:
            continue

        return {
            "status": "OK",
            "analisadas": analisadas,
            "mes": mes,
            "ano": ano,
            "percentual": percentual,
            "calculo_legacy": calculo_legacy,
            "valor_30": valor_30,
            "base_calculo": round(float(calculo_legacy.get("base_calculo", 0.0) or 0.0), 2),
            "obrigacao_admin_existente": "NAO",
            "base_calculo_disponivel": "SIM",
        }

    return {
        "status": "FALHA",
        "analisadas": analisadas,
        "percentual": percentual,
    }


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

        selecao = selecionar_competencia_historica_segura()
        selecao_status = str(selecao.get("status", "FALHA"))
        competencias_analisadas = int(selecao.get("analisadas", 0) or 0)
        percentual = float(selecao.get("percentual", percentual_conselho_sem_escrita()) or 0.0)

        print(f"COMPETENCIAS_ANALISADAS: {competencias_analisadas}")
        print(f"PERCENTUAL_CONSELHO: {percentual}")

        if selecao_status == "OK":
            mes_teste = int(selecao["mes"])
            ano_teste = int(selecao["ano"])
            valor_30 = round(float(selecao["valor_30"]), 2)
            base_calculo = round(float(selecao["base_calculo"]), 2)
            base_calculo_disponivel = str(selecao["base_calculo_disponivel"])
            obrigacao_admin_existente = str(selecao["obrigacao_admin_existente"])

            print(f"COMPETENCIA_SELECIONADA: {mes_teste:02d}/{ano_teste}")
            print(f"BASE_CALCULO: {base_calculo}")
            print(f"VALOR_30_CALCULADO: {valor_30}")
            print(f"OBRIGACAO_ADMIN_EXISTENTE: {obrigacao_admin_existente}")
            print(f"BASE_CALCULO_DISPONIVEL: {base_calculo_disponivel}")
            print("SELECAO_COMPETENCIA: OK")
        else:
            print("COMPETENCIA_SELECIONADA: NENHUMA")
            print("BASE_CALCULO: 0.0")
            print("VALOR_30_CALCULADO: 0.0")
            print("OBRIGACAO_ADMIN_EXISTENTE: NAO")
            print("BASE_CALCULO_DISPONIVEL: NAO")
            print("SELECAO_COMPETENCIA: FALHA")

        if deploy["DEPLOY_VALIDADO"] != "SIM":
            resultado = "ABORTAR"
            abortar_motivo = "deploy nao validado"
        elif dialeto != "postgresql":
            resultado = "ABORTAR"
            abortar_motivo = "dialeto nao e postgresql"
        elif not tabelas_novas_ok:
            resultado = "ABORTAR"
            abortar_motivo = "tabelas necessarias ausentes"
        elif selecao_status != "OK":
            resultado = "ABORTAR"
            abortar_motivo = "nenhuma competencia historica segura com valor 30 > 0"

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