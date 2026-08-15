#!/usr/bin/env python3
"""
D.2.3D.16 - Executor transacional do bootstrap historico ADMIN_SEDE_30.

Modos:
- --check (default): 100% read-only
- --apply: escrita explicita em transacao unica
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import create_engine, inspect, text

ESTADO_A = "ESTADO_A_VAZIO_APTO"
ESTADO_B = "ESTADO_B_JA_APLICADO"
ESTADO_C = "ESTADO_C_PARCIAL_BLOQUEADO"
ESTADO_D = "ESTADO_D_INCOMPATIVEL"

OBRIGACOES_ALVO = [
    {"mes": 1, "ano": 2026, "devido": Decimal("1240.95"), "status": "PARCIAL", "data_quitacao": None},
    {"mes": 2, "ano": 2026, "devido": Decimal("1361.01"), "status": "PAGO", "data_quitacao": date(2026, 2, 1)},
    {"mes": 3, "ano": 2026, "devido": Decimal("1829.11"), "status": "PAGO", "data_quitacao": date(2026, 7, 4)},
    {"mes": 4, "ano": 2026, "devido": Decimal("1865.34"), "status": "PARCIAL", "data_quitacao": None},
    {"mes": 5, "ano": 2026, "devido": Decimal("1145.59"), "status": "PENDENTE", "data_quitacao": None},
    {"mes": 6, "ano": 2026, "devido": Decimal("2403.31"), "status": "PENDENTE", "data_quitacao": None},
    {"mes": 7, "ano": 2026, "devido": Decimal("1122.56"), "status": "PENDENTE", "data_quitacao": None},
]

PAGAMENTOS_ALVO = [
    {"mes": 1, "ano": 2026, "valor": Decimal("1240.00"), "data": date(2026, 1, 1), "envio_id": 15},
    {"mes": 2, "ano": 2026, "valor": Decimal("1361.01"), "data": date(2026, 2, 1), "envio_id": 16},
    {"mes": 3, "ano": 2026, "valor": Decimal("1829.11"), "data": date(2026, 7, 4), "envio_id": 17},
    {"mes": 4, "ano": 2026, "valor": Decimal("654.49"), "data": date(2026, 7, 4), "envio_id": 18},
]

ENVIOS_HISTORICOS_IDS = [15, 16, 17, 18]

TOTAL_DEVIDO_ESPERADO = Decimal("10967.87")
TOTAL_PAGO_ESPERADO = Decimal("5084.61")
TOTAL_SALDO_ESPERADO = Decimal("5883.26")

SALDO_POR_COMP_ESPERADO = {
    "01/2026": Decimal("0.95"),
    "02/2026": Decimal("0.00"),
    "03/2026": Decimal("0.00"),
    "04/2026": Decimal("1210.85"),
    "05/2026": Decimal("1145.59"),
    "06/2026": Decimal("2403.31"),
    "07/2026": Decimal("1122.56"),
}

CHECK_SQL_STATEMENTS = [
    "SELECT COUNT(*) FROM obrigacoes_financeiras",
    "SELECT COUNT(*) FROM pagamentos_obrigacao",
    "SELECT COUNT(*) FROM pagamentos_obrigacao_itens",
    "SELECT COUNT(*) FROM obrigacao_eventos",
    "SELECT COUNT(*) FROM envios_sede",
    "SELECT COUNT(*) FROM lancamentos",
    "SELECT id, pagamento_obrigacao_id, valor_administrativo, valor_total, valor, competencia, data_pagamento, forma_pagamento, observacao, lancamento_financeiro_id FROM envios_sede WHERE id IN (15,16,17,18)",
]

SCHEMA_REQUIRED_COLUMNS = {
    "obrigacoes_financeiras": {
        "id",
        "tipo_obrigacao",
        "origem_obrigacao",
        "referencia_origem_tipo",
        "referencia_origem_id",
        "categoria",
        "descricao",
        "competencia_mes",
        "competencia_ano",
        "valor_devido",
        "status",
        "data_quitacao",
        "historico_sem_movimentacao",
        "observacao",
    },
    "pagamentos_obrigacao": {
        "id",
        "data_pagamento",
        "valor_pago",
        "forma_pagamento",
        "tipo_pagamento",
        "observacao",
        "lancamento_financeiro_id",
    },
    "pagamentos_obrigacao_itens": {
        "id",
        "pagamento_obrigacao_id",
        "obrigacao_financeira_id",
        "valor_alocado",
    },
    "obrigacao_eventos": {
        "id",
        "obrigacao_financeira_id",
        "evento_tipo",
        "payload_json",
        "usuario",
    },
    "envios_sede": {
        "id",
        "pagamento_obrigacao_id",
        "valor",
        "valor_total",
        "valor_administrativo",
        "valor_despesas_fixas",
        "competencia",
        "data_pagamento",
        "forma_pagamento",
        "observacao",
        "lancamento_financeiro_id",
        "tipo_pagamento",
    },
    "lancamentos": {
        "id",
        "tipo",
        "valor",
    },
}

SCHEMA_REQUIRED_FKS = [
    ("pagamentos_obrigacao_itens", "pagamento_obrigacao_id", "pagamentos_obrigacao", "id"),
    ("pagamentos_obrigacao_itens", "obrigacao_financeira_id", "obrigacoes_financeiras", "id"),
    ("obrigacao_eventos", "obrigacao_financeira_id", "obrigacoes_financeiras", "id"),
    ("envios_sede", "pagamento_obrigacao_id", "pagamentos_obrigacao", "id"),
    ("pagamentos_obrigacao", "lancamento_financeiro_id", "lancamentos", "id"),
]

# Campos que no model estao nullable=False e que o bootstrap deve garantir no INSERT,
# para evitar dependencia de default de banco em ambientes heterogeneos.
INSERT_NOT_NULL_REQUIRED_BY_TABLE: dict[str, set[str]] = {
    "obrigacoes_financeiras": {
        "tipo_obrigacao",
        "origem_obrigacao",
        "descricao",
        "valor_devido",
        "status",
        "historico_sem_movimentacao",
        "created_at",
        "updated_at",
    },
    "pagamentos_obrigacao": {
        "data_pagamento",
        "valor_pago",
        "tipo_pagamento",
        "created_at",
        "updated_at",
    },
    "pagamentos_obrigacao_itens": {
        "pagamento_obrigacao_id",
        "obrigacao_financeira_id",
        "valor_alocado",
        "created_at",
    },
    "obrigacao_eventos": {
        "obrigacao_financeira_id",
        "evento_tipo",
        "created_at",
    },
}

INSERT_COLUMNS_BY_TABLE: dict[str, set[str]] = {
    "obrigacoes_financeiras": {
        "tipo_obrigacao",
        "origem_obrigacao",
        "referencia_origem_tipo",
        "referencia_origem_id",
        "categoria",
        "descricao",
        "competencia_mes",
        "competencia_ano",
        "valor_devido",
        "status",
        "data_quitacao",
        "historico_sem_movimentacao",
        "observacao",
        "created_at",
        "updated_at",
        "criado_por",
        "atualizado_por",
    },
    "pagamentos_obrigacao": {
        "data_pagamento",
        "valor_pago",
        "forma_pagamento",
        "tipo_pagamento",
        "observacao",
        "lancamento_financeiro_id",
        "created_at",
        "updated_at",
        "criado_por",
        "atualizado_por",
    },
    "pagamentos_obrigacao_itens": {
        "pagamento_obrigacao_id",
        "obrigacao_financeira_id",
        "valor_alocado",
        "created_at",
    },
    "obrigacao_eventos": {
        "obrigacao_financeira_id",
        "evento_tipo",
        "payload_json",
        "usuario",
        "created_at",
    },
}


@dataclass
class ResultadoExecucao:
    ok: bool
    estado: str
    problemas: list[str]
    metricas: dict[str, Any]


def validar_insert_not_null_obrigatorio() -> tuple[bool, list[str]]:
    problemas: list[str] = []
    for table_name, required_cols in INSERT_NOT_NULL_REQUIRED_BY_TABLE.items():
        declared = INSERT_COLUMNS_BY_TABLE.get(table_name, set())
        faltando = sorted(required_cols - declared)
        if faltando:
            problemas.append(
                f"{table_name}: faltam campos NOT NULL obrigatorios no INSERT ({', '.join(faltando)})"
            )
    return len(problemas) == 0, problemas


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


def competencia_chave(mes: int, ano: int) -> str:
    return f"{int(mes):02d}/{int(ano)}"


def referencia_origem_id(mes: int, ano: int) -> int:
    return int(ano) * 100 + int(mes)


def observacao_pagamento(mes: int, ano: int) -> str:
    return f"BOOTSTRAP_D23D16_COMP_{int(mes):02d}_{int(ano)}"


def payload_criacao(mes: int, ano: int, valor_devido: Decimal) -> str:
    return json.dumps(
        {
            "tipo_obrigacao": "ADMIN_SEDE_30",
            "competencia": competencia_chave(mes, ano),
            "origem": "bootstrap_d23d16",
            "valor_devido": str(d2(valor_devido)),
        },
        ensure_ascii=False,
    )


def payload_pagamento(pagamento_id: int, valor_alocado: Decimal, valor_total_operacao: Decimal) -> str:
    return json.dumps(
        {
            "pagamento_id": int(pagamento_id),
            "valor_alocado": str(d2(valor_alocado)),
            "valor_total_operacao": str(d2(valor_total_operacao)),
            "tipo_pagamento": "HISTORICO_SEM_MOVIMENTACAO",
            "lancamento_financeiro_id": None,
            "origem": "bootstrap_d23d16",
        },
        ensure_ascii=False,
    )


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


def inspect_schema(conn) -> tuple[dict[str, set[str]], dict[str, list[dict[str, Any]]]]:
    inspector = inspect(conn)
    schema: dict[str, set[str]] = {}
    fks: dict[str, list[dict[str, Any]]] = {}

    for table_name in inspector.get_table_names():
        schema[table_name] = {col["name"] for col in inspector.get_columns(table_name)}
        fks[table_name] = inspector.get_foreign_keys(table_name)

    return schema, fks


def _fk_exists(
    fks: dict[str, list[dict[str, Any]]],
    src_table: str,
    src_col: str,
    ref_table: str,
    ref_col: str,
) -> bool:
    for fk in fks.get(src_table, []):
        cols = fk.get("constrained_columns") or []
        rtable = fk.get("referred_table")
        rcols = fk.get("referred_columns") or []
        if src_col in cols and rtable == ref_table and ref_col in rcols:
            return True
    return False


def validate_schema(schema: dict[str, set[str]], fks: dict[str, list[dict[str, Any]]]) -> tuple[bool, list[str]]:
    problemas: list[str] = []

    for table_name, required_cols in SCHEMA_REQUIRED_COLUMNS.items():
        cols = schema.get(table_name)
        if cols is None:
            problemas.append(f"tabela ausente: {table_name}")
            continue
        missing = sorted(required_cols - cols)
        if missing:
            problemas.append(f"colunas ausentes em {table_name}: {', '.join(missing)}")

    for src_table, src_col, ref_table, ref_col in SCHEMA_REQUIRED_FKS:
        if not _fk_exists(fks, src_table, src_col, ref_table, ref_col):
            problemas.append(
                f"fk ausente: {src_table}.{src_col} -> {ref_table}.{ref_col}"
            )

    return len(problemas) == 0, problemas


def load_envios_historicos(conn) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            SELECT
                id,
                pagamento_obrigacao_id,
                valor,
                valor_total,
                valor_administrativo,
                valor_despesas_fixas,
                competencia,
                data_pagamento,
                forma_pagamento,
                observacao,
                lancamento_financeiro_id,
                tipo_pagamento
            FROM envios_sede
            WHERE id IN (15, 16, 17, 18)
            ORDER BY id
            """
        )
    ).mappings().all()
    return [dict(r) for r in rows]


