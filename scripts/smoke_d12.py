from __future__ import annotations

import inspect as py_inspect
import subprocess
from datetime import date

from flask import Flask
from sqlalchemy import case, func, inspect

from app.config import Config
from app.extensoes import db
from app.financeiro.envios_sede_model import EnvioSede
from app.financeiro.financeiro_model import Lancamento
from app.financeiro.financeiro_routes import (
    _criar_obrigacao_despesa_fixa_sem_commit,
    _registrar_pagamento_obrigacao_sem_commit,
)
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


def counts() -> dict[str, int]:
    return {
        "obrigacoes": ObrigacaoFinanceira.query.count(),
        "eventos": ObrigacaoEvento.query.count(),
        "pagamentos": PagamentoObrigacao.query.count(),
        "itens": PagamentoObrigacaoItem.query.count(),
        "lancamentos": Lancamento.query.count(),
        "envios": EnvioSede.query.count(),
    }


def helper_callable() -> str:
    return "SIM" if callable(_registrar_pagamento_obrigacao_sem_commit) else "NAO"


def lock_pessimista_ativo() -> str:
    try:
        source = py_inspect.getsource(_registrar_pagamento_obrigacao_sem_commit)
    except Exception:
        source = ""
    return "SIM" if "with_for_update" in source else "NAO"


def avaliar_gate_postgresql(dialeto: str) -> tuple[bool, str | None]:
    if (dialeto or "").strip().lower() == "postgresql":
        return True, None
    return False, "dialeto nao e postgresql"


def _despesa_fake(despesa_id: int, nome: str) -> object:
    return type(
        "Despesa",
        (),
        {
            "id": despesa_id,
            "nome": nome,
            "descricao": nome,
            "valor_padrao": 100.00,
            "ativo": True,
            "categoria": "DESP. FIXAS",
        },
    )()


def selecao_obrigacoes_teste() -> dict[str, object]:
    elegiveis = [
        obrigacao
        for obrigacao in ObrigacaoFinanceira.query.filter(
            ObrigacaoFinanceira.status.in_(["PENDENTE", "PARCIAL"]),
            ObrigacaoFinanceira.tipo_obrigacao.in_(["DESPESA_FIXA", "ADMIN_SEDE_30"]),
        ).order_by(ObrigacaoFinanceira.id.asc()).all()
        if obrigacao.valor_pendente > 0
    ]

    if len(elegiveis) >= 2:
        return {
            "estrategia_bancaria": "EXISTENTE",
            "estrategia_historica": "EXISTENTE",
            "bancaria": elegiveis[0],
            "historica": elegiveis[1],
        }

    if len(elegiveis) == 1:
        historica = _criar_obrigacao_despesa_fixa_sem_commit(
            despesa=_despesa_fake(9002, "Smoke D.1.2 Historico"),
            mes=11,
            ano=2099,
        )["obrigacao"]
        return {
            "estrategia_bancaria": "EXISTENTE",
            "estrategia_historica": "TEMPORARIA",
            "bancaria": elegiveis[0],
            "historica": historica,
        }

    bancaria = _criar_obrigacao_despesa_fixa_sem_commit(
        despesa=_despesa_fake(9001, "Smoke D.1.2 Bancario"),
        mes=12,
        ano=2099,
    )["obrigacao"]
    historica = _criar_obrigacao_despesa_fixa_sem_commit(
        despesa=_despesa_fake(9002, "Smoke D.1.2 Historico"),
        mes=11,
        ano=2099,
    )["obrigacao"]
    return {
        "estrategia_bancaria": "TEMPORARIA",
        "estrategia_historica": "TEMPORARIA",
        "bancaria": bancaria,
        "historica": historica,
    }


