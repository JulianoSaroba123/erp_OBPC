#!/usr/bin/env python3
"""
D.2.3D.22 - Executor da regularizacao historica 01/2026 a 05/2026.

Modos:
- --check (default): 100% read-only
- --apply: escrita explicita em transacao unica
"""

from __future__ import annotations

import argparse
import json
import os
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import create_engine, inspect, text

ESTADO_A = "ESTADO_A_APTO_PARA_REGULARIZAR"
ESTADO_B = "ESTADO_B_JA_APLICADO"
ESTADO_C = "ESTADO_C_PARCIAL_BLOQUEADO"
ESTADO_D = "ESTADO_D_INCOMPATIVEL"

TARGET_YEAR = 2026
TARGET_COMPS = [1, 2, 3, 4, 5, 6, 7]
APPLY_COMPS = [1, 4, 5]

FIXAS_MENSAL = Decimal("280.00")
ADMIN_DEVIDO_ESPERADO = {
    1: Decimal("1240.95"),
    2: Decimal("1361.01"),
    3: Decimal("1829.11"),
    4: Decimal("1865.34"),
    5: Decimal("1145.59"),
    6: Decimal("2403.31"),
    7: Decimal("1122.56"),
}

CHECK_SQL_STATEMENTS = [
    "SELECT COUNT(*) FROM obrigacoes_financeiras",
    "SELECT COUNT(*) FROM pagamentos_obrigacao",
    "SELECT COUNT(*) FROM pagamentos_obrigacao_itens",
    "SELECT COUNT(*) FROM obrigacao_eventos",
    "SELECT COUNT(*) FROM envios_sede",
    "SELECT COUNT(*) FROM lancamentos",
    "SELECT id, competencia_mes, competencia_ano, valor_devido, status FROM obrigacoes_financeiras WHERE origem_obrigacao='automatico' AND tipo_obrigacao='ADMIN_SEDE_30' AND competencia_ano=2026",
]


@dataclass
class ResultadoExecucao:
    ok: bool
    estado: str
    problemas: list[str]
    metricas: dict[str, Any]


@dataclass
class OperacaoRegularizacao:
    codigo: str
    competencia_mes: int
    forma_pagamento: str
    valor_admin: Decimal
    valor_fixas: Decimal
    valor_total_envio: Decimal
    data_pagamento: date
    observacao: str


def d2(v: Any) -> Decimal:
    if v is None:
        return Decimal("0.00")
    return Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money(v: Any) -> str:
    return f"{d2(v):.2f}"


def print_kv(chave: str, valor: Any):
    print(f"{chave}: {valor}")


def normalize_database_url(database_url: str | None) -> str | None:
    if not database_url:
        return None
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url


def avaliar_gate_postgresql(dialeto: str) -> tuple[bool, str | None]:
    if (dialeto or "").strip().lower() == "postgresql":
        return True, None
    return False, "dialeto nao e postgresql"


def is_sql_readonly(sql_text: str) -> bool:
    normalized = " ".join((sql_text or "").strip().lower().split())
    return normalized.startswith("select ") or normalized.startswith("with ")


def assert_sql_set_readonly(sql_statements: list[str]) -> bool:
    return all(is_sql_readonly(stmt) for stmt in sql_statements)


def snapshot_totais(conn) -> dict[str, Decimal]:
    def count_table(table_name: str) -> Decimal:
        return d2(conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar())

    saldo_lanc = d2(
        conn.execute(
            text(
                """
                SELECT COALESCE(
                    SUM(
                        CASE
                            WHEN lower(tipo)='entrada' THEN valor
                            WHEN lower(tipo) IN ('saída','saida') THEN -valor
                            ELSE 0
                        END
                    ),
                    0
                )
                FROM lancamentos
                """
            )
        ).scalar()
    )

    return {
        "TOTAL_OBRIGACOES": count_table("obrigacoes_financeiras"),
        "TOTAL_PAGAMENTOS": count_table("pagamentos_obrigacao"),
        "TOTAL_ITENS": count_table("pagamentos_obrigacao_itens"),
        "TOTAL_EVENTOS": count_table("obrigacao_eventos"),
        "TOTAL_ENVIOS": count_table("envios_sede"),
        "TOTAL_LANCAMENTOS": count_table("lancamentos"),
        "SALDO_LANCAMENTOS": saldo_lanc,
    }