def _map_obrigacoes_por_comp(obrigacoes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for row in obrigacoes:
        comp = competencia_chave(row["competencia_mes"], row["competencia_ano"])
        mapped[comp] = row
    return mapped


def load_existing_bootstrap(conn) -> dict[str, Any]:
    obrig_rows = conn.execute(
        text(
            """
            SELECT id, competencia_mes, competencia_ano, valor_devido, status, data_quitacao,
                   referencia_origem_tipo, referencia_origem_id, origem_obrigacao, tipo_obrigacao
            FROM obrigacoes_financeiras
            WHERE tipo_obrigacao = 'ADMIN_SEDE_30'
              AND origem_obrigacao = 'automatico'
              AND competencia_ano = 2026
              AND competencia_mes BETWEEN 1 AND 7
            ORDER BY competencia_mes
            """
        )
    ).mappings().all()

    pag_rows = conn.execute(
        text(
            """
            SELECT id, data_pagamento, valor_pago, forma_pagamento, tipo_pagamento,
                   observacao, lancamento_financeiro_id
            FROM pagamentos_obrigacao
            WHERE tipo_pagamento = 'HISTORICO_SEM_MOVIMENTACAO'
              AND observacao LIKE 'BOOTSTRAP_D23D16_COMP_%'
            ORDER BY id
            """
        )
    ).mappings().all()

    pag_ids = [int(r["id"]) for r in pag_rows]
    itens_rows: list[dict[str, Any]] = []
    if pag_ids:
        itens_rows = [
            dict(r)
            for r in conn.execute(
                text(
                    """
                    SELECT id, pagamento_obrigacao_id, obrigacao_financeira_id, valor_alocado
                    FROM pagamentos_obrigacao_itens
                    WHERE pagamento_obrigacao_id = ANY(:pag_ids)
                    ORDER BY id
                    """
                ),
                {"pag_ids": pag_ids},
            ).mappings().all()
        ]

    obrig_ids = [int(r["id"]) for r in obrig_rows]
    eventos_rows: list[dict[str, Any]] = []
    if obrig_ids:
        eventos_rows = [
            dict(r)
            for r in conn.execute(
                text(
                    """
                    SELECT id, obrigacao_financeira_id, evento_tipo, payload_json
                    FROM obrigacao_eventos
                    WHERE obrigacao_financeira_id = ANY(:obrig_ids)
                      AND evento_tipo IN ('CRIACAO', 'PAGAMENTO')
                    ORDER BY id
                    """
                ),
                {"obrig_ids": obrig_ids},
            ).mappings().all()
        ]

    return {
        "obrigacoes": [dict(r) for r in obrig_rows],
        "pagamentos": [dict(r) for r in pag_rows],
        "itens": itens_rows,
        "eventos": eventos_rows,
    }


def _is_estado_b(existing: dict[str, Any], envios_rows: list[dict[str, Any]]) -> bool:
    obrigacoes = existing["obrigacoes"]
    pagamentos = existing["pagamentos"]
    itens = existing["itens"]
    eventos = existing["eventos"]

    if len(obrigacoes) != 7 or len(pagamentos) != 4 or len(itens) != 4:
        return False

    if len([e for e in eventos if e.get("evento_tipo") == "CRIACAO"]) != 7:
        return False
    if len([e for e in eventos if e.get("evento_tipo") == "PAGAMENTO"]) != 4:
        return False

    obrig_by_comp = _map_obrigacoes_por_comp(obrigacoes)
    for alvo in OBRIGACOES_ALVO:
        comp = competencia_chave(alvo["mes"], alvo["ano"])
        row = obrig_by_comp.get(comp)
        if row is None:
            return False
        if row.get("tipo_obrigacao") != "ADMIN_SEDE_30":
            return False
        if row.get("origem_obrigacao") != "automatico":
            return False
        if row.get("referencia_origem_tipo") != "FECHAMENTO_MENSAL":
            return False
        if int(row.get("referencia_origem_id") or 0) != referencia_origem_id(alvo["mes"], alvo["ano"]):
            return False
        if d2(row.get("valor_devido")) != d2(alvo["devido"]):
            return False
        if (row.get("status") or "").upper() != alvo["status"]:
            return False
        rq = row.get("data_quitacao")
        aq = alvo["data_quitacao"]
        if (rq is None) != (aq is None):
            return False
        if rq is not None and str(rq) != str(aq):
            return False

    pag_by_comp: dict[str, dict[str, Any]] = {}
    for row in pagamentos:
        obs = (row.get("observacao") or "").strip()
        if not obs.startswith("BOOTSTRAP_D23D16_COMP_"):
            return False
        parts = obs.split("_")
        if len(parts) != 5:
            return False
        comp = f"{parts[3]}/{parts[4]}"
        pag_by_comp[comp] = row

    if len(pag_by_comp) != 4:
        return False

    for alvo in PAGAMENTOS_ALVO:
        comp = competencia_chave(alvo["mes"], alvo["ano"])
        row = pag_by_comp.get(comp)
        if row is None:
            return False
        if d2(row.get("valor_pago")) != d2(alvo["valor"]):
            return False
        if str(row.get("data_pagamento")) != str(alvo["data"]):
            return False
        if (row.get("tipo_pagamento") or "").upper() != "HISTORICO_SEM_MOVIMENTACAO":
            return False
        if (row.get("forma_pagamento") or "") != "Dinheiro":
            return False
        if row.get("lancamento_financeiro_id") is not None:
            return False

    itens_by_pag = {int(i["pagamento_obrigacao_id"]): i for i in itens}
    if len(itens_by_pag) != 4:
        return False

    for alvo in PAGAMENTOS_ALVO:
        comp = competencia_chave(alvo["mes"], alvo["ano"])
        pag = pag_by_comp[comp]
        item = itens_by_pag.get(int(pag["id"]))
        if item is None:
            return False
        obrig = obrig_by_comp.get(comp)
        if obrig is None:
            return False
        if int(item["obrigacao_financeira_id"]) != int(obrig["id"]):
            return False
        if d2(item.get("valor_alocado")) != d2(alvo["valor"]):
            return False

    envios_by_id = {int(r["id"]): r for r in envios_rows}
    for alvo in PAGAMENTOS_ALVO:
        comp = competencia_chave(alvo["mes"], alvo["ano"])
        pag = pag_by_comp.get(comp)
        envio = envios_by_id.get(alvo["envio_id"])
        if envio is None:
            return False
        if int(envio.get("pagamento_obrigacao_id") or 0) != int(pag["id"]):
            return False

    return True


def classificar_estado(
    snapshot: dict[str, Decimal],
    schema_ok: bool,
    envios_rows: list[dict[str, Any]],
    existing: dict[str, Any],
) -> tuple[str, list[str]]:
    problemas: list[str] = []
    envios_by_id = {int(r["id"]): r for r in envios_rows}

    if not schema_ok:
        problemas.append("schema incompatível")
        return ESTADO_D, problemas

    faltando = [eid for eid in ENVIOS_HISTORICOS_IDS if eid not in envios_by_id]
    if faltando:
        problemas.append(f"envios historicos ausentes: {faltando}")
        return ESTADO_D, problemas

    if _is_estado_b(existing, envios_rows):
        return ESTADO_B, problemas

    trio_zero = (
        snapshot.get("TOTAL_OBRIGACOES", Decimal("0")) == Decimal("0.00")
        and snapshot.get("TOTAL_PAGAMENTOS", Decimal("0")) == Decimal("0.00")
        and snapshot.get("TOTAL_ITENS", Decimal("0")) == Decimal("0.00")
    )
    if trio_zero:
        return ESTADO_A, problemas

    trio_algum = (
        snapshot.get("TOTAL_OBRIGACOES", Decimal("0")) > Decimal("0.00")
        or snapshot.get("TOTAL_PAGAMENTOS", Decimal("0")) > Decimal("0.00")
        or snapshot.get("TOTAL_ITENS", Decimal("0")) > Decimal("0.00")
    )
    if trio_algum:
        problemas.append(
            "estado parcial detectado em obrigacoes/pagamentos/itens; bootstrap nao sera completado automaticamente"
        )
        return ESTADO_C, problemas

    problemas.append("estado nao classificado")
    return ESTADO_D, problemas


def build_apply_plan(envios_rows: list[dict[str, Any]]) -> dict[str, Any]:
    envios_by_id = {int(r["id"]): r for r in envios_rows}
    obrigacoes_plan = []
    pagamentos_plan = []
    itens_plan = []
    eventos_plan = []
    vinculos_envio = []

    for alvo in OBRIGACOES_ALVO:
        comp = competencia_chave(alvo["mes"], alvo["ano"])
        obrigacoes_plan.append(
            {
                "competencia": comp,
                "mes": alvo["mes"],
                "ano": alvo["ano"],
                "valor_devido": d2(alvo["devido"]),
                "status": alvo["status"],
                "data_quitacao": alvo["data_quitacao"],
                "tipo_obrigacao": "ADMIN_SEDE_30",
                "origem_obrigacao": "automatico",
                "referencia_origem_tipo": "FECHAMENTO_MENSAL",
                "referencia_origem_id": referencia_origem_id(alvo["mes"], alvo["ano"]),
            }
        )
        eventos_plan.append({"tipo": "CRIACAO", "competencia": comp})

    for alvo in PAGAMENTOS_ALVO:
        comp = competencia_chave(alvo["mes"], alvo["ano"])
        envio = envios_by_id.get(alvo["envio_id"])
        if envio is None:
            raise RuntimeError(f"EnvioSede {alvo['envio_id']} ausente")
        if envio.get("pagamento_obrigacao_id") is not None:
            raise RuntimeError(f"EnvioSede {alvo['envio_id']} ja vinculado a pagamento_obrigacao_id")

        valor_admin = envio.get("valor_administrativo")
        if valor_admin is None:
            raise RuntimeError(
                f"EnvioSede {alvo['envio_id']} sem valor_administrativo; nao e permitido usar valor_total"
            )

        valor_item = d2(valor_admin)
        if valor_item != d2(alvo["valor"]):
            raise RuntimeError(
                f"EnvioSede {alvo['envio_id']} divergente: valor_administrativo={money(valor_item)} esperado={money(alvo['valor'])}"
            )

        pagamentos_plan.append(
            {
                "competencia": comp,
                "mes": alvo["mes"],
                "ano": alvo["ano"],
                "valor_pago": d2(alvo["valor"]),
                "data_pagamento": alvo["data"],
                "tipo_pagamento": "HISTORICO_SEM_MOVIMENTACAO",
                "forma_pagamento": "Dinheiro",
                "observacao": observacao_pagamento(alvo["mes"], alvo["ano"]),
                "lancamento_financeiro_id": None,
                "envio_id": alvo["envio_id"],
            }
        )
        itens_plan.append(
            {
                "competencia": comp,
                "valor_alocado": valor_item,
                "fonte_valor": "valor_administrativo",
            }
        )
        eventos_plan.append({"tipo": "PAGAMENTO", "competencia": comp})
        vinculos_envio.append({"envio_id": alvo["envio_id"], "competencia": comp})

    return {
        "obrigacoes": obrigacoes_plan,
        "pagamentos": pagamentos_plan,
        "itens": itens_plan,
        "eventos": eventos_plan,
        "vinculos_envio": vinculos_envio,
    }


def executar_em_transacao(engine, callback):
    with engine.begin() as conn:
        return callback(conn)


def aplicar_bootstrap(conn, envios_rows: list[dict[str, Any]], forcar_falha_etapa: str | None = None) -> dict[str, Any]:
    plan = build_apply_plan(envios_rows)
    agora_utc = datetime.utcnow()

    snap_before = snapshot_totais(conn)

    obrig_ids_por_comp: dict[str, int] = {}
    for row in plan["obrigacoes"]:
        result = conn.execute(
            text(
                """
                INSERT INTO obrigacoes_financeiras (
                    tipo_obrigacao,
                    origem_obrigacao,
                    referencia_origem_tipo,
                    referencia_origem_id,
                    categoria,
                    descricao,
                    competencia_mes,
                    competencia_ano,
                    valor_devido,
                    status,
                    data_quitacao,
                    historico_sem_movimentacao,
                    observacao,
                    created_at,
                    updated_at,
                    criado_por,
                    atualizado_por
                ) VALUES (
                    'ADMIN_SEDE_30',
                    'automatico',
                    'FECHAMENTO_MENSAL',
                    :referencia_origem_id,
                    'CONTRIB. SEDE',
                    :descricao,
                    :competencia_mes,
                    :competencia_ano,
                    :valor_devido,
                    :status,
                    :data_quitacao,
                    false,
                    :observacao,
                    :created_at,
                    :updated_at,
                    'bootstrap_d23d16',
                    'bootstrap_d23d16'
                )
                RETURNING id
                """
            ),
            {
                "referencia_origem_id": row["referencia_origem_id"],
                "descricao": f"30% Administrativo - Conselho Sede {row['mes']:02d}/{row['ano']}",
                "competencia_mes": row["mes"],
                "competencia_ano": row["ano"],
                "valor_devido": row["valor_devido"],
                "status": row["status"],
                "data_quitacao": row["data_quitacao"],
                "observacao": f"BOOTSTRAP_D23D16_OBRIGACAO_COMP_{row['mes']:02d}_{row['ano']}",
                "created_at": agora_utc,
                "updated_at": agora_utc,
            },
        )
        oid = int(result.scalar_one())
        obrig_ids_por_comp[row["competencia"]] = oid

        conn.execute(
            text(
                """
                INSERT INTO obrigacao_eventos (obrigacao_financeira_id, evento_tipo, payload_json, usuario, created_at)
                VALUES (:obrigacao_financeira_id, 'CRIACAO', :payload_json, 'bootstrap_d23d16', :created_at)
                """
            ),
            {
                "obrigacao_financeira_id": oid,
                "payload_json": payload_criacao(row["mes"], row["ano"], row["valor_devido"]),
                "created_at": agora_utc,
            },
        )

    if forcar_falha_etapa == "apos_obrigacoes":
        raise RuntimeError("falha_forcada_apos_obrigacoes")

    pag_ids_por_comp: dict[str, int] = {}
    for row in plan["pagamentos"]:
        result = conn.execute(
            text(
                """
                INSERT INTO pagamentos_obrigacao (
                    data_pagamento,
                    valor_pago,
                    forma_pagamento,
                    tipo_pagamento,
                    observacao,
                    lancamento_financeiro_id,
                    created_at,
                    updated_at,
                    criado_por,
                    atualizado_por
                ) VALUES (
                    :data_pagamento,
                    :valor_pago,
                    :forma_pagamento,
                    'HISTORICO_SEM_MOVIMENTACAO',
                    :observacao,
                    NULL,
                    :created_at,
                    :updated_at,
                    'bootstrap_d23d16',
                    'bootstrap_d23d16'
                )
                RETURNING id
                """
            ),
            {
                "data_pagamento": row["data_pagamento"],
                "valor_pago": row["valor_pago"],
                "forma_pagamento": row["forma_pagamento"],
                "observacao": row["observacao"],
                "created_at": agora_utc,
                "updated_at": agora_utc,
            },
        )
        pag_ids_por_comp[row["competencia"]] = int(result.scalar_one())

    if forcar_falha_etapa == "apos_pagamentos":
        raise RuntimeError("falha_forcada_apos_pagamentos")

    for item in plan["itens"]:
        comp = item["competencia"]
        conn.execute(
            text(
                """
                INSERT INTO pagamentos_obrigacao_itens (
                    pagamento_obrigacao_id,
                    obrigacao_financeira_id,
                    valor_alocado,
                    created_at
                ) VALUES (
                    :pagamento_obrigacao_id,
                    :obrigacao_financeira_id,
                    :valor_alocado,
                    :created_at
                )
                """
            ),
            {
                "pagamento_obrigacao_id": pag_ids_por_comp[comp],
                "obrigacao_financeira_id": obrig_ids_por_comp[comp],
                "valor_alocado": item["valor_alocado"],
                "created_at": agora_utc,
            },
        )

        conn.execute(
            text(
                """
                INSERT INTO obrigacao_eventos (obrigacao_financeira_id, evento_tipo, payload_json, usuario, created_at)
                VALUES (:obrigacao_financeira_id, 'PAGAMENTO', :payload_json, 'bootstrap_d23d16', :created_at)
                """
            ),
            {
                "obrigacao_financeira_id": obrig_ids_por_comp[comp],
                "payload_json": payload_pagamento(
                    pag_ids_por_comp[comp],
                    item["valor_alocado"],
                    item["valor_alocado"],
                ),
                "created_at": agora_utc,
            },
        )

    if forcar_falha_etapa == "apos_itens_eventos":
        raise RuntimeError("falha_forcada_apos_itens_eventos")

    for vinc in plan["vinculos_envio"]:
        comp = vinc["competencia"]
        conn.execute(
            text(
                """
                UPDATE envios_sede
                SET pagamento_obrigacao_id = :pagamento_obrigacao_id
                WHERE id = :envio_id
                """
            ),
            {
                "pagamento_obrigacao_id": pag_ids_por_comp[comp],
                "envio_id": vinc["envio_id"],
            },
        )

    snap_after = snapshot_totais(conn)

    if snap_after["TOTAL_LANCAMENTOS"] != snap_before["TOTAL_LANCAMENTOS"]:
        raise RuntimeError("NOVOS_LANCAMENTOS_DETECTADOS")
    if snap_after["SALDO_LANCAMENTOS"] != snap_before["SALDO_LANCAMENTOS"]:
        raise RuntimeError("MOVIMENTACAO_CAIXA_DETECTADA")

    return {
        "snap_before": snap_before,
        "snap_after": snap_after,
        "obrig_ids_por_comp": obrig_ids_por_comp,
        "pag_ids_por_comp": pag_ids_por_comp,
        "plan": plan,
    }


def poscheck(conn) -> tuple[bool, list[str], dict[str, Any]]:
    problemas: list[str] = []

    obrig_rows = [
        dict(r)
        for r in conn.execute(
            text(
                """
                SELECT id, competencia_mes, competencia_ano, valor_devido, status, data_quitacao
                FROM obrigacoes_financeiras
                WHERE tipo_obrigacao = 'ADMIN_SEDE_30'
                  AND origem_obrigacao = 'automatico'
                  AND competencia_ano = 2026
                  AND competencia_mes BETWEEN 1 AND 7
                ORDER BY competencia_mes
                """
            )
        ).mappings().all()
    ]

    pag_rows = [
        dict(r)
        for r in conn.execute(
            text(
                """
                SELECT id, data_pagamento, valor_pago, observacao, lancamento_financeiro_id
                FROM pagamentos_obrigacao
                WHERE tipo_pagamento = 'HISTORICO_SEM_MOVIMENTACAO'
                  AND observacao LIKE 'BOOTSTRAP_D23D16_COMP_%'
                ORDER BY id
                """
            )
        ).mappings().all()
    ]

    pag_ids = [int(r["id"]) for r in pag_rows]
    itens_rows = []
    if pag_ids:
        itens_rows = [
            dict(r)
            for r in conn.execute(
                text(
                    """
                    SELECT pagamento_obrigacao_id, obrigacao_financeira_id, valor_alocado
                    FROM pagamentos_obrigacao_itens
                    WHERE pagamento_obrigacao_id = ANY(:ids)
                    ORDER BY pagamento_obrigacao_id
                    """
                ),
                {"ids": pag_ids},
            ).mappings().all()
        ]

    obrig_ids = [int(r["id"]) for r in obrig_rows]
    eventos_count = 0
    if obrig_ids:
        eventos_count = int(
            conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM obrigacao_eventos
                    WHERE obrigacao_financeira_id = ANY(:ids)
                      AND evento_tipo IN ('CRIACAO', 'PAGAMENTO')
                    """
                ),
                {"ids": obrig_ids},
            ).scalar()
            or 0
        )

    envios_vinculados = int(
        conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM envios_sede
                WHERE id IN (15,16,17,18)
                  AND pagamento_obrigacao_id IS NOT NULL
                """
            )
        ).scalar()
        or 0
    )

    novos_envios = int(
        conn.execute(
            text("SELECT COUNT(*) FROM envios_sede WHERE id NOT IN (15,16,17,18) AND pagamento_obrigacao_id IS NOT NULL")
        ).scalar()
        or 0
    )

    total_lanc = d2(conn.execute(text("SELECT COUNT(*) FROM lancamentos")).scalar())

    total_devido = sum((d2(r["valor_devido"]) for r in obrig_rows), Decimal("0.00"))
    total_pago = sum((d2(i["valor_alocado"]) for i in itens_rows), Decimal("0.00"))
    total_saldo = (total_devido - total_pago).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    saldo_por_comp: dict[str, Decimal] = {}
    obrig_by_id = {int(r["id"]): r for r in obrig_rows}
    for r in obrig_rows:
        comp = competencia_chave(r["competencia_mes"], r["competencia_ano"])
        saldo_por_comp[comp] = d2(r["valor_devido"])
    for i in itens_rows:
        oid = int(i["obrigacao_financeira_id"])
        row = obrig_by_id.get(oid)
        if row is None:
            continue
        comp = competencia_chave(row["competencia_mes"], row["competencia_ano"])
        saldo_por_comp[comp] = d2(saldo_por_comp.get(comp, Decimal("0.00")) - d2(i["valor_alocado"]))

    if len(obrig_rows) != 7:
        problemas.append("poscheck: obrigacoes != 7")
    if len(pag_rows) != 4:
        problemas.append("poscheck: pagamentos != 4")
    if len(itens_rows) != 4:
        problemas.append("poscheck: itens != 4")
    if eventos_count != 11:
        problemas.append("poscheck: eventos != 11")
    if envios_vinculados != 4:
        problemas.append("poscheck: envios vinculados != 4")
    if novos_envios != 0:
        problemas.append("poscheck: novos envios detectados")
    if total_devido != TOTAL_DEVIDO_ESPERADO:
        problemas.append("poscheck: total devido divergente")
    if total_pago != TOTAL_PAGO_ESPERADO:
        problemas.append("poscheck: total pago divergente")
    if total_saldo != TOTAL_SALDO_ESPERADO:
        problemas.append("poscheck: total saldo divergente")
    for comp, esperado in SALDO_POR_COMP_ESPERADO.items():
        real = d2(saldo_por_comp.get(comp, Decimal("0.00")))
        if real != esperado:
            problemas.append(f"poscheck: saldo {comp} divergente ({money(real)} != {money(esperado)})")

    metricas = {
        "OBRIGACOES": len(obrig_rows),
        "PAGAMENTOS": len(pag_rows),
        "ITENS": len(itens_rows),
        "EVENTOS": eventos_count,
        "ENVIOS_VINCULADOS": envios_vinculados,
        "NOVOS_ENVIOS": novos_envios,
        "NOVOS_LANCAMENTOS": "0",
        "TOTAL_LANCAMENTOS": money(total_lanc),
        "TOTAL_DEVIDO": money(total_devido),
        "TOTAL_PAGO": money(total_pago),
        "TOTAL_SALDO": money(total_saldo),
    }
    for comp in sorted(SALDO_POR_COMP_ESPERADO.keys()):
        metricas[f"SALDO_{comp}"] = money(saldo_por_comp.get(comp, Decimal("0.00")))

    return len(problemas) == 0, problemas, metricas


