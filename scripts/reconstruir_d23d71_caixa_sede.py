#!/usr/bin/env python3
"""
D23D71 - Reconstrução read-only do caixa histórico da Sede até 31/08/2026.

Esta etapa NÃO altera produção.

Princípio:
- obrigação não é caixa;
- pagamento real é caixa;
- lançamento automático legado de obrigação deve ser neutralizado;
- PIX já importado no extrato permanece como fato financeiro real;
- pagamento histórico sem data exata não recebe data inventada.

Saída principal:
- saldo atual do ERP até 31/08/2026;
- total de saídas automáticas legadas ainda impactando;
- pagamentos reais em dinheiro que não possuem lançamento financeiro;
- PIX reais já representados no caixa;
- saldo reconstruído até 31/08/2026;
- pendências que impedem um apply automático seguro.
"""

from __future__ import annotations

import argparse
import json
import os
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import create_engine, text


TARGET_DATE = "2026-08-31"

EXPECTED_CURRENT_BALANCE = Decimal("-419.68")
EXPECTED_LEGACY_TOTAL = Decimal("8718.15")
EXPECTED_UNPOSTED_CASH_TOTAL = Decimal("6416.41")
EXPECTED_RECONSTRUCTED_BALANCE = Decimal("1882.06")

# Pagamentos em dinheiro já reconhecidos como quitação histórica, mas que não
# possuem lançamento financeiro real no caixa. As datas exatas não serão
# inventadas pela D23D71.
UNPOSTED_CASH_PAYMENTS = [
    {
        "code": "JAN_2026_DINHEIRO",
        "competencia": "01/2026",
        "valor": Decimal("1520.95"),
        "envio_ids": [15, 22],
        "data_exata_confirmada": False,
    },
    {
        "code": "FEV_2026_DINHEIRO",
        "competencia": "02/2026",
        "valor": Decimal("1641.01"),
        "envio_ids": [16],
        "data_exata_confirmada": False,
    },
    {
        "code": "MAR_2026_DINHEIRO",
        "competencia": "03/2026",
        "valor": Decimal("2109.11"),
        "envio_ids": [17],
        "data_exata_confirmada": False,
    },
    {
        "code": "ABR_2026_DINHEIRO",
        "competencia": "04/2026",
        "valor": Decimal("1145.34"),
        "envio_ids": [18, 24],
        "data_exata_confirmada": False,
    },
]

# PIX reais já existem nos lançamentos importados e, por isso, NÃO entram como
# novos ajustes de caixa na reconstrução.
CONFIRMED_BANK_PAYMENTS = {
    601: {
        "competencia": "04/2026",
        "valor": Decimal("1000.00"),
        "descricao": "Complemento de abril pago por PIX no acerto posterior.",
    },
    600: {
        "competencia": "05/2026",
        "valor": Decimal("1426.00"),
        "descricao": "Acerto de maio pago por PIX, sem incluir Projeto Filipe.",
    },
    615: {
        "competencia": "06/2026",
        "valor": Decimal("2573.31"),
        "descricao": "Pagamento real de junho registrado em 28/08/2026.",
    },
    616: {
        "competencia": "07/2026",
        "valor": Decimal("1292.56"),
        "descricao": "Pagamento real de julho registrado em 28/08/2026.",
    },
    664: {
        "competencia": "Projeto Filipe 05/2026 a 07/2026",
        "valor": Decimal("30.00"),
        "descricao": "Pagamento acumulado do Projeto Filipe em 28/08/2026.",
    },
}

MAY_DUE_WITHOUT_PROJETO_FILIPE = Decimal("1415.59")
MAY_REAL_PIX = Decimal("1426.00")
MAY_UNALLOCATED_CREDIT = Decimal("10.41")


def d2(value: Any) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money(value: Any) -> str:
    return f"{d2(value):.2f}"


