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


def counts() -> dict[str, int]:
    return {
        "obrigacoes": ObrigacaoFinanceira.query.count(),
        "eventos": ObrigacaoEvento.query.count(),
        "pagamentos": PagamentoObrigacao.query.count(),
        "itens": PagamentoObrigacaoItem.query.count(),
        "lancamentos": Lancamento.query.count(),
        "envios": EnviosedeCount.count(),
    }


class EnviosedeCount:
    @staticmethod
    def count() -> int:
        return int(db.session.query(EnvioSede).count())


def obrigacao_teste_existe(despesa_id: int, mes: int, ano: int) -> bool:
    return ObrigacaoFinanceira.query.filter(
        ObrigacaoFinanceira.tipo_obrigacao == "DESPESA_FIXA",
        ObrigacaoFinanceira.origem_obrigacao == "automatico",
        ObrigacaoFinanceira.referencia_origem_tipo == "DESPESA_FIXA_CONSELHO",
        ObrigacaoFinanceira.referencia_origem_id == despesa_id,
        ObrigacaoFinanceira.competencia_mes == mes,
        ObrigacaoFinanceira.competencia_ano == ano,
    ).first() is not None


def selecionar_candidata() -> DespesaFixaConselho | None:
    return DespesaFixaConselho.query.filter_by(ativo=True).order_by(DespesaFixaConselho.id.asc()).first()