def _comp_ord(mes: int, ano: int) -> str:
    return f"{int(mes):02d}/{int(ano)}"


def _fetch_existing(conn) -> dict[str, Any]:
    obrigacoes_rows = conn.execute(
        text(
            """
            SELECT id, competencia_mes, competencia_ano, valor_devido, status, origem_obrigacao, tipo_obrigacao
            FROM obrigacoes_financeiras
            WHERE origem_obrigacao='automatico'
              AND tipo_obrigacao='ADMIN_SEDE_30'
              AND competencia_ano=:ano
              AND competencia_mes IN (1,2,3,4,5,6,7)
            ORDER BY competencia_mes, id
            """
        ),
        {"ano": TARGET_YEAR},
    ).mappings().all()

    pagamentos_rows = conn.execute(
        text(
            """
            SELECT p.id, p.data_pagamento, p.valor_pago, p.forma_pagamento, p.tipo_pagamento,
                   p.observacao, p.lancamento_financeiro_id
            FROM pagamentos_obrigacao p
            ORDER BY p.id
            """
        )
    ).mappings().all()

    itens_rows = conn.execute(
        text(
            """
            SELECT i.id, i.pagamento_obrigacao_id, i.obrigacao_financeira_id, i.valor_alocado,
                   o.competencia_mes, o.competencia_ano
            FROM pagamentos_obrigacao_itens i
            JOIN obrigacoes_financeiras o ON o.id = i.obrigacao_financeira_id
            WHERE o.origem_obrigacao='automatico'
              AND o.tipo_obrigacao='ADMIN_SEDE_30'
              AND o.competencia_ano=:ano
              AND o.competencia_mes IN (1,2,3,4,5,6,7)
            ORDER BY i.id
            """
        ),
        {"ano": TARGET_YEAR},
    ).mappings().all()

    envios_rows = conn.execute(
        text(
            """
            SELECT id, pagamento_obrigacao_id, data_pagamento,
                   competencia_mes, competencia_ano, competencia_mes_ref, competencia_ano_ref,
                   valor, valor_total, valor_administrativo, valor_despesas_fixas,
                   forma_pagamento, tipo_pagamento, observacao, lancamento_financeiro_id
            FROM envios_sede
            ORDER BY id
            """
        )
    ).mappings().all()

    return {
        "obrigacoes": [dict(r) for r in obrigacoes_rows],
        "pagamentos": [dict(r) for r in pagamentos_rows],
        "itens": [dict(r) for r in itens_rows],
        "envios": [dict(r) for r in envios_rows],
    }


def _admin_due_by_comp(existing: dict[str, Any]) -> dict[int, Decimal]:
    out: dict[int, Decimal] = {}
    for r in existing["obrigacoes"]:
        mes = int(r["competencia_mes"])
        out[mes] = d2(r["valor_devido"])
    return out


def _admin_paid_by_comp(existing: dict[str, Any]) -> dict[int, Decimal]:
    out: dict[int, Decimal] = {m: Decimal("0.00") for m in TARGET_COMPS}
    for item in existing["itens"]:
        mes = int(item["competencia_mes"])
        out[mes] = d2(out.get(mes, Decimal("0.00")) + d2(item["valor_alocado"]))
    return out


def _fixas_envio_by_comp(existing: dict[str, Any]) -> dict[int, Decimal]:
    out: dict[int, Decimal] = {m: Decimal("0.00") for m in TARGET_COMPS}
    for e in existing["envios"]:
        mes = e.get("competencia_mes")
        ano = e.get("competencia_ano")
        if mes is None:
            mes = e.get("competencia_mes_ref")
        if ano is None:
            ano = e.get("competencia_ano_ref")
        if mes is None or ano is None:
            continue
        if int(ano) != TARGET_YEAR or int(mes) not in TARGET_COMPS:
            continue
        out[int(mes)] = d2(out.get(int(mes), Decimal("0.00")) + d2(e.get("valor_despesas_fixas")))
    return out


def _has_marker(existing: dict[str, Any], marker: str) -> bool:
    marker_norm = (marker or "").strip().lower()
    for p in existing["pagamentos"]:
        obs = (p.get("observacao") or "").strip().lower()
        if obs == marker_norm:
            return True
    return False


