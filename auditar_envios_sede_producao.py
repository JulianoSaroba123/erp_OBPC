import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import create_engine, inspect, text


EXPECTED_ADMIN_PAGAMENTOS = Decimal("7230.20")
OBRIGACOES_ADMINISTRATIVAS = Decimal("7228.15")
SALDO_ESPERADO_JUNHO = Decimal("-2.05")


def fmt_value(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="seconds")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)


def to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def get_total(row: Dict[str, Any]) -> Decimal:
    valor_total = row.get("valor_total")
    if valor_total is not None:
        return to_decimal(valor_total)
    return to_decimal(row.get("valor"))


def competencia_efetiva(row: Dict[str, Any]) -> Optional[Tuple[int, int]]:
    cm = row.get("competencia_mes")
    ca = row.get("competencia_ano")
    if cm is not None and ca is not None:
        return int(cm), int(ca)

    cmr = row.get("competencia_mes_ref")
    car = row.get("competencia_ano_ref")
    if cmr is not None and car is not None:
        return int(cmr), int(car)

    dp = row.get("data_pagamento")
    if isinstance(dp, datetime):
        dp = dp.date()
    if isinstance(dp, date):
        return dp.month, dp.year

    return None


def competencia_label(comp: Optional[Tuple[int, int]]) -> str:
    if comp is None:
        return "NULL"
    return f"{comp[0]:02d}/{comp[1]}"


def periodo(rows: List[Dict[str, Any]]) -> Tuple[str, str]:
    datas: List[date] = []
    for row in rows:
        dp = row.get("data_pagamento")
        if isinstance(dp, datetime):
            datas.append(dp.date())
        elif isinstance(dp, date):
            datas.append(dp)
    if not datas:
        return "NULL", "NULL"
    return min(datas).isoformat(), max(datas).isoformat()


def helper_atual_admin(row: Dict[str, Any]) -> Decimal:
    total = get_total(row)
    valor_admin = row.get("valor_administrativo")
    valor_fixas = row.get("valor_despesas_fixas")

    if valor_admin is not None:
        return to_decimal(valor_admin)
    if valor_fixas is not None:
        calculado = total - to_decimal(valor_fixas)
        return calculado if calculado > 0 else Decimal("0")
    return total


def helper_zero_legado_admin(row: Dict[str, Any]) -> Decimal:
    total = get_total(row)
    valor_admin = row.get("valor_administrativo")
    valor_fixas = row.get("valor_despesas_fixas")

    if (
        valor_admin is not None
        and valor_fixas is not None
        and to_decimal(valor_admin) == 0
        and to_decimal(valor_fixas) == 0
        and total > 0
    ):
        return total

    return helper_atual_admin(row)


