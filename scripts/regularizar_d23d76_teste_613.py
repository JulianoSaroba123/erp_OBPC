#!/usr/bin/env python3
"""
D23D76 - Neutraliza o lançamento manual de teste ID 613.

O registro é preservado para auditoria, mas deixa de impactar o caixa:
- ID 613
- 31/07/2026
- Saída
- DESP. VARIAVEIS
- descrição "teste"
- R$ 295,34
- conta Dinheiro
- origem manual
- sem comprovante, conciliação ou vínculo com obrigações/Sede

Modo padrão: somente leitura.
Modo de escrita: --apply exige token explícito.

Resultado esperado:
- saídas de julho: R$ 12.571,97
- saldo acumulado em 31/07: R$ 3.429,32
- saldo acumulado em 31/08: R$ 2.177,40
"""

from __future__ import annotations

import argparse
import json
import os
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import create_engine, text

TARGET_ID = 613
EXPECTED_VALUE = Decimal("295.34")
EXPECTED_DATE = "2026-07-31"
EXPECTED_CURRENT_AUG_BALANCE = Decimal("1882.06")
EXPECTED_FINAL_AUG_BALANCE = Decimal("2177.40")
EXPECTED_JULY_OUTFLOWS = Decimal("12571.97")
EXPECTED_JULY_ACCUMULATED = Decimal("3429.32")
MARKER = "D23D76_NEUTRALIZA_TESTE_613"
CONFIRM_TOKEN = "CONFIRMO_D23D76_TESTE_613"