def _build_operations(existing: dict[str, Any]) -> list[OperacaoRegularizacao]:
    due = _admin_due_by_comp(existing)
    paid = _admin_paid_by_comp(existing)
    fixas = _fixas_envio_by_comp(existing)

    ops: list[OperacaoRegularizacao] = []

    jan_need = d2(due.get(1, Decimal("0.00")) - paid.get(1, Decimal("0.00")))
    if jan_need > Decimal("0.00") and not _has_marker(existing, "D23D22_JAN_ADMIN_095"):
        ops.append(
            OperacaoRegularizacao(
                codigo="D23D22_JAN_ADMIN_095",
                competencia_mes=1,
                forma_pagamento="Dinheiro",
                valor_admin=jan_need,
                valor_fixas=Decimal("0.00"),
                valor_total_envio=jan_need,
                data_pagamento=date(2026, 1, 1),
                observacao="D23D22_JAN_ADMIN_095",
            )
        )

    abr_need = d2(due.get(4, Decimal("0.00")) - paid.get(4, Decimal("0.00")))
    if abr_need > Decimal("0.00"):
        if not _has_marker(existing, "D23D22_ABR_ADMIN_PIX_1000"):
            ops.append(
                OperacaoRegularizacao(
                    codigo="D23D22_ABR_ADMIN_PIX_1000",
                    competencia_mes=4,
                    forma_pagamento="PIX",
                    valor_admin=Decimal("1000.00"),
                    valor_fixas=Decimal("0.00"),
                    valor_total_envio=Decimal("1000.00"),
                    data_pagamento=date(2026, 4, 30),
                    observacao="D23D22_ABR_ADMIN_PIX_1000",
                )
            )
        if not _has_marker(existing, "D23D22_ABR_ADMIN_DIN_21085"):
            ops.append(
                OperacaoRegularizacao(
                    codigo="D23D22_ABR_ADMIN_DIN_21085",
                    competencia_mes=4,
                    forma_pagamento="Dinheiro",
                    valor_admin=Decimal("210.85"),
                    valor_fixas=Decimal("0.00"),
                    valor_total_envio=Decimal("210.85"),
                    data_pagamento=date(2026, 4, 30),
                    observacao="D23D22_ABR_ADMIN_DIN_21085",
                )
            )

    mai_need = d2(due.get(5, Decimal("0.00")) - paid.get(5, Decimal("0.00")))
    mai_fixas_rep = fixas.get(5, Decimal("0.00"))
    if (mai_need > Decimal("0.00") or mai_fixas_rep < FIXAS_MENSAL) and not _has_marker(existing, "D23D22_MAI_ADMIN_114559_FIXAS_280"):
        ops.append(
            OperacaoRegularizacao(
                codigo="D23D22_MAI_ADMIN_114559_FIXAS_280",
                competencia_mes=5,
                forma_pagamento="PIX",
                valor_admin=Decimal("1145.59"),
                valor_fixas=FIXAS_MENSAL,
                valor_total_envio=Decimal("1425.59"),
                data_pagamento=date(2026, 5, 31),
                observacao="D23D22_MAI_ADMIN_114559_FIXAS_280",
            )
        )

    return ops


def _simulate_apply(existing: dict[str, Any], operations: list[OperacaoRegularizacao]) -> dict[str, Any]:
    sim = deepcopy(existing)
    next_pag_id = max([int(p["id"]) for p in sim["pagamentos"]] + [0]) + 1
    next_item_id = max([int(i["id"]) for i in sim["itens"]] + [0]) + 1
    next_envio_id = max([int(e["id"]) for e in sim["envios"]] + [0]) + 1

    ob_by_mes = {int(o["competencia_mes"]): int(o["id"]) for o in sim["obrigacoes"]}

    for op in operations:
        pag_id = next_pag_id
        next_pag_id += 1

        sim["pagamentos"].append(
            {
                "id": pag_id,
                "data_pagamento": op.data_pagamento,
                "valor_pago": op.valor_admin,
                "forma_pagamento": op.forma_pagamento,
                "tipo_pagamento": "HISTORICO_SEM_MOVIMENTACAO",
                "observacao": op.observacao,
                "lancamento_financeiro_id": None,
            }
        )

        sim["itens"].append(
            {
                "id": next_item_id,
                "pagamento_obrigacao_id": pag_id,
                "obrigacao_financeira_id": ob_by_mes[op.competencia_mes],
                "valor_alocado": op.valor_admin,
                "competencia_mes": op.competencia_mes,
                "competencia_ano": TARGET_YEAR,
            }
        )
        next_item_id += 1

        sim["envios"].append(
            {
                "id": next_envio_id,
                "pagamento_obrigacao_id": pag_id,
                "data_pagamento": op.data_pagamento,
                "competencia_mes": op.competencia_mes,
                "competencia_ano": TARGET_YEAR,
                "competencia_mes_ref": op.competencia_mes,
                "competencia_ano_ref": TARGET_YEAR,
                "valor": op.valor_total_envio,
                "valor_total": op.valor_total_envio,
                "valor_administrativo": op.valor_admin,
                "valor_despesas_fixas": op.valor_fixas,
                "forma_pagamento": op.forma_pagamento,
                "tipo_pagamento": "HISTORICO_SEM_MOVIMENTACAO",
                "observacao": op.observacao,
                "lancamento_financeiro_id": None,
            }
        )
        next_envio_id += 1

    return sim