def normalize_database_url(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def is_readonly_sql(sql: str) -> bool:
    normalized = " ".join((sql or "").strip().lower().split())
    return normalized.startswith("select ") or normalized.startswith("with ")


SQL_CURRENT_BALANCE = """
WITH econ AS (
    SELECT data, valor,
           CASE
             WHEN lower(coalesce(origem,''))='importado'
                  AND conciliado IS TRUE
                  AND par_conciliacao_id IS NOT NULL
               THEN 'Evidência'
             ELSE tipo
           END AS tipo_economico
    FROM lancamentos
)
SELECT COALESCE(SUM(
    CASE
      WHEN tipo_economico='Entrada' THEN valor
      WHEN tipo_economico='Saída' THEN -valor
      ELSE 0
    END
),0) AS saldo
FROM econ
WHERE data <= CAST(:data_limite AS DATE)
"""

SQL_LEGACY_TARGETS = """
SELECT id,data,tipo,categoria,descricao,valor,conta,origem,observacoes
FROM lancamentos
WHERE origem='automatico'
  AND lower(tipo) IN ('saída','saida')
  AND data <= CAST(:data_limite AS DATE)
  AND (
      (categoria='CONTRIB. SEDE' AND descricao ILIKE '30% Administrativo - Conselho Sede %')
      OR
      (categoria='DESP. FIXAS' AND descricao ILIKE '% - Despesa Fixa %')
  )
ORDER BY data,id
"""

SQL_ENVIOS = """
SELECT id,data_pagamento,competencia,competencia_mes_ref,competencia_ano_ref,
       valor_administrativo,valor_despesas_fixas,valor_total,
       forma_pagamento,tipo_pagamento,pagamento_historico_sem_movimentacao,
       data_pagamento_informada,lancamento_financeiro_id,observacao
FROM envios_sede
WHERE id IN (15,16,17,18,22,24,25,26,27,28)
ORDER BY id
"""

SQL_BANK_ROWS = """
SELECT id,data,tipo,categoria,descricao,valor,conta,origem,
       conciliado,par_conciliacao_id,observacoes
FROM lancamentos
WHERE id IN (600,601,615,616,664)
ORDER BY id
"""

SQL_MONTHLY_CURRENT = """
WITH econ AS (
    SELECT data, valor,
           CASE
             WHEN lower(coalesce(origem,''))='importado'
                  AND conciliado IS TRUE
                  AND par_conciliacao_id IS NOT NULL
               THEN 'Evidência'
             ELSE tipo
           END AS tipo_economico
    FROM lancamentos
)
SELECT EXTRACT(MONTH FROM data)::int AS mes,
       SUM(CASE WHEN tipo_economico='Entrada' THEN valor ELSE 0 END) AS entradas,
       SUM(CASE WHEN tipo_economico='Saída' THEN valor ELSE 0 END) AS saidas,
       SUM(CASE WHEN tipo_economico='Entrada' THEN valor
                WHEN tipo_economico='Saída' THEN -valor
                ELSE 0 END) AS saldo_mes
FROM econ
WHERE data BETWEEN DATE '2026-01-01' AND DATE '2026-08-31'
GROUP BY 1
ORDER BY 1
"""

READ_ONLY_SQL = (
    SQL_CURRENT_BALANCE,
    SQL_LEGACY_TARGETS,
    SQL_ENVIOS,
    SQL_BANK_ROWS,
    SQL_MONTHLY_CURRENT,
)


def rows(conn, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute(text(sql), params or {}).mappings().all()]


def scalar(conn, sql: str, params: dict[str, Any] | None = None) -> Decimal:
    return d2(conn.execute(text(sql), params or {}).scalar())


def validate_snapshot(
    current_balance: Decimal,
    legacy_rows: list[dict[str, Any]],
    envios: list[dict[str, Any]],
    bank_rows: list[dict[str, Any]],
) -> list[str]:
    problems: list[str] = []

    legacy_total = d2(sum((d2(r["valor"]) for r in legacy_rows), Decimal("0.00")))
    if legacy_total != EXPECTED_LEGACY_TOTAL:
        problems.append(
            f"legado automatico mudou: atual={money(legacy_total)} esperado={money(EXPECTED_LEGACY_TOTAL)}"
        )

    if current_balance != EXPECTED_CURRENT_BALANCE:
        problems.append(
            f"saldo atual mudou: atual={money(current_balance)} esperado={money(EXPECTED_CURRENT_BALANCE)}"
        )

    envio_by_id = {int(r["id"]): r for r in envios}
    for item in UNPOSTED_CASH_PAYMENTS:
        total = d2(sum(
            (d2(envio_by_id[eid]["valor_total"]) for eid in item["envio_ids"] if eid in envio_by_id),
            Decimal("0.00"),
        ))
        if total != item["valor"]:
            problems.append(
                f"{item['code']} divergiu: envios={money(total)} esperado={money(item['valor'])}"
            )

    bank_by_id = {int(r["id"]): r for r in bank_rows}
    for lid, expected in CONFIRMED_BANK_PAYMENTS.items():
        row = bank_by_id.get(lid)
        if not row:
            problems.append(f"lancamento bancario confirmado ausente: {lid}")
            continue
        if d2(row["valor"]) != expected["valor"]:
            problems.append(
                f"lancamento {lid} mudou: atual={money(row['valor'])} esperado={money(expected['valor'])}"
            )

    cash_total = d2(sum((x["valor"] for x in UNPOSTED_CASH_PAYMENTS), Decimal("0.00")))
    if cash_total != EXPECTED_UNPOSTED_CASH_TOTAL:
        problems.append(
            f"total de dinheiro sem lancamento divergiu: {money(cash_total)}"
        )

    if d2(MAY_REAL_PIX - MAY_DUE_WITHOUT_PROJETO_FILIPE) != MAY_UNALLOCATED_CREDIT:
        problems.append("credito/ajuste de maio nao fecha em R$ 10,41")

    return problems


def build_result(conn) -> dict[str, Any]:
    if not all(is_readonly_sql(sql) for sql in READ_ONLY_SQL):
        raise RuntimeError("D23D71 bloqueada: SQL de escrita detectado.")

    current_balance = scalar(
        conn,
        SQL_CURRENT_BALANCE,
        {"data_limite": TARGET_DATE},
    )
    legacy_rows = rows(
        conn,
        SQL_LEGACY_TARGETS,
        {"data_limite": TARGET_DATE},
    )
    envios = rows(conn, SQL_ENVIOS)
    bank_rows = rows(conn, SQL_BANK_ROWS)
    monthly = rows(conn, SQL_MONTHLY_CURRENT)

    problems = validate_snapshot(current_balance, legacy_rows, envios, bank_rows)

    legacy_total = d2(sum((d2(r["valor"]) for r in legacy_rows), Decimal("0.00")))
    cash_total = d2(sum((x["valor"] for x in UNPOSTED_CASH_PAYMENTS), Decimal("0.00")))
    reconstructed = d2(current_balance + legacy_total - cash_total)

    if reconstructed != EXPECTED_RECONSTRUCTED_BALANCE:
        problems.append(
            f"saldo reconstruido mudou: atual={money(reconstructed)} esperado={money(EXPECTED_RECONSTRUCTED_BALANCE)}"
        )

    monthly_out = []
    for r in monthly:
        month = int(r["mes"])
        monthly_out.append({
            "competencia": f"{month:02d}/2026",
            "entradas_erp": money(r["entradas"]),
            "saidas_erp": money(r["saidas"]),
            "resultado_erp": money(r["saldo_mes"]),
            "status_reconstrucao": (
                "DATA_EXATA_DE_CAIXA_PENDENTE"
                if month in {1,2,3,4}
                else "SEM_PENDENCIA_DE_DATA_NESTA_ETAPA"
            ),
        })

    return {
        "d23d71": "RECONSTRUCAO_CAIXA_SEDE_ATE_31_08_2026",
        "modo": "READ_ONLY",
        "banco_alterado": False,
        "snapshot_valido": len(problems) == 0,
        "problemas": problems,
        "saldo_atual_erp_31_08": money(current_balance),
        "legado_automatico_a_neutralizar": {
            "quantidade": len(legacy_rows),
            "total": money(legacy_total),
            "ids": [int(r["id"]) for r in legacy_rows],
        },
        "pagamentos_reais_em_dinheiro_sem_lancamento": {
            "total": money(cash_total),
            "itens": [
                {
                    "codigo": x["code"],
                    "competencia": x["competencia"],
                    "valor": money(x["valor"]),
                    "envio_ids": x["envio_ids"],
                    "data_exata_confirmada": x["data_exata_confirmada"],
                }
                for x in UNPOSTED_CASH_PAYMENTS
            ],
        },
        "pix_e_pagamentos_reais_ja_representados_no_caixa": {
            str(k): {
                "competencia": v["competencia"],
                "valor": money(v["valor"]),
                "descricao": v["descricao"],
            }
            for k, v in CONFIRMED_BANK_PAYMENTS.items()
        },
        "maio_2026": {
            "pix_real": money(MAY_REAL_PIX),
            "devido_sem_projeto_filipe": money(MAY_DUE_WITHOUT_PROJETO_FILIPE),
            "projeto_filipe_incluido_no_pix": False,
            "credito_ajuste_nao_alocado": money(MAY_UNALLOCATED_CREDIT),
        },
        "saldo_reconstruido_31_08": money(reconstructed),
        "formula_saldo_reconstruido": (
            f"{money(current_balance)} + {money(legacy_total)} - {money(cash_total)} = {money(reconstructed)}"
        ),
        "movimento_mensal_atual": monthly_out,
        "pendencias_antes_do_apply": [
            "Não inventar datas para os pagamentos em dinheiro de 01/2026, 02/2026, 03/2026 e a parcela em dinheiro de 04/2026.",
            "Vincular os PIX IDs 601 e 600 às competências 04/2026 e 05/2026 sem criar nova saída financeira.",
            "Manter Projeto Filipe de 05/2026 no pagamento acumulado de agosto.",
            "Tratar R$ 10,41 de maio como crédito/ajuste não alocado, sem forçar em obrigação.",
            "Neutralizar apenas os lançamentos automáticos legados listados, preservando-os como evidência/auditoria.",
        ],
        "apto_para_apply_automatico": False,
        "motivo_bloqueio_apply": (
            "O saldo final até 31/08 pode ser reconstruído sem inventar caixa, "
            "mas as datas exatas de quatro pagamentos em dinheiro não estão confirmadas."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", default=True)
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    args = parser.parse_args()

    url = normalize_database_url(args.database_url)
    if not url:
        print("D23D71: BLOQUEADA - DATABASE_URL ausente")
        return 2

    engine = create_engine(url)
    with engine.connect() as conn:
        result = build_result(conn)

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    print(
        "D23D71: OK_READ_ONLY"
        if result["snapshot_valido"]
        else "D23D71: SNAPSHOT_DIVERGENTE"
    )
    return 0 if result["snapshot_valido"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
