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
from scripts.precheck_c1 import selecionar_competencia_historica_segura


ARQUIVOS_OBRIGATORIOS = [
    "app/financeiro/financeiro_routes.py",
    "scripts/precheck_c1.py",
    "scripts/smoke_c1.py",
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


def counts() -> dict[str, int]:
    return {
        "obrigacoes": ObrigacaoFinanceira.query.count(),
        "eventos": ObrigacaoEvento.query.count(),
        "pagamentos": PagamentoObrigacao.query.count(),
        "itens": PagamentoObrigacaoItem.query.count(),
        "lancamentos": Lancamento.query.count(),
        "envios": int(db.session.query(EnvioSede).count()),
    }


def admin_obrigacoes_query(mes: int, ano: int):
    return ObrigacaoFinanceira.query.filter(
        ObrigacaoFinanceira.tipo_obrigacao == "ADMIN_SEDE_30",
        ObrigacaoFinanceira.origem_obrigacao == "automatico",
        ObrigacaoFinanceira.referencia_origem_tipo == "FECHAMENTO_MENSAL",
        ObrigacaoFinanceira.competencia_mes == mes,
        ObrigacaoFinanceira.competencia_ano == ano,
    )


def admin_eventos_query(mes: int, ano: int):
    return ObrigacaoEvento.query.join(
        ObrigacaoFinanceira,
        ObrigacaoEvento.obrigacao_financeira_id == ObrigacaoFinanceira.id,
    ).filter(
        ObrigacaoFinanceira.tipo_obrigacao == "ADMIN_SEDE_30",
        ObrigacaoFinanceira.origem_obrigacao == "automatico",
        ObrigacaoFinanceira.referencia_origem_tipo == "FECHAMENTO_MENSAL",
        ObrigacaoFinanceira.competencia_mes == mes,
        ObrigacaoFinanceira.competencia_ano == ano,
        ObrigacaoEvento.evento_tipo == "CRIACAO",
    )


def main() -> int:
    print("=== SMOKE C.1 PRODUCAO ===")

    erro_smoke = None
    resultado_smoke = "FALHA"
    rollback_executado = "NAO"
    primeira_chamada = "ERRO"
    segunda_chamada = "ERRO"
    obrigacao_criada = "NAO"
    evento_criado = "NAO"
    lancamento_criado = "NAO"
    pagamento_criado = "NAO"
    item_criado = "NAO"
    envio_sede_criado = "NAO"
    idempotencia = "FALHA"
    saldo_durante = None
    validacao_obrigacao_ok = "NAO"

    app = novo_app()

    with app.app_context():
        head = obter_head()
        origin_main = obter_origin_main()
        shallow = repositorio_shallow()

        arquivos_tracked = {caminho: arquivo_tracked_no_head(caminho) for caminho in ARQUIVOS_OBRIGATORIOS}
        arquivos_deploy_ok = "SIM" if all(status == "SIM" for status in arquivos_tracked.values()) else "NAO"
        helper_ok = "SIM" if callable(_criar_obrigacao_admin_sede_sem_commit) else "NAO"
        deploy = avaliar_validacao_deploy(head, origin_main, arquivos_deploy_ok, helper_ok)

        print(f"HEAD: {head}")
        print(f"ORIGIN_MAIN: {origin_main}")
        print(f"HEAD_IGUAL_ORIGIN_MAIN: {deploy['HEAD_IGUAL_ORIGIN_MAIN']}")
        print(f"REPOSITORIO_SHALLOW: {shallow}")
        print(f"ARQUIVOS_DEPLOY_OK: {arquivos_deploy_ok}")
        print(f"HELPER_OK: {helper_ok}")
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
        tabelas_ok = required.issubset(set(insp.get_table_names()))

        selecao = selecionar_competencia_historica_segura()
        selecao_status = str(selecao.get("status", "FALHA"))
        competencias_analisadas = int(selecao.get("analisadas", 0) or 0)
        percentual = float(selecao.get("percentual", percentual_conselho_sem_escrita()) or 0.0)

        print(f"COMPETENCIAS_ANALISADAS: {competencias_analisadas}")
        print(f"PERCENTUAL_CONSELHO: {percentual}")

        if selecao_status != "OK":
            print("SELECAO_COMPETENCIA: FALHA")
            print("RESULTADO_SMOKE: FALHA")
            print("=== FIM SMOKE C.1 ===")
            return 1

        mes_teste = int(selecao["mes"])
        ano_teste = int(selecao["ano"])
        calculo = dict(selecao["calculo_legacy"])
        valor_30 = round(float(selecao["valor_30"]), 2)
        base_calculo = round(float(selecao["base_calculo"]), 2)

        print("SELECAO_COMPETENCIA: OK")
        print(f"COMPETENCIA_SELECIONADA: {mes_teste:02d}/{ano_teste}")
        print(f"VALOR_30: {valor_30}")
        print(f"BASE_CALCULO: {base_calculo}")

        if (
            deploy["DEPLOY_VALIDADO"] != "SIM"
            or helper_ok != "SIM"
            or dialeto != "postgresql"
            or not tabelas_ok
            or valor_30 <= 0
            or admin_obrigacoes_query(mes_teste, ano_teste).first() is not None
        ):
            print("RESULTADO_SMOKE: FALHA")
            print("=== FIM SMOKE C.1 ===")
            return 1

        c_before = counts()
        saldo_antes = saldo_atual()

        print(f"ANTES_OBRIGACOES: {c_before['obrigacoes']}")
        print(f"ANTES_EVENTOS: {c_before['eventos']}")
        print(f"ANTES_PAGAMENTOS: {c_before['pagamentos']}")
        print(f"ANTES_ITENS: {c_before['itens']}")
        print(f"ANTES_LANCAMENTOS: {c_before['lancamentos']}")
        print(f"ANTES_ENVIOS: {c_before['envios']}")
        print(f"SALDO_ANTES: {saldo_antes}")

        try:
            r1 = _criar_obrigacao_admin_sede_sem_commit(mes_teste, ano_teste, percentual, calculo)
            primeira_chamada = r1.get("status", "ERRO")
            print(f"PRIMEIRA_CHAMADA: {primeira_chamada}")

            db.session.flush()

            obrigacoes_q = admin_obrigacoes_query(mes_teste, ano_teste)
            eventos_q = admin_eventos_query(mes_teste, ano_teste)
            obrigacao_obj = obrigacoes_q.first()

            obrigacao_criada = "SIM" if obrigacoes_q.count() == 1 else "NAO"
            evento_criado = "SIM" if eventos_q.count() == 1 else "NAO"

            if obrigacao_obj is not None:
                valor_devido_criado = round(float(obrigacao_obj.valor_devido or 0.0), 2)
                validacao_obrigacao_ok = "SIM" if (
                    obrigacao_obj.tipo_obrigacao == "ADMIN_SEDE_30"
                    and obrigacao_obj.origem_obrigacao == "automatico"
                    and obrigacao_obj.competencia_mes == mes_teste
                    and obrigacao_obj.competencia_ano == ano_teste
                    and valor_devido_criado == valor_30
                    and obrigacao_obj.status == "PENDENTE"
                ) else "NAO"

            print(f"VALIDACAO_OBRIGACAO: {validacao_obrigacao_ok}")

            c_durante = counts()
            saldo_durante = saldo_atual()

            lancamento_criado = "SIM" if c_durante["lancamentos"] != c_before["lancamentos"] else "NAO"
            pagamento_criado = "SIM" if c_durante["pagamentos"] != c_before["pagamentos"] else "NAO"
            item_criado = "SIM" if c_durante["itens"] != c_before["itens"] else "NAO"
            envio_sede_criado = "SIM" if c_durante["envios"] != c_before["envios"] else "NAO"

            print(f"OBRIGACAO_CRIADA: {obrigacao_criada}")
            print(f"EVENTO_CRIADO: {evento_criado}")
            print(f"LANCAMENTO_CRIADO: {lancamento_criado}")
            print(f"PAGAMENTO_CRIADO: {pagamento_criado}")
            print(f"ITEM_CRIADO: {item_criado}")
            print(f"ENVIO_SEDE_CRIADO: {envio_sede_criado}")
            print(f"SALDO_DURANTE: {saldo_durante}")

            r2 = _criar_obrigacao_admin_sede_sem_commit(mes_teste, ano_teste, percentual, calculo)
            segunda_chamada = r2.get("status", "ERRO")
            print(f"SEGUNDA_CHAMADA: {segunda_chamada}")

            db.session.flush()
            idempotencia = "OK" if (obrigacoes_q.count() == 1 and eventos_q.count() == 1) else "FALHA"
            print(f"IDEMPOTENCIA: {idempotencia}")

        except Exception as exc:
            erro_smoke = exc
            print(f"ERRO_SMOKE: {type(exc).__name__}: {exc}")
        finally:
            db.session.rollback()
            rollback_executado = "SIM"
            print(f"ROLLBACK_EXECUTADO: {rollback_executado}")

        db.session.remove()

    with app.app_context():
        c_after = counts()
        saldo_depois = saldo_atual()

        obrigacao_persistiu = admin_obrigacoes_query(mes_teste, ano_teste).first() is not None
        evento_persistiu = admin_eventos_query(mes_teste, ano_teste).first() is not None

        contagens_restauradas = c_after == c_before
        saldo_inalterado = saldo_depois == saldo_antes

        print(f"DEPOIS_OBRIGACOES: {c_after['obrigacoes']}")
        print(f"DEPOIS_EVENTOS: {c_after['eventos']}")
        print(f"DEPOIS_PAGAMENTOS: {c_after['pagamentos']}")
        print(f"DEPOIS_ITENS: {c_after['itens']}")
        print(f"DEPOIS_LANCAMENTOS: {c_after['lancamentos']}")
        print(f"DEPOIS_ENVIOS: {c_after['envios']}")
        print(f"SALDO_DEPOIS: {saldo_depois}")
        print(f"OBRIGACAO_TESTE_PERSISTIU: {'SIM' if obrigacao_persistiu else 'NAO'}")
        print(f"EVENTO_TESTE_PERSISTIU: {'SIM' if evento_persistiu else 'NAO'}")
        print(f"CONTAGENS_RESTAURADAS: {'SIM' if contagens_restauradas else 'NAO'}")
        print(f"SALDO_INALTERADO: {'SIM' if saldo_inalterado else 'NAO'}")

        aprovado = (
            erro_smoke is None
            and primeira_chamada == "criada"
            and segunda_chamada == "ja_existente"
            and obrigacao_criada == "SIM"
            and evento_criado == "SIM"
            and validacao_obrigacao_ok == "SIM"
            and idempotencia == "OK"
            and lancamento_criado == "NAO"
            and pagamento_criado == "NAO"
            and item_criado == "NAO"
            and envio_sede_criado == "NAO"
            and saldo_durante == saldo_antes
            and rollback_executado == "SIM"
            and not obrigacao_persistiu
            and not evento_persistiu
            and contagens_restauradas
            and saldo_inalterado
        )

        resultado_smoke = "APROVADO" if aprovado else "FALHA"
        print(f"RESULTADO_SMOKE: {resultado_smoke}")
        print("=== FIM SMOKE C.1 ===")
        return 0 if aprovado else 40


if __name__ == "__main__":
    raise SystemExit(main())