def _build_state_table(existing: dict[str, Any]) -> dict[int, dict[str, Decimal | str]]:
    due = _admin_due_by_comp(existing)
    paid = _admin_paid_by_comp(existing)

    status_by_mes: dict[int, str] = {}
    for ob in existing["obrigacoes"]:
        status_by_mes[int(ob["competencia_mes"])] = ob["status"]

    out: dict[int, dict[str, Decimal | str]] = {}
    for mes in TARGET_COMPS:
        valor_devido = d2(due.get(mes, Decimal("0.00")))
        valor_pago = d2(paid.get(mes, Decimal("0.00")))
        saldo = d2(valor_devido - valor_pago)
        if saldo <= Decimal("0.00"):
            status = "PAGO"
        elif valor_pago > Decimal("0.00"):
            status = "PARCIAL"
        else:
            status = status_by_mes.get(mes, "PENDENTE")
        out[mes] = {
            "devido": valor_devido,
            "pago": valor_pago,
            "saldo": saldo,
            "status": status,
        }
    return out


def _saldo_admin_antes_junho(state_table: dict[int, dict[str, Decimal | str]]) -> Decimal:
    total = Decimal("0.00")
    for mes in [1, 2, 3, 4, 5]:
        total += d2(state_table[mes]["saldo"])
    return d2(total)


def classificar_estado(existing: dict[str, Any]) -> tuple[str, list[str], list[OperacaoRegularizacao], dict[int, dict[str, Decimal | str]]]:
    problemas: list[str] = []

    due = _admin_due_by_comp(existing)
    for mes in TARGET_COMPS:
        if mes not in due:
            problemas.append(f"obrigacao ADMIN_SEDE_30 ausente para {mes:02d}/{TARGET_YEAR}")
        elif d2(due[mes]) != ADMIN_DEVIDO_ESPERADO[mes]:
            problemas.append(
                f"valor_devido divergente em {mes:02d}/{TARGET_YEAR}: atual={money(due[mes])} esperado={money(ADMIN_DEVIDO_ESPERADO[mes])}"
            )

    state_now = _build_state_table(existing)
    if d2(state_now[6]["pago"]) != Decimal("0.00"):
        problemas.append("junho/2026 ja possui pagamento; escopo D23D22 exige junho sem pagamento")

    ops = _build_operations(existing)

    if problemas:
        return ESTADO_D, problemas, ops, state_now

    if not ops:
        if d2(_saldo_admin_antes_junho(state_now)) == Decimal("0.00"):
            return ESTADO_B, [], ops, state_now
        return ESTADO_C, ["sem operacoes planejadas, mas saldo antes de junho nao zerou"], ops, state_now

    # Se ha parte aplicada (marcadores) e ainda falta completar, bloquear para analise manual.
    tem_marcador = any(
        _has_marker(existing, marker)
        for marker in [
            "D23D22_JAN_ADMIN_095",
            "D23D22_ABR_ADMIN_PIX_1000",
            "D23D22_ABR_ADMIN_DIN_21085",
            "D23D22_MAI_ADMIN_114559_FIXAS_280",
        ]
    )
    if tem_marcador:
        return ESTADO_C, ["regularizacao parcialmente aplicada"], ops, state_now

    return ESTADO_A, [], ops, state_now


def executar_em_transacao(engine, executor_func):
    with engine.begin() as conn:
        return executor_func(conn)