def d2(v: Any) -> Decimal:
    return Decimal(str(v or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money(v: Any) -> str:
    return f"{d2(v):.2f}"


def normalize_url(url: str | None) -> str | None:
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def economic_type_sql() -> str:
    return """
        CASE
          WHEN lower(coalesce(origem,''))='importado'
               AND conciliado IS TRUE
               AND par_conciliacao_id IS NOT NULL
            THEN 'Evidência'
          ELSE tipo
        END
    """


def get_row(conn) -> dict[str, Any] | None:
    row = conn.execute(text("""
        SELECT id,data,tipo,categoria,descricao,valor,conta,origem,criado_em,
               observacoes,comprovante,conciliado,par_conciliacao_id,projeto_id
        FROM lancamentos
        WHERE id=:id
    """), {"id": TARGET_ID}).mappings().first()
    return dict(row) if row else None


def get_dependencies(conn) -> dict[str, int]:
    return {
        "comprovantes": int(conn.execute(text(
            "SELECT COUNT(*) FROM comprovantes WHERE lancamento_id=:id"
        ), {"id": TARGET_ID}).scalar_one()),
        "conciliacoes": int(conn.execute(text("""
            SELECT COUNT(*) FROM conciliacao_pares
            WHERE lancamento_manual_id=:id OR lancamento_importado_id=:id
        """), {"id": TARGET_ID}).scalar_one()),
        "envios_sede": int(conn.execute(text(
            "SELECT COUNT(*) FROM envios_sede WHERE lancamento_financeiro_id=:id"
        ), {"id": TARGET_ID}).scalar_one()),
        "pagamentos_obrigacao": int(conn.execute(text(
            "SELECT COUNT(*) FROM pagamentos_obrigacao WHERE lancamento_financeiro_id=:id"
        ), {"id": TARGET_ID}).scalar_one()),
    }


def saldo_ate(conn, data_limite: str) -> Decimal:
    sql = f"""
        SELECT COALESCE(SUM(
            CASE
              WHEN {economic_type_sql()}='Entrada' THEN valor
              WHEN {economic_type_sql()}='Saída' THEN -valor
              ELSE 0
            END
        ),0)
        FROM lancamentos
        WHERE data <= CAST(:data_limite AS DATE)
    """
    return d2(conn.execute(text(sql), {"data_limite": data_limite}).scalar_one())


def saidas_julho(conn) -> Decimal:
    sql = f"""
        SELECT COALESCE(SUM(valor),0)
        FROM lancamentos
        WHERE data BETWEEN DATE '2026-07-01' AND DATE '2026-07-31'
          AND {economic_type_sql()}='Saída'
    """
    return d2(conn.execute(text(sql)).scalar_one())


def validate(conn) -> list[str]:
    errors: list[str] = []
    row = get_row(conn)
    deps = get_dependencies(conn)

    if not row:
        return ["lançamento ID 613 não encontrado"]

    if str(row["data"]) != EXPECTED_DATE:
        errors.append(f"data divergente: {row['data']}")
    if row["tipo"] != "Saída":
        errors.append(f"tipo divergente: {row['tipo']}")
    if row["categoria"] != "DESP. VARIAVEIS":
        errors.append(f"categoria divergente: {row['categoria']}")
    if (row["descricao"] or "").strip().lower() != "teste":
        errors.append(f"descrição divergente: {row['descricao']}")
    if d2(row["valor"]) != EXPECTED_VALUE:
        errors.append(f"valor divergente: {money(row['valor'])}")
    if row["conta"] != "Dinheiro":
        errors.append(f"conta divergente: {row['conta']}")
    if row["origem"] != "manual":
        errors.append(f"origem divergente: {row['origem']}")
    if row.get("observacoes"):
        errors.append("registro já possui observação")
    if row.get("comprovante"):
        errors.append("registro possui comprovante")
    if bool(row.get("conciliado")) or row.get("par_conciliacao_id") is not None:
        errors.append("registro possui conciliação")
    if any(deps.values()):
        errors.append(f"registro possui dependências: {deps}")

    current_aug = saldo_ate(conn, "2026-08-31")
    if current_aug != EXPECTED_CURRENT_AUG_BALANCE:
        errors.append(
            f"saldo atual de 31/08 divergiu: {money(current_aug)} "
            f"(esperado {money(EXPECTED_CURRENT_AUG_BALANCE)})"
        )

    return errors


def preview(conn) -> dict[str, Any]:
    row = get_row(conn)
    deps = get_dependencies(conn)
    errors = validate(conn)
    current_aug = saldo_ate(conn, "2026-08-31")
    current_july_outflows = saidas_julho(conn)

    return {
        "status": "APTO" if not errors else "BLOQUEADO",
        "modo": "CHECK_READ_ONLY",
        "banco_alterado": False,
        "registro": row,
        "dependencias": deps,
        "erros": errors,
        "saldo_atual_31_08": money(current_aug),
        "saldo_previsto_31_08": money(current_aug + EXPECTED_VALUE),
        "saidas_julho_atuais": money(current_july_outflows),
        "saidas_julho_previstas": money(current_july_outflows - EXPECTED_VALUE),
        "saldo_acumulado_31_07_previsto": money(EXPECTED_JULY_ACCUMULATED),
        "acao": (
            "Preservar ID 613 e trocar tipo de Saída para Evidência, "
            "com marcador de auditoria D23D76."
        ),
        "apply_exige_token": CONFIRM_TOKEN,
    }


def apply(conn) -> dict[str, Any]:
    errors = validate(conn)
    if errors:
        raise RuntimeError("D23D76 bloqueada: " + " | ".join(errors))

    conn.execute(text("SELECT pg_advisory_xact_lock(237376)"))

    result = conn.execute(text("""
        UPDATE lancamentos
        SET tipo='Evidência',
            observacoes=:obs
        WHERE id=:id
          AND tipo='Saída'
          AND valor=:valor
          AND descricao='teste'
          AND origem='manual'
    """), {
        "id": TARGET_ID,
        "valor": EXPECTED_VALUE,
        "obs": (
            f"{MARKER}: lançamento manual de teste sem fato financeiro real; "
            "preservado apenas para auditoria."
        ),
    })

    if result.rowcount != 1:
        raise RuntimeError(f"D23D76 esperava alterar 1 registro; alterou {result.rowcount}")

    final_aug = saldo_ate(conn, "2026-08-31")
    final_july_outflows = saidas_julho(conn)

    if final_aug != EXPECTED_FINAL_AUG_BALANCE:
        raise RuntimeError(
            f"saldo final 31/08 divergente: {money(final_aug)} "
            f"(esperado {money(EXPECTED_FINAL_AUG_BALANCE)})"
        )
    if final_july_outflows != EXPECTED_JULY_OUTFLOWS:
        raise RuntimeError(
            f"saídas de julho divergentes: {money(final_july_outflows)} "
            f"(esperado {money(EXPECTED_JULY_OUTFLOWS)})"
        )

    return {
        "status": "APLICADA",
        "id": TARGET_ID,
        "tipo_novo": "Evidência",
        "valor_neutralizado": money(EXPECTED_VALUE),
        "saidas_julho": money(final_july_outflows),
        "saldo_31_08": money(final_aug),
        "marker": MARKER,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    args = parser.parse_args()

    if args.check and args.apply:
        parser.error("use apenas --check ou --apply")

    url = normalize_url(args.database_url)
    if not url:
        print("D23D76: BLOQUEADA - DATABASE_URL ausente")
        return 2

    engine = create_engine(url)

    with engine.connect() as conn:
        report = preview(conn)
    print("D23D76_PREVIEW")
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))

    if report["status"] != "APTO":
        print("D23D76: BLOQUEADA_PELO_GATE")
        return 2

    if not args.apply:
        print("D23D76: CHECK_READ_ONLY - BANCO ALTERADO: NAO")
        return 0

    if engine.dialect.name != "postgresql":
        print("D23D76: APPLY BLOQUEADO - somente PostgreSQL")
        return 2

    if args.confirm != CONFIRM_TOKEN:
        print("D23D76: APPLY BLOQUEADO - token inválido")
        return 2

    with engine.begin() as conn:
        result = apply(conn)

    print("D23D76_RESULTADO")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