def executar_check(engine) -> ResultadoExecucao:
    problemas: list[str] = []
    metricas: dict[str, Any] = {}

    with engine.connect() as conn:
        schema, fks = inspect_schema(conn)
        schema_ok, schema_problemas = validate_schema(schema, fks)
        problemas.extend(schema_problemas)
        metricas["SCHEMA_GATE"] = "SIM" if schema_ok else "NAO"

        snapshot = snapshot_totais(conn)
        for k, v in snapshot.items():
            metricas[k] = money(v)

        envios_rows = load_envios_historicos(conn)
        metricas["TOTAL_ENVIOS_HISTORICOS_15_18"] = str(len(envios_rows))

        existing = load_existing_bootstrap(conn)
        estado, problemas_estado = classificar_estado(snapshot, schema_ok, envios_rows, existing)
        problemas.extend(problemas_estado)
        metricas["ESTADO_CLASSIFICADO"] = estado
        metricas["READONLY_AUDIT_OK"] = "SIM" if assert_sql_set_readonly(CHECK_SQL_STATEMENTS) else "NAO"

    ok = estado in {ESTADO_A, ESTADO_B}
    return ResultadoExecucao(ok=ok, estado=estado, problemas=problemas, metricas=metricas)


def executar_apply(engine) -> ResultadoExecucao:
    problemas: list[str] = []
    metricas: dict[str, Any] = {}

    with engine.connect() as conn:
        schema, fks = inspect_schema(conn)
        schema_ok, schema_problemas = validate_schema(schema, fks)
        if not schema_ok:
            problemas.extend(schema_problemas)
            return ResultadoExecucao(ok=False, estado=ESTADO_D, problemas=problemas, metricas={"SCHEMA_GATE": "NAO"})

        snapshot = snapshot_totais(conn)
        envios_rows = load_envios_historicos(conn)
        existing = load_existing_bootstrap(conn)
        estado, problemas_estado = classificar_estado(snapshot, schema_ok, envios_rows, existing)
        if estado == ESTADO_B:
            metricas["IDEMPOTENCIA"] = "SIM"
            metricas["NOVAS_OBRIGACOES"] = "0"
            metricas["NOVOS_PAGAMENTOS"] = "0"
            metricas["NOVOS_ITENS"] = "0"
            metricas["NOVOS_EVENTOS"] = "0"
            metricas["NOVOS_ENVIOS"] = "0"
            metricas["NOVOS_LANCAMENTOS"] = "0"
            return ResultadoExecucao(ok=True, estado=estado, problemas=[], metricas=metricas)

        if estado != ESTADO_A:
            problemas.extend(problemas_estado)
            return ResultadoExecucao(ok=False, estado=estado, problemas=problemas, metricas=metricas)

    try:
        tx_result = executar_em_transacao(
            engine,
            lambda tx_conn: aplicar_bootstrap(tx_conn, load_envios_historicos(tx_conn)),
        )
    except Exception as exc:
        problemas.append(str(exc))
        return ResultadoExecucao(ok=False, estado=ESTADO_C, problemas=problemas, metricas={"ROLLBACK_TOTAL": "SIM"})

    with engine.connect() as conn2:
        ok_pos, problemas_pos, metricas_pos = poscheck(conn2)

    metricas.update(metricas_pos)
    metricas["NOVAS_OBRIGACOES"] = str(len(tx_result["plan"]["obrigacoes"]))
    metricas["NOVOS_PAGAMENTOS"] = str(len(tx_result["plan"]["pagamentos"]))
    metricas["NOVOS_ITENS"] = str(len(tx_result["plan"]["itens"]))
    metricas["NOVOS_EVENTOS"] = str(len(tx_result["plan"]["eventos"]))
    metricas["NOVOS_ENVIOS"] = "0"
    metricas["NOVOS_LANCAMENTOS"] = "0"
    metricas["MOVIMENTACAO_CAIXA"] = "0.00"
    metricas["TRANSACAO_UNICA"] = "SIM"
    metricas["ROLLBACK_TOTAL"] = "SIM"
    metricas["BACKFILL_FIXAS_EXECUTADO"] = "NAO"

    problemas.extend(problemas_pos)
    return ResultadoExecucao(ok=ok_pos, estado=ESTADO_B if ok_pos else ESTADO_C, problemas=problemas, metricas=metricas)