def _insert_pagamento(conn, op: OperacaoRegularizacao, usuario: str | None) -> int:
    now = datetime.utcnow()
    pid = conn.execute(
        text(
            """
            INSERT INTO pagamentos_obrigacao
            (data_pagamento, valor_pago, forma_pagamento, tipo_pagamento, observacao,
             lancamento_financeiro_id, created_at, updated_at, criado_por, atualizado_por)
            VALUES
            (:data_pagamento, :valor_pago, :forma_pagamento, 'HISTORICO_SEM_MOVIMENTACAO', :observacao,
             NULL, :created_at, :updated_at, :criado_por, :atualizado_por)
            RETURNING id
            """
        ),
        {
            "data_pagamento": op.data_pagamento,
            "valor_pago": op.valor_admin,
            "forma_pagamento": op.forma_pagamento,
            "observacao": op.observacao,
            "created_at": now,
            "updated_at": now,
            "criado_por": usuario,
            "atualizado_por": usuario,
        },
    ).scalar_one()
    return int(pid)


def _insert_item(conn, pagamento_id: int, obrigacao_id: int, valor_alocado: Decimal):
    conn.execute(
        text(
            """
            INSERT INTO pagamentos_obrigacao_itens
            (pagamento_obrigacao_id, obrigacao_financeira_id, valor_alocado, created_at)
            VALUES
            (:pagamento_id, :obrigacao_id, :valor_alocado, :created_at)
            """
        ),
        {
            "pagamento_id": pagamento_id,
            "obrigacao_id": obrigacao_id,
            "valor_alocado": valor_alocado,
            "created_at": datetime.utcnow(),
        },
    )


def _insert_evento_pagamento(conn, obrigacao_id: int, pagamento_id: int, op: OperacaoRegularizacao, usuario: str | None):
    payload = json.dumps(
        {
            "pagamento_id": pagamento_id,
            "valor_alocado": money(op.valor_admin),
            "valor_total_operacao": money(op.valor_admin),
            "tipo_pagamento": "HISTORICO_SEM_MOVIMENTACAO",
            "lancamento_financeiro_id": None,
            "origem": "regularizacao_d23d22",
            "codigo": op.codigo,
        },
        ensure_ascii=False,
    )

    conn.execute(
        text(
            """
            INSERT INTO obrigacao_eventos
            (obrigacao_financeira_id, evento_tipo, payload_json, usuario, created_at)
            VALUES
            (:obrigacao_id, 'PAGAMENTO', :payload_json, :usuario, :created_at)
            """
        ),
        {
            "obrigacao_id": obrigacao_id,
            "payload_json": payload,
            "usuario": usuario,
            "created_at": datetime.utcnow(),
        },
    )