def main() -> int:
    print("=== SMOKE B.3 PRODUCAO ===")

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
    idempotencia = "FALHA"
    saldo_durante = None

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
        required = {
            "obrigacoes_financeiras",
            "pagamentos_obrigacao",
            "pagamentos_obrigacao_itens",
            "obrigacao_eventos",
            "lancamentos",
            "envios_sede",
            "despesas_fixas_conselho",
        }
        if (
            deploy["DEPLOY_VALIDADO"] != "SIM"
            or helper_existe != "SIM"
            or dialeto != "postgresql"
            or not required.issubset(set(insp.get_table_names()))
        ):
            print(f"RESULTADO_SMOKE: {resultado_smoke}")
            print("=== FIM SMOKE B.3 ===")
            return 1

        despesa = selecionar_candidata()
        if despesa is None:
            print("DESPESA_ID: NONE")
            print("DESPESA_NOME: NONE")
            print("DESPESA_VALOR: NONE")
            print("DESPESA_CATEGORIA: NONE")
            print(f"COMPETENCIA: {MES_TESTE:02d}/{ANO_TESTE}")
            print(f"RESULTADO_SMOKE: {resultado_smoke}")
            print("=== FIM SMOKE B.3 ===")
            return 1

        despesa_id = int(despesa.id)
        despesa_nome = despesa.nome
        despesa_valor = float(despesa.valor_padrao or 0)
        despesa_categoria = (despesa.categoria or "").strip()

        if obrigacao_teste_existe(despesa_id, MES_TESTE, ANO_TESTE):
            print(f"DESPESA_ID: {despesa_id}")
            print(f"DESPESA_NOME: {despesa_nome}")
            print(f"DESPESA_VALOR: {despesa_valor:.2f}")
            print(f"DESPESA_CATEGORIA: {despesa_categoria}")
            print(f"COMPETENCIA: {MES_TESTE:02d}/{ANO_TESTE}")
            print(f"RESULTADO_SMOKE: {resultado_smoke}")
            print("=== FIM SMOKE B.3 ===")
            return 1

        c_before = counts()
        saldo_antes = saldo_atual()

        print(f"DESPESA_ID: {despesa_id}")
        print(f"DESPESA_NOME: {despesa_nome}")
        print(f"DESPESA_VALOR: {despesa_valor:.2f}")
        print(f"DESPESA_CATEGORIA: {despesa_categoria}")
        print(f"COMPETENCIA: {MES_TESTE:02d}/{ANO_TESTE}")
        print(f"ANTES_OBRIGACOES: {c_before['obrigacoes']}")
        print(f"ANTES_EVENTOS: {c_before['eventos']}")
        print(f"ANTES_PAGAMENTOS: {c_before['pagamentos']}")
        print(f"ANTES_ITENS: {c_before['itens']}")
        print(f"ANTES_LANCAMENTOS: {c_before['lancamentos']}")
        print(f"ANTES_ENVIOS: {c_before['envios']}")
        print(f"SALDO_ANTES: {saldo_antes}")

        try:
            r1 = _criar_obrigacao_despesa_fixa_sem_commit(despesa, MES_TESTE, ANO_TESTE)
            primeira_chamada = r1.get("status", "ERRO")
            print(f"PRIMEIRA_CHAMADA: {primeira_chamada}")

            db.session.flush()

            obrigacoes_durante_q = ObrigacaoFinanceira.query.filter(
                ObrigacaoFinanceira.tipo_obrigacao == "DESPESA_FIXA",
                ObrigacaoFinanceira.origem_obrigacao == "automatico",
                ObrigacaoFinanceira.referencia_origem_tipo == "DESPESA_FIXA_CONSELHO",
                ObrigacaoFinanceira.referencia_origem_id == despesa_id,
                ObrigacaoFinanceira.competencia_mes == MES_TESTE,
                ObrigacaoFinanceira.competencia_ano == ANO_TESTE,
            )
            eventos_durante_q = ObrigacaoEvento.query.join(
                ObrigacaoFinanceira,
                ObrigacaoEvento.obrigacao_financeira_id == ObrigacaoFinanceira.id,
            ).filter(
                ObrigacaoFinanceira.tipo_obrigacao == "DESPESA_FIXA",
                ObrigacaoFinanceira.origem_obrigacao == "automatico",
                ObrigacaoFinanceira.referencia_origem_tipo == "DESPESA_FIXA_CONSELHO",
                ObrigacaoFinanceira.referencia_origem_id == despesa_id,
                ObrigacaoFinanceira.competencia_mes == MES_TESTE,
                ObrigacaoFinanceira.competencia_ano == ANO_TESTE,
                ObrigacaoEvento.evento_tipo == "CRIACAO",
            )

            obrigacao_criada = "SIM" if obrigacoes_durante_q.count() == 1 else "NAO"
            evento_criado = "SIM" if eventos_durante_q.count() == 1 else "NAO"

            c_durante = counts()
            saldo_durante = saldo_atual()

            lancamento_criado = "SIM" if c_durante["lancamentos"] != c_before["lancamentos"] else "NAO"
            pagamento_criado = "SIM" if c_durante["pagamentos"] != c_before["pagamentos"] else "NAO"
            item_criado = "SIM" if c_durante["itens"] != c_before["itens"] else "NAO"

            print(f"OBRIGACAO_CRIADA: {obrigacao_criada}")
            print(f"EVENTO_CRIADO: {evento_criado}")
            print(f"LANCAMENTO_CRIADO: {lancamento_criado}")
            print(f"PAGAMENTO_CRIADO: {pagamento_criado}")
            print(f"ITEM_CRIADO: {item_criado}")
            print(f"SALDO_DURANTE: {saldo_durante}")

            r2 = _criar_obrigacao_despesa_fixa_sem_commit(despesa, MES_TESTE, ANO_TESTE)
            segunda_chamada = r2.get("status", "ERRO")
            print(f"SEGUNDA_CHAMADA: {segunda_chamada}")

            db.session.flush()

            idempotencia = "OK" if (obrigacoes_durante_q.count() == 1 and eventos_durante_q.count() == 1) else "FALHA"
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

        obrigacao_teste_persistiu = obrigacao_teste_existe(despesa_id, MES_TESTE, ANO_TESTE)
        evento_teste_persistiu = ObrigacaoEvento.query.join(
            ObrigacaoFinanceira,
            ObrigacaoEvento.obrigacao_financeira_id == ObrigacaoFinanceira.id,
        ).filter(
            ObrigacaoFinanceira.tipo_obrigacao == "DESPESA_FIXA",
            ObrigacaoFinanceira.origem_obrigacao == "automatico",
            ObrigacaoFinanceira.referencia_origem_tipo == "DESPESA_FIXA_CONSELHO",
            ObrigacaoFinanceira.referencia_origem_id == despesa_id,
            ObrigacaoFinanceira.competencia_mes == MES_TESTE,
            ObrigacaoFinanceira.competencia_ano == ANO_TESTE,
            ObrigacaoEvento.evento_tipo == "CRIACAO",
        ).first() is not None

        contagens_restauradas = c_after == c_before
        saldo_inalterado = saldo_depois == saldo_antes

        print(f"DEPOIS_OBRIGACOES: {c_after['obrigacoes']}")
        print(f"DEPOIS_EVENTOS: {c_after['eventos']}")
        print(f"DEPOIS_PAGAMENTOS: {c_after['pagamentos']}")
        print(f"DEPOIS_ITENS: {c_after['itens']}")
        print(f"DEPOIS_LANCAMENTOS: {c_after['lancamentos']}")
        print(f"DEPOIS_ENVIOS: {c_after['envios']}")
        print(f"SALDO_DEPOIS: {saldo_depois}")
        print(f"OBRIGACAO_TESTE_PERSISTIU: {'SIM' if obrigacao_teste_persistiu else 'NAO'}")
        print(f"EVENTO_TESTE_PERSISTIU: {'SIM' if evento_teste_persistiu else 'NAO'}")
        print(f"CONTAGENS_RESTAURADAS: {'SIM' if contagens_restauradas else 'NAO'}")
        print(f"SALDO_INALTERADO: {'SIM' if saldo_inalterado else 'NAO'}")

        aprovado = (
            erro_smoke is None
            and primeira_chamada == "criada"
            and segunda_chamada == "ja_existente"
            and idempotencia == "OK"
            and rollback_executado == "SIM"
            and obrigacao_teste_persistiu is False
            and evento_teste_persistiu is False
            and contagens_restauradas
            and saldo_inalterado
            and lancamento_criado == "NAO"
            and pagamento_criado == "NAO"
            and item_criado == "NAO"
        )

        resultado_smoke = "APROVADO" if aprovado else "FALHA"
        print(f"RESULTADO_SMOKE: {resultado_smoke}")
        print("=== FIM SMOKE B.3 ===")

        if not aprovado:
            return 40

    return 0


if __name__ == "__main__":
    raise SystemExit(main())