def print_header(table_exists: bool) -> None:
    print("=== AUDITORIA ENVIOS_SEDE PRODUÇÃO ===")
    print("DIALETO: postgresql")
    print("DATABASE_URL_DEFINIDA: SIM")
    print(f"TABELA_ENVIOS_SEDE: {'SIM' if table_exists else 'NÃO'}")
    print("MODO: SOMENTE LEITURA")


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("AUDITORIA CANCELADA: DATABASE_URL NÃO DEFINIDA")
        return

    normalized_url = database_url
    if normalized_url.startswith("postgres://"):
        normalized_url = normalized_url.replace("postgres://", "postgresql://", 1)

    engine = create_engine(normalized_url, future=True)

    if engine.url.get_backend_name() != "postgresql":
        print("AUDITORIA CANCELADA: BANCO NÃO É POSTGRESQL")
        engine.dispose()
        return

    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text("SET TRANSACTION READ ONLY"))

            insp = inspect(conn)
            table_exists = insp.has_table("envios_sede")
            print_header(table_exists)

            if not table_exists:
                print("AUDITORIA CANCELADA: TABELA ENVIOS_SEDE NÃO ENCONTRADA")
                return

            cols = [c["name"] for c in insp.get_columns("envios_sede")]
            cols_set = set(cols)

            print("=== COLUNAS ENVIOS_SEDE ===")
            for col in cols:
                print(col)

            desired_cols = [
                "id",
                "data_pagamento",
                "competencia",
                "competencia_mes",
                "competencia_ano",
                "competencia_mes_ref",
                "competencia_ano_ref",
                "valor",
                "valor_total",
                "valor_administrativo",
                "valor_despesas_fixas",
                "valor_devido_competencia",
                "tipo_pagamento",
                "observacao",
                "created_at",
                "updated_at",
            ]
            selected_cols = [c for c in desired_cols if c in cols_set]

            if not selected_cols:
                print("AUDITORIA CANCELADA: COLUNAS ESSENCIAIS NÃO ENCONTRADAS")
                return

            sql = "SELECT " + ", ".join(selected_cols) + " FROM envios_sede"
            rows = [dict(r) for r in conn.execute(text(sql)).mappings().all()]

            print(f"TOTAL_REGISTROS: {len(rows)}")

            def admin_is_null(row: Dict[str, Any]) -> bool:
                return "valor_administrativo" in cols_set and row.get("valor_administrativo") is None

            def admin_is_zero(row: Dict[str, Any]) -> bool:
                return "valor_administrativo" in cols_set and row.get("valor_administrativo") is not None and to_decimal(row.get("valor_administrativo")) == 0

            def fixas_is_null(row: Dict[str, Any]) -> bool:
                return "valor_despesas_fixas" in cols_set and row.get("valor_despesas_fixas") is None

            def fixas_is_zero(row: Dict[str, Any]) -> bool:
                return "valor_despesas_fixas" in cols_set and row.get("valor_despesas_fixas") is not None and to_decimal(row.get("valor_despesas_fixas")) == 0

            def total_positive(row: Dict[str, Any]) -> bool:
                return get_total(row) > 0

            grupo_a = [r for r in rows if admin_is_null(r)]
            pmin, pmax = periodo(grupo_a)
            print("=== GRUPO A ===")
            print(f"QUANTIDADE: {len(grupo_a)}")
            print(f"DATA_MIN: {pmin}")
            print(f"DATA_MAX: {pmax}")

            grupo_b = [
                r for r in rows
                if (
                    ((admin_is_zero(r) or admin_is_null(r)) if "valor_administrativo" in cols_set else True)
                    and ((fixas_is_zero(r) or fixas_is_null(r)) if "valor_despesas_fixas" in cols_set else True)
                    and total_positive(r)
                )
            ]
            pmin, pmax = periodo(grupo_b)
            soma_b = sum(get_total(r) for r in grupo_b)
            admin_null_b = sum(1 for r in grupo_b if admin_is_null(r))
            admin_zero_b = sum(1 for r in grupo_b if admin_is_zero(r))
            fixas_null_b = sum(1 for r in grupo_b if fixas_is_null(r))
            fixas_zero_b = sum(1 for r in grupo_b if fixas_is_zero(r))
            print("=== GRUPO B ===")
            print(f"QUANTIDADE: {len(grupo_b)}")
            print(f"ADMIN_IS_NULL: {admin_null_b}")
            print(f"ADMIN_ZERO: {admin_zero_b}")
            print(f"FIXAS_IS_NULL: {fixas_null_b}")
            print(f"FIXAS_ZERO: {fixas_zero_b}")
            print(f"DATA_MIN: {pmin}")
            print(f"DATA_MAX: {pmax}")
            print(f"SOMA_TOTAL: {fmt_value(soma_b)}")

            grupo_c = [r for r in rows if "valor_administrativo" in cols_set and r.get("valor_administrativo") is not None and to_decimal(r.get("valor_administrativo")) > 0]
            pmin, pmax = periodo(grupo_c)
            print("=== GRUPO C ===")
            print(f"QUANTIDADE: {len(grupo_c)}")
            print(f"DATA_MIN: {pmin}")
            print(f"DATA_MAX: {pmax}")

            grupo_d = [
                r for r in rows
                if (
                    "valor_administrativo" in cols_set
                    and "valor_despesas_fixas" in cols_set
                    and r.get("valor_administrativo") is not None
                    and r.get("valor_despesas_fixas") is not None
                    and to_decimal(r.get("valor_administrativo")) == 0
                    and to_decimal(r.get("valor_despesas_fixas")) > 0
                )
            ]
            pmin, pmax = periodo(grupo_d)
            print("=== GRUPO D ===")
            print(f"QUANTIDADE: {len(grupo_d)}")
            print(f"DATA_MIN: {pmin}")
            print(f"DATA_MAX: {pmax}")

            grupo_e = [
                r for r in rows
                if (
                    "valor_administrativo" in cols_set
                    and "valor_despesas_fixas" in cols_set
                    and r.get("valor_administrativo") is None
                    and r.get("valor_despesas_fixas") is not None
                    and to_decimal(r.get("valor_despesas_fixas")) > 0
                )
            ]
            pmin, pmax = periodo(grupo_e)
            print("=== GRUPO E ===")
            print(f"QUANTIDADE: {len(grupo_e)}")
            print(f"DATA_MIN: {pmin}")
            print(f"DATA_MAX: {pmax}")

            def diff_abs(row: Dict[str, Any]) -> Decimal:
                admin = to_decimal(row.get("valor_administrativo"))
                fixas = to_decimal(row.get("valor_despesas_fixas"))
                total = get_total(row)
                d = admin + fixas - total
                return d.copy_abs()

            grupo_f = [r for r in rows if diff_abs(r) > Decimal("0.01")]
            pmin, pmax = periodo(grupo_f)
            soma_diff = sum(diff_abs(r) for r in grupo_f)
            print("=== GRUPO F ===")
            print(f"QUANTIDADE: {len(grupo_f)}")
            print(f"DATA_MIN: {pmin}")
            print(f"DATA_MAX: {pmax}")
            print(f"SOMA_DIFERENCA_ABSOLUTA: {fmt_value(soma_diff)}")

            print("=== REGISTROS GRUPO B ===")
            ordered_b = sorted(
                grupo_b,
                key=lambda r: (
                    r.get("data_pagamento") or date.min,
                    r.get("id") or 0,
                ),
            )
            to_show: List[Dict[str, Any]]
            if len(ordered_b) <= 100:
                to_show = ordered_b
            else:
                to_show = ordered_b[:50] + ordered_b[-50:]

            for r in to_show:
                parts = []
                for c in selected_cols:
                    parts.append(f"{c}={fmt_value(r.get(c))}")
                print(" | ".join(parts))

            jan_mai_rows = []
            for r in rows:
                comp = competencia_efetiva(r)
                if comp is None:
                    continue
                if comp[1] == 2026 and 1 <= comp[0] <= 5:
                    jan_mai_rows.append((comp, r))

            jan_mai_rows.sort(key=lambda x: (x[0][1], x[0][0], x[1].get("data_pagamento") or date.min, x[1].get("id") or 0))

            for comp, r in jan_mai_rows:
                print("=== REGISTRO JAN-MAI ===")
                print(f"COMPETENCIA_EFETIVA: {competencia_label(comp)}")
                print(f"ID: {fmt_value(r.get('id'))}")
                print(f"DATA_PAGAMENTO: {fmt_value(r.get('data_pagamento'))}")
                print(f"VALOR: {fmt_value(r.get('valor'))}")
                print(f"VALOR_TOTAL: {fmt_value(r.get('valor_total'))}")
                print(f"VALOR_ADMINISTRATIVO: {fmt_value(r.get('valor_administrativo'))}")
                print(f"VALOR_DESPESAS_FIXAS: {fmt_value(r.get('valor_despesas_fixas'))}")
                print(f"VALOR_DEVIDO_COMPETENCIA: {fmt_value(r.get('valor_devido_competencia'))}")
                print(f"TIPO_PAGAMENTO: {fmt_value(r.get('tipo_pagamento'))}")
                print(f"CREATED_AT: {fmt_value(r.get('created_at'))}")
                print(f"UPDATED_AT: {fmt_value(r.get('updated_at'))}")

            for m in range(1, 6):
                comp = (m, 2026)
                subset = [r for c, r in jan_mai_rows if c == comp]
                soma_valor = sum(to_decimal(r.get("valor")) for r in subset)
                soma_valor_total = sum(to_decimal(r.get("valor_total")) for r in subset)
                soma_admin = sum(to_decimal(r.get("valor_administrativo")) for r in subset if r.get("valor_administrativo") is not None)
                admin_nulls = sum(1 for r in subset if r.get("valor_administrativo") is None)
                admin_zeros = sum(1 for r in subset if r.get("valor_administrativo") is not None and to_decimal(r.get("valor_administrativo")) == 0)
                soma_fixas = sum(to_decimal(r.get("valor_despesas_fixas")) for r in subset if r.get("valor_despesas_fixas") is not None)
                fixas_nulls = sum(1 for r in subset if r.get("valor_despesas_fixas") is None)
                fixas_zeros = sum(1 for r in subset if r.get("valor_despesas_fixas") is not None and to_decimal(r.get("valor_despesas_fixas")) == 0)

                print(f"=== COMPETENCIA {m:02d}/2026 ===")
                print(f"QUANTIDADE_REGISTROS: {len(subset)}")
                print(f"SOMA_VALOR: {fmt_value(soma_valor)}")
                print(f"SOMA_VALOR_TOTAL: {fmt_value(soma_valor_total)}")
                print(f"SOMA_VALOR_ADMINISTRATIVO: {fmt_value(soma_admin)}")
                print(f"VALOR_ADMINISTRATIVO_NULLS: {admin_nulls}")
                print(f"VALOR_ADMINISTRATIVO_ZEROS: {admin_zeros}")
                print(f"SOMA_VALOR_DESPESAS_FIXAS: {fmt_value(soma_fixas)}")
                print(f"VALOR_DESPESAS_FIXAS_NULLS: {fixas_nulls}")
                print(f"VALOR_DESPESAS_FIXAS_ZEROS: {fixas_zeros}")

            ate_mai = [r for r in rows if (competencia_efetiva(r) is not None and (competencia_efetiva(r)[1] < 2026 or (competencia_efetiva(r)[1] == 2026 and competencia_efetiva(r)[0] <= 5)))]

            helper_atual_pag = sum(helper_atual_admin(r) for r in ate_mai)
            zero_legado_pag = sum(helper_zero_legado_admin(r) for r in ate_mai)
            delta_estrategias = zero_legado_pag - helper_atual_pag

            print(f"HELPER_ATUAL_PAGAMENTOS_ADMIN: {fmt_value(helper_atual_pag)}")
            print(f"ZERO_LEGADO_PAGAMENTOS_ADMIN: {fmt_value(zero_legado_pag)}")
            print(f"DIFERENCA_ENTRE_ESTRATEGIAS: {fmt_value(delta_estrategias)}")

            print("=== CENARIO CONHECIDO JAN-MAI/2026 ===")
            print(f"OBRIGACOES_ADMINISTRATIVAS: {fmt_value(OBRIGACOES_ADMINISTRATIVAS)}")
            print(f"PAGAMENTOS_ADMINISTRATIVOS_ESPERADOS: {fmt_value(EXPECTED_ADMIN_PAGAMENTOS)}")
            print(f"SALDO_ESPERADO_JUNHO: {fmt_value(SALDO_ESPERADO_JUNHO)}")

            dif_helper_esp = helper_atual_pag - EXPECTED_ADMIN_PAGAMENTOS
            dif_zero_legado_esp = zero_legado_pag - EXPECTED_ADMIN_PAGAMENTOS
            print(f"DIFERENCA_HELPER_ATUAL_PARA_ESPERADO: {fmt_value(dif_helper_esp)}")
            print(f"DIFERENCA_ZERO_LEGADO_PARA_ESPERADO: {fmt_value(dif_zero_legado_esp)}")

            print("=== RESUMO AUDITORIA ===")
            print(f"TOTAL: {len(rows)}")
            print(f"GRUPO_B: {len(grupo_b)}")
            print(f"ADMIN_NULL_NO_GRUPO_B: {admin_null_b}")
            print(f"ADMIN_ZERO_NO_GRUPO_B: {admin_zero_b}")
            print(f"FIXAS_NULL_NO_GRUPO_B: {fixas_null_b}")
            print(f"FIXAS_ZERO_NO_GRUPO_B: {fixas_zero_b}")
            print(f"HELPER_ATUAL_PAGAMENTOS_ADMIN: {fmt_value(helper_atual_pag)}")
            print(f"ZERO_LEGADO_PAGAMENTOS_ADMIN: {fmt_value(zero_legado_pag)}")
            print(f"DIFERENCA_ENTRE_ESTRATEGIAS: {fmt_value(delta_estrategias)}")
            print(f"DIFERENCA_HELPER_ATUAL_PARA_ESPERADO: {fmt_value(dif_helper_esp)}")
            print(f"DIFERENCA_ZERO_LEGADO_PARA_ESPERADO: {fmt_value(dif_zero_legado_esp)}")
            print("=== FIM AUDITORIA ===")

    engine.dispose()


if __name__ == "__main__":
    main()