def _insert_envio(conn, pagamento_id: int, op: OperacaoRegularizacao):
    conn.execute(
        text(
            """
            INSERT INTO envios_sede
            (data_pagamento, valor, valor_administrativo, valor_despesas_fixas, valor_total,
             forma_pagamento, competencia, competencia_mes_ref, competencia_ano_ref,
             competencia_mes, competencia_ano, tipo_pagamento, pagamento_obrigacao_id,
             lancamento_financeiro_id, observacao, valor_devido_competencia,
             pagamento_historico_sem_movimentacao, data_pagamento_informada,
             created_at, updated_at)
            VALUES
            (:data_pagamento, :valor, :valor_admin, :valor_fixas, :valor_total,
             :forma_pagamento, :competencia, :comp_mes, :comp_ano,
             :comp_mes, :comp_ano, 'HISTORICO_SEM_MOVIMENTACAO', :pagamento_id,
             NULL, :observacao, :valor_total,
             TRUE, TRUE,
             :created_at, :updated_at)
            """
        ),
        {
            "data_pagamento": op.data_pagamento,
            "valor": op.valor_total_envio,
            "valor_admin": op.valor_admin,
            "valor_fixas": op.valor_fixas,
            "valor_total": op.valor_total_envio,
            "forma_pagamento": op.forma_pagamento,
            "competencia": f"Competência {op.competencia_mes:02d}/{TARGET_YEAR}",
            "comp_mes": op.competencia_mes,
            "comp_ano": TARGET_YEAR,
            "pagamento_id": pagamento_id,
            "observacao": op.observacao,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
    )


def _recalcular_status_obrigacao(conn, obrigacao_id: int):
    row = conn.execute(
        text(
            """
            SELECT o.valor_devido,
                   COALESCE(SUM(i.valor_alocado), 0) AS pago
            FROM obrigacoes_financeiras o
            LEFT JOIN pagamentos_obrigacao_itens i ON i.obrigacao_financeira_id = o.id
            WHERE o.id = :obrigacao_id
            GROUP BY o.id, o.valor_devido
            """
        ),
        {"obrigacao_id": obrigacao_id},
    ).mappings().one()

    devido = d2(row["valor_devido"])
    pago = d2(row["pago"])

    if pago <= Decimal("0.00"):
        status = "PENDENTE"
        data_quitacao = None
    elif pago < devido:
        status = "PARCIAL"
        data_quitacao = None
    else:
        status = "PAGO"
        data_quitacao = date.today()

    conn.execute(
        text(
            """
            UPDATE obrigacoes_financeiras
            SET status = :status,
                data_quitacao = :data_quitacao,
                updated_at = :updated_at
            WHERE id = :obrigacao_id
            """
        ),
        {
            "status": status,
            "data_quitacao": data_quitacao,
            "updated_at": datetime.utcnow(),
            "obrigacao_id": obrigacao_id,
        },
    )


def aplicar_regularizacao(conn, existing: dict[str, Any], operations: list[OperacaoRegularizacao], usuario: str | None) -> dict[str, Any]:
    obrigacao_por_mes = {int(r["competencia_mes"]): int(r["id"]) for r in existing["obrigacoes"]}

    applied = {
        "NOVOS_PAGAMENTOS": 0,
        "NOVOS_ITENS": 0,
        "NOVOS_ENVIOS": 0,
        "NOVOS_EVENTOS": 0,
        "NOVOS_LANCAMENTOS": 0,
    }

    for op in operations:
        if op.competencia_mes not in obrigacao_por_mes:
            raise RuntimeError(f"Obrigacao alvo inexistente para {op.competencia_mes:02d}/{TARGET_YEAR}")

        obrigacao_id = obrigacao_por_mes[op.competencia_mes]
        pagamento_id = _insert_pagamento(conn, op, usuario)
        applied["NOVOS_PAGAMENTOS"] += 1

        _insert_item(conn, pagamento_id, obrigacao_id, op.valor_admin)
        applied["NOVOS_ITENS"] += 1

        _insert_evento_pagamento(conn, obrigacao_id, pagamento_id, op, usuario)
        applied["NOVOS_EVENTOS"] += 1

        _insert_envio(conn, pagamento_id, op)
        applied["NOVOS_ENVIOS"] += 1

        _recalcular_status_obrigacao(conn, obrigacao_id)

    return applied


def run_check(conn, usuario: str | None = None) -> ResultadoExecucao:
    if not assert_sql_set_readonly(CHECK_SQL_STATEMENTS):
        return ResultadoExecucao(False, ESTADO_D, ["check sql contem escrita"], {})

    before = snapshot_totais(conn)
    existing = _fetch_existing(conn)
    estado, problemas, ops, state_now = classificar_estado(existing)

    sim = _simulate_apply(existing, ops)
    state_sim = _build_state_table(sim)
    saldo_antes_junho_pos = _saldo_admin_antes_junho(state_sim)

    metricas = {
        "ESTADO": estado,
        "OPERACOES_PLANEJADAS": len(ops),
        "SALDO_ANTES_JUNHO_ATUAL": money(_saldo_admin_antes_junho(state_now)),
        "SALDO_ANTES_JUNHO_POS_SIM": money(saldo_antes_junho_pos),
        "JUNHO_SALDO_POS_SIM": money(state_sim[6]["saldo"]),
        "JULHO_SALDO_POS_SIM": money(state_sim[7]["saldo"]),
        "SNAPSHOT_ANTES": {k: money(v) for k, v in before.items()},
    }

    if ops:
        metricas["OPERACOES"] = [
            {
                "codigo": op.codigo,
                "competencia": _comp_ord(op.competencia_mes, TARGET_YEAR),
                "forma": op.forma_pagamento,
                "admin": money(op.valor_admin),
                "fixas": money(op.valor_fixas),
                "envio_total": money(op.valor_total_envio),
                "data": str(op.data_pagamento),
            }
            for op in ops
        ]

    ok = estado in {ESTADO_A, ESTADO_B} and len(problemas) == 0
    return ResultadoExecucao(ok=ok, estado=estado, problemas=problemas, metricas=metricas)


def run_apply(conn, usuario: str | None = None) -> ResultadoExecucao:
    before = snapshot_totais(conn)
    existing = _fetch_existing(conn)
    estado, problemas, ops, _state_now = classificar_estado(existing)

    if estado == ESTADO_B:
        return ResultadoExecucao(
            ok=True,
            estado=ESTADO_B,
            problemas=[],
            metricas={
                "JA_APLICADO": True,
                "NOVOS_PAGAMENTOS": 0,
                "NOVOS_ITENS": 0,
                "NOVOS_ENVIOS": 0,
                "NOVOS_EVENTOS": 0,
                "NOVOS_LANCAMENTOS": 0,
                "SNAPSHOT_ANTES": {k: money(v) for k, v in before.items()},
                "SNAPSHOT_DEPOIS": {k: money(v) for k, v in before.items()},
            },
        )

    if estado != ESTADO_A:
        return ResultadoExecucao(False, estado, problemas or ["estado bloqueado para apply"], {"SNAPSHOT_ANTES": {k: money(v) for k, v in before.items()}})

    applied = aplicar_regularizacao(conn, existing, ops, usuario)

    after = snapshot_totais(conn)

    existing_after = _fetch_existing(conn)
    state_after = _build_state_table(existing_after)
    saldo_antes_junho_pos = _saldo_admin_antes_junho(state_after)

    novos_lanc = d2(after["TOTAL_LANCAMENTOS"] - before["TOTAL_LANCAMENTOS"])
    mov_caixa = d2(after["SALDO_LANCAMENTOS"] - before["SALDO_LANCAMENTOS"])

    metricas = {
        **applied,
        "SALDO_ANTES_JUNHO_POS": money(saldo_antes_junho_pos),
        "JUNHO_POS": money(state_after[6]["saldo"]),
        "JULHO_POS": money(state_after[7]["saldo"]),
        "NOVOS_LANCAMENTOS": int(novos_lanc),
        "MOVIMENTACAO_CAIXA": money(mov_caixa),
        "SNAPSHOT_ANTES": {k: money(v) for k, v in before.items()},
        "SNAPSHOT_DEPOIS": {k: money(v) for k, v in after.items()},
    }

    problemas_apply: list[str] = []
    for mes in [1, 2, 3, 4, 5]:
        if d2(state_after[mes]["saldo"]) != Decimal("0.00"):
            problemas_apply.append(f"saldo nao zerado em {mes:02d}/{TARGET_YEAR}: {money(state_after[mes]['saldo'])}")

    if d2(state_after[6]["saldo"]) != Decimal("2403.31"):
        problemas_apply.append(f"junho alterado indevidamente: {money(state_after[6]['saldo'])}")

    if int(novos_lanc) != 0:
        problemas_apply.append(f"novos lancamentos detectados: {int(novos_lanc)}")

    if d2(mov_caixa) != Decimal("0.00"):
        problemas_apply.append(f"movimentacao de caixa detectada: {money(mov_caixa)}")

    ok = len(problemas_apply) == 0
    return ResultadoExecucao(ok=ok, estado=ESTADO_B if ok else ESTADO_C, problemas=problemas_apply, metricas=metricas)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Executor D23D22 - regularizacao historica sede")
    parser.add_argument("--apply", action="store_true", help="aplica a regularizacao (transacao unica)")
    parser.add_argument("--database-url", default=None, help="sobrescreve DATABASE_URL")
    parser.add_argument("--usuario", default="d23d22_executor", help="usuario para trilha de auditoria")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    database_url = normalize_database_url(args.database_url or os.getenv("DATABASE_URL"))
    if not database_url:
        print_kv("EXECUCAO", "BLOQUEADA")
        print_kv("MOTIVO", "DATABASE_URL ausente")
        return 2

    engine = create_engine(database_url)
    gate_ok, gate_msg = avaliar_gate_postgresql(engine.dialect.name)
    if not gate_ok:
        print_kv("EXECUCAO", "BLOQUEADA")
        print_kv("MOTIVO", gate_msg)
        return 2

    if args.apply:
        resultado = executar_em_transacao(engine, lambda conn: run_apply(conn, args.usuario))
    else:
        with engine.connect() as conn:
            resultado = run_check(conn, args.usuario)

    print_kv("OK", "SIM" if resultado.ok else "NAO")
    print_kv("ESTADO", resultado.estado)
    print_kv("PROBLEMAS", len(resultado.problemas))
    for p in resultado.problemas:
        print(f"- {p}")
    for chave, valor in resultado.metricas.items():
        print_kv(chave, valor)

    return 0 if resultado.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