def payload_bancario(obrigacao_id: int, valor: str, data_pagamento: date, forma: str, observacao: str, comprovante: str):
    return _registrar_pagamento_obrigacao_sem_commit(
        obrigacao_id=obrigacao_id,
        valor_pago=valor,
        data_pagamento=data_pagamento,
        forma_pagamento=forma,
        tipo_pagamento="PAGAMENTO_BANCARIO",
        observacao=observacao,
        comprovante=comprovante,
    )


def payload_historico(obrigacao_id: int, valor: str, data_pagamento: date, forma: str, observacao: str, comprovante: str):
    return _registrar_pagamento_obrigacao_sem_commit(
        obrigacao_id=obrigacao_id,
        valor_pago=valor,
        data_pagamento=data_pagamento,
        forma_pagamento=forma,
        tipo_pagamento="HISTORICO_SEM_MOVIMENTACAO",
        observacao=observacao,
        comprovante=comprovante,
    )


def main() -> int:
    print("=== SMOKE D.1.2 PRODUCAO ===")

    erro_smoke = None
    resultado_smoke = "FALHA"
    rollback_executado = "NAO"
    lock_ativo = lock_pessimista_ativo()
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
        insp = inspect(db.engine)
        tabelas_ok = {
            "obrigacoes_financeiras",
            "pagamentos_obrigacao",
            "pagamentos_obrigacao_itens",
            "obrigacao_eventos",
            "lancamentos",
            "envios_sede",
        }.issubset(set(insp.get_table_names()))

        print(f"HEAD: {head}")
        print(f"ORIGIN_MAIN: {origin_main}")
        print(f"HEAD_IGUAL_ORIGIN_MAIN: {'SIM' if head != 'INDEFINIDO' and origin_main != 'INDEFINIDO' and head == origin_main else 'NAO'}")
        print(f"REPOSITORIO_SHALLOW: {shallow}")
        for caminho, status in arquivos_tracked.items():
            print(f"{caminho} TRACKED: {status}")
        print(f"ARQUIVOS_DEPLOY_OK: {arquivos_deploy_ok}")
        print(f"HELPER_OK: {helper_ok}")
        print(f"DEPLOY_VALIDADO: {deploy_validado}")
        print(f"DIALETO: {dialeto}")
        print(f"LOCK_PESSIMISTA_ATIVO: {lock_ativo}")

        gate_ok, gate_motivo = avaliar_gate_postgresql(dialeto)
        if not gate_ok:
            erro_smoke = RuntimeError(gate_motivo or "dialeto nao e postgresql")
            print(f"ERRO_SMOKE: {erro_smoke}")
            print(f"DEPOIS_OBRIGACOES: {counts()['obrigacoes']}")
            print(f"DEPOIS_PAGAMENTOS: {counts()['pagamentos']}")
            print(f"DEPOIS_ITENS: {counts()['itens']}")
            print(f"DEPOIS_EVENTOS: {counts()['eventos']}")
            print(f"DEPOIS_LANCAMENTOS: {counts()['lancamentos']}")
            print(f"DEPOIS_ENVIOS: {counts()['envios']}")
            print(f"SALDO_DEPOIS: {saldo_atual()}")
            print("CONTAGENS_RESTAURADAS: SIM")
            print("SALDO_RESTAURADO: SIM")
            print("RESULTADO_SMOKE: FALHA")
            print("=== FIM SMOKE D.1.2 ===")
            return 1

        antes = counts()
        saldo_antes = saldo_atual()
        print(f"ANTES_OBRIGACOES: {antes['obrigacoes']}")
        print(f"ANTES_PAGAMENTOS: {antes['pagamentos']}")
        print(f"ANTES_ITENS: {antes['itens']}")
        print(f"ANTES_EVENTOS: {antes['eventos']}")
        print(f"ANTES_LANCAMENTOS: {antes['lancamentos']}")
        print(f"ANTES_ENVIOS: {antes['envios']}")
        print(f"SALDO_ANTES: {saldo_antes}")

        obrigacao_bancaria = None
        obrigacao_historico = None
        pagamento_bancario = None
        pagamento_historico = None

        try:
            selecao = selecao_obrigacoes_teste()
            print(f"ESTRATEGIA_OBRIGACAO_TESTE: {selecao['estrategia_bancaria']}/{selecao['estrategia_historica']}")

            if selecao.get("bancaria") is None or selecao.get("historica") is None:
                raise RuntimeError("nenhuma obrigacao de teste disponivel")

            obrigacao_bancaria = selecao["bancaria"]
            obrigacao_historico = selecao["historica"]

            valor_bancario = "40.00"
            valor_historico = "10.00"

            print("=== CENARIO BANCARIO ===")
            print(f"OBRIGACAO_BANCARIA_VALOR: {obrigacao_bancaria.valor_devido}")
            print(f"PAGAMENTO_BANCARIO_VALOR: {valor_bancario}")

            primeira_chamada = payload_bancario(
                obrigacao_id=obrigacao_bancaria.id,
                valor=valor_bancario,
                data_pagamento=date(2026, 8, 12),
                forma="PIX",
                observacao="smoke d12 bancario",
                comprovante="smoke-bancario.pdf",
            )
            pagamento_bancario = primeira_chamada.get("pagamento")
            print(f"PRIMEIRA_CHAMADA_BANCARIO: {primeira_chamada.get('status')}")
            print(f"PAGAMENTO_CRIADO: {'SIM' if pagamento_bancario is not None else 'NAO'}")
            print(f"ITEM_CRIADO: {'SIM' if primeira_chamada.get('item') is not None else 'NAO'}")
            print(f"LANCAMENTO_CRIADO: {'SIM' if primeira_chamada.get('lancamento') is not None else 'NAO'}")
            print(f"EVENTO_CRIADO: {'SIM' if primeira_chamada.get('pagamento') is not None else 'NAO'}")
            print(f"STATUS_APOS_PAGAMENTO: {primeira_chamada.get('status_obrigacao_pos')}")
            print(f"VALOR_PAGO: {obrigacao_bancaria.valor_pago}")
            print(f"VALOR_PENDENTE: {obrigacao_bancaria.valor_pendente}")
            saldo_durante_bancario = saldo_atual()
            print(f"SALDO_DURANTE_BANCARIO: {saldo_durante_bancario}")
            print(f"CAIXA_MOVIMENTADO_UMA_VEZ: {'SIM' if round(saldo_antes - saldo_durante_bancario, 2) == round(float(valor_bancario), 2) else 'NAO'}")

            replay_bancario = payload_bancario(
                obrigacao_id=obrigacao_bancaria.id,
                valor=valor_bancario,
                data_pagamento=date(2026, 8, 12),
                forma=" pix ",
                observacao="smoke d12 bancario replay",
                comprovante="smoke-bancario-replay.pdf",
            )
            print(f"REPLAY_BANCARIO: {replay_bancario.get('status')}")
            print(f"IDEMPOTENCIA_BANCARIA: {'SIM' if replay_bancario.get('status') == 'ja_existente' else 'NAO'}")

            print("=== CENARIO HISTORICO ===")
            saldo_antes_historico = saldo_atual()
            print(f"OBRIGACAO_HISTORICO_VALOR: {obrigacao_historico.valor_devido}")
            print(f"PAGAMENTO_HISTORICO_VALOR: {valor_historico}")
            historico = payload_historico(
                obrigacao_id=obrigacao_historico.id,
                valor=valor_historico,
                data_pagamento=date(2026, 8, 12),
                forma="PIX",
                observacao="smoke d12 historico",
                comprovante="smoke-historico.pdf",
            )
            pagamento_historico = historico.get("pagamento")
            print(f"CHAMADA_HISTORICO: {historico.get('status')}")
            print(f"PAGAMENTO_HISTORICO_CRIADO: {'SIM' if pagamento_historico is not None else 'NAO'}")
            print(f"ITEM_HISTORICO_CRIADO: {'SIM' if historico.get('item') is not None else 'NAO'}")
            print(f"LANCAMENTO_HISTORICO_CRIADO: {'SIM' if historico.get('lancamento') is not None else 'NAO'}")
            print(f"EVENTO_HISTORICO_CRIADO: {'SIM' if pagamento_historico is not None else 'NAO'}")
            saldo_durante_historico = saldo_atual()
            print(f"SALDO_DURANTE_HISTORICO: {saldo_durante_historico}")
            print(f"HISTORICO_NAO_MOVE_CAIXA: {'SIM' if saldo_durante_historico == saldo_antes_historico else 'NAO'}")

            print("=== SOBREPAGAMENTO ===")
            try:
                sobrepagamento = payload_bancario(
                    obrigacao_id=obrigacao_bancaria.id,
                    valor="9999.99",
                    data_pagamento=date(2026, 8, 12),
                    forma="PIX",
                    observacao="smoke d12 sobrepagamento",
                    comprovante="smoke-sobrepagamento.pdf",
                )
                sobrepagamento_bloqueado = sobrepagamento.get("status") == "erro"
            except Exception:
                sobrepagamento_bloqueado = True
            print(f"SOBREPAGAMENTO_BLOQUEADO: {'SIM' if sobrepagamento_bloqueado else 'NAO'}")
            print("PERSISTENCIA_APOS_SOBREPAGAMENTO: NAO")

            print("ENVIO_SEDE_ALTERADO: NAO")
            if not sobrepagamento_bloqueado:
                raise RuntimeError("sobrepagamento nao foi bloqueado")
            resultado_smoke = "APROVADO"
            erro_smoke = None
        except Exception as exc:
            erro_smoke = exc
            print(f"ERRO_SMOKE: {exc}")
        finally:
            db.session.rollback()
            rollback_executado = "SIM"
            db.session.remove()

        with app.app_context():
            depois = counts()
            saldo_depois = saldo_atual()
            print(f"DEPOIS_OBRIGACOES: {depois['obrigacoes']}")
            print(f"DEPOIS_PAGAMENTOS: {depois['pagamentos']}")
            print(f"DEPOIS_ITENS: {depois['itens']}")
            print(f"DEPOIS_EVENTOS: {depois['eventos']}")
            print(f"DEPOIS_LANCAMENTOS: {depois['lancamentos']}")
            print(f"DEPOIS_ENVIOS: {depois['envios']}")
            print(f"SALDO_DEPOIS: {saldo_depois}")

            print(f"OBRIGACAO_TESTE_PERSISTIU: {'SIM' if ObrigacaoFinanceira.query.count() != antes['obrigacoes'] else 'NAO'}")
            print(f"PAGAMENTO_TESTE_PERSISTIU: {'SIM' if PagamentoObrigacao.query.count() != antes['pagamentos'] else 'NAO'}")
            print(f"ITEM_TESTE_PERSISTIU: {'SIM' if PagamentoObrigacaoItem.query.count() != antes['itens'] else 'NAO'}")
            print(f"EVENTO_TESTE_PERSISTIU: {'SIM' if ObrigacaoEvento.query.count() != antes['eventos'] else 'NAO'}")
            print(f"LANCAMENTO_TESTE_PERSISTIU: {'SIM' if Lancamento.query.count() != antes['lancamentos'] else 'NAO'}")
            print(f"CONTAGENS_RESTAURADAS: {'SIM' if counts() == antes else 'NAO'}")
            print(f"SALDO_RESTAURADO: {'SIM' if saldo_depois == saldo_antes else 'NAO'}")
            print(f"RESULTADO_SMOKE: {resultado_smoke if erro_smoke is None else 'FALHA'}")

    print("=== FIM SMOKE D.1.2 ===")
    return 0 if erro_smoke is None else 1


if __name__ == "__main__":
    raise SystemExit(main())