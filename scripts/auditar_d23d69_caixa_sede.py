#!/usr/bin/env python3
"""
D23D69 - Auditoria read-only do caixa historico da Sede.

Objetivo:
- localizar lancamentos automaticos legados que representam obrigacao, nao caixa;
- comparar o caixa atual com uma simulacao que neutraliza essas obrigacoes;
- evidenciar pagamentos historicos sem lancamento financeiro;
- listar movimentos bancarios/importados ainda nao conciliados que podem representar
  pagamentos reais da Sede;
- BLOQUEAR qualquer escrita ate a reconciliacao documental estar resolvida.

Uso:
    python scripts/auditar_d23d69_caixa_sede.py --check
    python scripts/auditar_d23d69_caixa_sede.py --check --year 2026 --through-month 8

Nao existe modo de escrita neste script.
"""

from __future__ import annotations

import argparse
import json
import os
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import create_engine, text


def d2(v: Any) -> Decimal:
    return Decimal(str(v or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money(v: Any) -> str:
    return f"{d2(v):.2f}"


def normalize_database_url(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def is_readonly_sql(sql: str) -> bool:
    normalized = " ".join((sql or "").strip().lower().split())
    return normalized.startswith("select ") or normalized.startswith("with ")


SQL_LEGADOS = """
SELECT id,data,tipo,categoria,descricao,valor,conta,origem,observacoes
FROM lancamentos
WHERE origem='automatico'
  AND lower(tipo) IN ('saída','saida')
  AND (
    (categoria='CONTRIB. SEDE' AND descricao ILIKE '30% Administrativo - Conselho Sede %')
    OR
    (categoria='DESP. FIXAS' AND descricao ILIKE '% - Despesa Fixa %')
  )
ORDER BY data,id
"""

SQL_HISTORICOS = """
SELECT id,pagamento_obrigacao_id,data_pagamento,competencia,
       competencia_mes_ref,competencia_ano_ref,
       valor_administrativo,valor_despesas_fixas,valor_total,
       forma_pagamento,tipo_pagamento,pagamento_historico_sem_movimentacao,
       data_pagamento_informada,lancamento_financeiro_id,observacao
FROM envios_sede
WHERE tipo_pagamento='HISTORICO_SEM_MOVIMENTACAO'
ORDER BY data_pagamento,id
"""

SQL_CANDIDATOS_IMPORTADOS = """
SELECT id,data,tipo,categoria,descricao,valor,conta,origem,
       conciliado,par_conciliacao_id,observacoes
FROM lancamentos
WHERE origem='importado'
  AND lower(tipo) IN ('saída','saida')
  AND NOT (conciliado IS TRUE AND par_conciliacao_id IS NOT NULL)
  AND (
       lower(coalesce(descricao,'')) LIKE '%igreja evang pentecostal o brasil para cristo%'
       OR lower(coalesce(descricao,'')) LIKE '%conselho%'
       OR lower(coalesce(descricao,'')) LIKE '%obpc%'
       OR lower(coalesce(observacoes,'')) LIKE '%sede%'
  )
ORDER BY data,id
"""

SQL_MENSAL_ATUAL = """
WITH econ AS (
  SELECT data,valor,
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
WHERE EXTRACT(YEAR FROM data)=:ano
  AND EXTRACT(MONTH FROM data)<=:mes_limite
GROUP BY 1
ORDER BY 1
"""

SQL_MENSAL_SIMULADO = """
WITH econ AS (
  SELECT data,valor,origem,categoria,descricao,
         CASE
           WHEN lower(coalesce(origem,''))='importado'
                AND conciliado IS TRUE
                AND par_conciliacao_id IS NOT NULL
           THEN 'Evidência'
           ELSE tipo
         END AS tipo_economico
  FROM lancamentos
),
atual AS (
  SELECT data,
         CASE WHEN tipo_economico='Entrada' THEN valor
              WHEN tipo_economico='Saída' THEN -valor
              ELSE 0 END AS impacto
  FROM econ
),
neutraliza_legado AS (
  SELECT data,valor AS impacto
  FROM lancamentos
  WHERE origem='automatico'
    AND lower(tipo) IN ('saída','saida')
    AND (
      (categoria='CONTRIB. SEDE' AND descricao ILIKE '30% Administrativo - Conselho Sede %')
      OR
      (categoria='DESP. FIXAS' AND descricao ILIKE '% - Despesa Fixa %')
    )
),
pagamentos_historicos AS (
  SELECT data_pagamento AS data,-valor_total AS impacto
  FROM envios_sede
  WHERE tipo_pagamento='HISTORICO_SEM_MOVIMENTACAO'
),
simulado AS (
  SELECT data,impacto FROM atual
  UNION ALL
  SELECT data,impacto FROM neutraliza_legado
  UNION ALL
  SELECT data,impacto FROM pagamentos_historicos
)
SELECT EXTRACT(MONTH FROM data)::int AS mes,
       SUM(impacto) AS saldo_mes
FROM simulado
WHERE EXTRACT(YEAR FROM data)=:ano
  AND EXTRACT(MONTH FROM data)<=:mes_limite
GROUP BY 1
ORDER BY 1
"""

READ_ONLY_SQL = (
    SQL_LEGADOS,
    SQL_HISTORICOS,
    SQL_CANDIDATOS_IMPORTADOS,
    SQL_MENSAL_ATUAL,
    SQL_MENSAL_SIMULADO,
)

# Mapeamentos confirmados durante a auditoria D23D69.
# Estes registros continuam sendo apenas evidência para diagnóstico. O script
# não altera lançamentos, pagamentos, obrigações nem conciliações.
MAPEAMENTOS_BANCARIOS_CONFIRMADOS = {
    601: {
        "competencia": "04/2026",
        "valor": Decimal("1000.00"),
        "natureza": "ADMIN_SEDE_30",
        "descricao": "Parcela restante do administrativo de 04/2026 paga por PIX no acerto posterior.",
    },
    600: {
        "competencia": "05/2026",
        "valor": Decimal("1426.00"),
        "natureza": "REPASSE_COMPETENCIA",
        "descricao": "Acerto da competencia 05/2026 pago por PIX, sem incluir Projeto Filipe.",
    },
}

# Em 05/2026, o PIX real foi R$ 1.426,00 e o Projeto Filipe de R$ 10,00 NÃO
# estava incluído nesse acerto. Após a realocação D23D48, a parte efetivamente
# atribuível à competência de maio, sem Projeto Filipe, é R$ 1.415,59.
# A diferença de R$ 10,41 deve permanecer como crédito/ajuste não alocado até
# sua destinação documental ser confirmada.
VALOR_REFERENCIA_MAIO_SEM_PROJETO_FILIPE = Decimal("1415.59")


def rows(conn, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute(text(sql), params or {}).mappings().all()]


def monthly_table(rows_: list[dict[str, Any]], through_month: int) -> dict[int, dict[str, Decimal]]:
    out: dict[int, dict[str, Decimal]] = {
        mes: {"entradas": Decimal("0.00"), "saidas": Decimal("0.00"), "saldo_mes": Decimal("0.00")}
        for mes in range(1, through_month + 1)
    }
    for row in rows_:
        mes = int(row["mes"])
        if "entradas" in row:
            out[mes]["entradas"] = d2(row.get("entradas"))
        if "saidas" in row:
            out[mes]["saidas"] = d2(row.get("saidas"))
        out[mes]["saldo_mes"] = d2(row.get("saldo_mes"))
    return out


def cumulative(table: dict[int, dict[str, Decimal]]) -> dict[int, Decimal]:
    total = Decimal("0.00")
    out: dict[int, Decimal] = {}
    for mes in sorted(table):
        total = d2(total + d2(table[mes]["saldo_mes"]))
        out[mes] = total
    return out


def classify_candidate(row: dict[str, Any]) -> str:
    obs = (row.get("observacoes") or "").lower()
    desc = (row.get("descricao") or "").lower()

    if "fachada" in obs:
        return "OUTRO_GASTO_SEDE_FACHADA"
    if "pereiras" in obs or "devolução" in obs or "devolucao" in obs:
        return "OUTRO_GASTO_OU_DEVOLUCAO"
    if "agenda pastoral" in obs:
        return "OUTRO_GASTO_CONSELHO"
    if "administrativo" in obs:
        return "CANDIDATO_REPASSE_ADMIN"
    if "projeto filipe" in obs or "força para viver" in obs or "forca para viver" in obs:
        return "CANDIDATO_DESPESA_FIXA_SEDE"
    if "igreja evang pentecostal o brasil para cristo" in desc:
        return "CANDIDATO_REPASSE_SEM_CLASSIFICACAO"
    return "REVISAR"


def audit(conn, year: int, through_month: int) -> dict[str, Any]:
    if not all(is_readonly_sql(sql) for sql in READ_ONLY_SQL):
        raise RuntimeError("Auditoria bloqueada: foi detectado SQL com escrita.")

    legados = rows(conn, SQL_LEGADOS)
    historicos = rows(conn, SQL_HISTORICOS)
    candidatos = rows(conn, SQL_CANDIDATOS_IMPORTADOS)

    atual_rows = rows(conn, SQL_MENSAL_ATUAL, {"ano": year, "mes_limite": through_month})
    sim_rows = rows(conn, SQL_MENSAL_SIMULADO, {"ano": year, "mes_limite": through_month})

    atual = monthly_table(atual_rows, through_month)
    sim = monthly_table(sim_rows, through_month)
    acum_atual = cumulative(atual)
    acum_sim = cumulative(sim)

    legados_por_mes: dict[str, dict[str, Any]] = {}
    for row in legados:
        if not row.get("data") or int(row["data"].year) != year or int(row["data"].month) > through_month:
            continue
        key = f"{row['data'].month:02d}/{year}"
        item = legados_por_mes.setdefault(key, {"qtd": 0, "total": Decimal("0.00"), "ids": []})
        item["qtd"] += 1
        item["total"] = d2(item["total"] + d2(row["valor"]))
        item["ids"].append(int(row["id"]))

    pagamentos_sem_data_exata = [
        {
            "id": int(row["id"]),
            "competencia": row.get("competencia"),
            "data_armazenada": str(row.get("data_pagamento")),
            "valor_total": money(row.get("valor_total")),
            "forma_pagamento": row.get("forma_pagamento"),
        }
        for row in historicos
        if not bool(row.get("data_pagamento_informada"))
    ]

    historicos_sem_lancamento = [
        {
            "id": int(row["id"]),
            "competencia": row.get("competencia"),
            "data_pagamento": str(row.get("data_pagamento")),
            "data_pagamento_informada": bool(row.get("data_pagamento_informada")),
            "valor_total": money(row.get("valor_total")),
            "forma_pagamento": row.get("forma_pagamento"),
        }
        for row in historicos
        if row.get("lancamento_financeiro_id") is None
    ]

    candidatos_out = []
    for row in candidatos:
        if not row.get("data") or int(row["data"].year) != year or int(row["data"].month) > through_month:
            continue
        rid = int(row["id"])
        mapping = MAPEAMENTOS_BANCARIOS_CONFIRMADOS.get(rid)
        candidatos_out.append({
            "id": rid,
            "data": str(row["data"]),
            "valor": money(row.get("valor")),
            "categoria": row.get("categoria"),
            "descricao": row.get("descricao"),
            "observacoes": row.get("observacoes"),
            "classificacao_preliminar": (
                "MAPEAMENTO_CONFIRMADO" if mapping else classify_candidate(row)
            ),
            "mapeamento_confirmado": (
                {
                    "competencia": mapping["competencia"],
                    "valor": money(mapping["valor"]),
                    "natureza": mapping["natureza"],
                    "descricao": mapping["descricao"],
                }
                if mapping else None
            ),
        })

    meses = []
    for mes in range(1, through_month + 1):
        meses.append({
            "competencia": f"{mes:02d}/{year}",
            "saldo_mes_atual": money(atual[mes]["saldo_mes"]),
            "saldo_acumulado_atual": money(acum_atual[mes]),
            "saldo_mes_simulado": money(sim[mes]["saldo_mes"]),
            "saldo_acumulado_simulado": money(acum_sim[mes]),
            "diferenca_acumulada": money(acum_sim[mes] - acum_atual[mes]),
        })

    blockers = []
    if pagamentos_sem_data_exata:
        blockers.append(
            "Existem pagamentos historicos com data real nao informada; nao converter automaticamente em movimento financeiro."
        )
    pendentes_nao_mapeados = [
        row for row in candidatos_out if not row.get("mapeamento_confirmado")
    ]
    if pendentes_nao_mapeados:
        blockers.append(
            "Existem movimentos importados da Sede ainda nao conciliados/classificados; neutralizar o legado antes de mapea-los pode duplicar ou omitir caixa."
        )
    if any(row["id"] == 600 for row in candidatos_out):
        blockers.append(
            "O PIX ID 600 foi confirmado como acerto de 05/2026 sem Projeto Filipe. A regularizacao deve preservar o Projeto Filipe para o pagamento acumulado de agosto e tratar R$ 10,41 como credito/ajuste nao alocado."
        )

    return {
        "d23d69": "AUDITORIA_CAIXA_SEDE_LEGADO",
        "modo": "READ_ONLY",
        "banco_alterado": False,
        "ano": year,
        "mes_limite": through_month,
        "legados_automaticos_ainda_impactando": {
            "quantidade": sum(item["qtd"] for item in legados_por_mes.values()),
            "total": money(sum((d2(item["total"]) for item in legados_por_mes.values()), Decimal("0.00"))),
            "por_mes": {
                k: {"qtd": v["qtd"], "total": money(v["total"]), "ids": v["ids"]}
                for k, v in legados_por_mes.items()
            },
        },
        "pagamentos_historicos_sem_data_exata": pagamentos_sem_data_exata,
        "pagamentos_historicos_sem_lancamento_financeiro": historicos_sem_lancamento,
        "movimentos_importados_sede_pendentes_de_revisao": candidatos_out,
        "mapeamentos_bancarios_confirmados": {
            str(k): {
                "competencia": v["competencia"],
                "valor": money(v["valor"]),
                "natureza": v["natureza"],
                "descricao": v["descricao"],
            }
            for k, v in MAPEAMENTOS_BANCARIOS_CONFIRMADOS.items()
        },
        "ajuste_maio": {
            "pix_real": money(MAPEAMENTOS_BANCARIOS_CONFIRMADOS[600]["valor"]),
            "referencia_maio_sem_projeto_filipe": money(VALOR_REFERENCIA_MAIO_SEM_PROJETO_FILIPE),
            "projeto_filipe_incluido_no_pix": False,
            "credito_ou_ajuste_nao_alocado": money(
                MAPEAMENTOS_BANCARIOS_CONFIRMADOS[600]["valor"] - VALOR_REFERENCIA_MAIO_SEM_PROJETO_FILIPE
            ),
            "observacao": "Projeto Filipe de 05/2026 permaneceu para o pagamento acumulado de agosto. O excedente de R$ 10,41 do PIX de maio deve ficar como crédito/ajuste não alocado até confirmação documental.",
        },
        "comparativo_mensal_simulacao_teorica": meses,
        "bloqueios_para_apply": blockers,
        "apto_para_apply": len(blockers) == 0,
        "observacao": (
            "A simulacao mensal e apenas diagnostica: neutraliza obrigacoes automaticas antigas "
            "e recoloca pagamentos historicos pela data armazenada. Nao deve ser aplicada enquanto "
            "existirem movimentos bancarios pendentes de reconciliacao."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", default=True)
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--through-month", type=int, default=8)
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    args = parser.parse_args()

    if args.through_month < 1 or args.through_month > 12:
        parser.error("--through-month deve estar entre 1 e 12")

    url = normalize_database_url(args.database_url)
    if not url:
        print("D23D69: BLOQUEADA - DATABASE_URL ausente")
        return 2

    engine = create_engine(url)
    with engine.connect() as conn:
        resultado = audit(conn, args.year, args.through_month)

    print(json.dumps(resultado, ensure_ascii=False, indent=2, default=str))
    if resultado["apto_para_apply"]:
        print("D23D69: AUDITORIA SEM BLOQUEIOS")
    else:
        print("D23D69: APPLY BLOQUEADO - revisar itens antes de qualquer escrita")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