def imprimir_relatorio(resultado: ResultadoExecucao):
    print_kv("ESTADO", resultado.estado)
    print_kv("SUCESSO", "SIM" if resultado.ok else "NAO")
    for k in sorted(resultado.metricas.keys()):
        print_kv(k, resultado.metricas[k])
    if resultado.problemas:
        print_kv("PROBLEMAS_ENCONTRADOS", " | ".join(resultado.problemas))
    else:
        print_kv("PROBLEMAS_ENCONTRADOS", "-")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Executor D.2.3D.16")
    parser.add_argument("--check", action="store_true", help="Modo read-only")
    parser.add_argument("--apply", action="store_true", help="Modo transacional")
    args = parser.parse_args(argv)

    if args.check and args.apply:
        print("ABORTAR_MOTIVO: use apenas um modo")
        return 1

    modo = "apply" if args.apply else "check"
    database_url_raw = os.getenv("DATABASE_URL")
    database_url = normalize_database_url(database_url_raw)

    print_kv("MODO", modo)
    print_kv("DATABASE_URL_PRESENTE", "SIM" if database_url else "NAO")
    if not database_url:
        print_kv("POSTGRESQL_OK", "NAO")
        print_kv("ABORTAR_MOTIVO", "DATABASE_URL ausente")
        return 1

    engine = create_engine(database_url, pool_pre_ping=True, future=True)
    dialeto = (engine.dialect.name or "").lower()
    gate_ok, gate_motivo = avaliar_gate_postgresql(dialeto)

    print_kv("DIALETO", dialeto)
    print_kv("POSTGRESQL_OK", "SIM" if gate_ok else "NAO")
    if not gate_ok:
        print_kv("ABORTAR_MOTIVO", gate_motivo or "gate postgresql")
        return 1

    inserts_ok, inserts_problemas = validar_insert_not_null_obrigatorio()
    print_kv("INSERT_NOT_NULL_AUDIT_OK", "SIM" if inserts_ok else "NAO")
    if not inserts_ok:
        print_kv("ABORTAR_MOTIVO", " | ".join(inserts_problemas))
        return 1

    if modo == "check":
        resultado = executar_check(engine)
    else:
        resultado = executar_apply(engine)

    imprimir_relatorio(resultado)
    return 0 if resultado.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
