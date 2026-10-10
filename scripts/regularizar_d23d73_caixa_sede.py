#!/usr/bin/env python3
"""
D23D73 - Regularização histórica do caixa da Sede.

Modo padrão: --check, somente leitura.
Modo de escrita: --apply exige token explícito e executa tudo em uma única transação.

Objetivos:
1. neutralizar lançamentos automáticos legados que representavam obrigação, não caixa;
2. registrar os pagamentos em dinheiro na data real do acerto: 04/07/2026;
3. ligar os PIX reais de 03/07/2026 às competências de abril e maio sem duplicar caixa;
4. manter Projeto Filipe de 05/2026 no pagamento acumulado de agosto;
5. preservar R$ 10,41 de maio como crédito/ajuste não alocado;
6. preservar todo o histórico para auditoria.

Este script NÃO é executado automaticamente no deploy.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import create_engine, text


MARKER = "D23D73_REGULARIZACAO_CAIXA_SEDE"
CONFIRM_TOKEN = "CONFIRMO_D23D73_CAIXA_SEDE_2026"
USUARIO = "regularizacao_d23d73"

CURRENT_BALANCE = Decimal("-419.68")
EXPECTED_FINAL_BALANCE = Decimal("1882.06")
EXPECTED_LEGACY_TOTAL = Decimal("8718.15")
EXPECTED_CASH_TOTAL = Decimal("6416.41")
EXPECTED_JULY_REAL_PAYMENTS = Decimal("8842.41")
EXPECTED_AUG_REAL_PAYMENTS = Decimal("3895.87")

LEGACY = {
    73: Decimal("100.00"), 74: Decimal("100.00"), 75: Decimal("50.00"),
    76: Decimal("10.00"), 77: Decimal("20.00"), 79: Decimal("1240.95"),
    276: Decimal("100.00"), 277: Decimal("100.00"), 278: Decimal("50.00"),
    279: Decimal("10.00"), 280: Decimal("20.00"), 281: Decimal("1361.01"),
    282: Decimal("100.00"), 283: Decimal("100.00"), 284: Decimal("50.00"),
    285: Decimal("10.00"), 286: Decimal("20.00"), 287: Decimal("1829.11"),
    355: Decimal("100.00"), 356: Decimal("100.00"), 357: Decimal("50.00"),
    358: Decimal("10.00"), 359: Decimal("20.00"), 360: Decimal("1654.49"),
    420: Decimal("100.00"), 421: Decimal("100.00"), 422: Decimal("50.00"),
    424: Decimal("20.00"), 447: Decimal("1142.59"), 515: Decimal("100.00"),
}

CASH_DATE = date(2026, 7, 4)
CASH_ENVIOS = {
    15: {"pagamento_id": 3, "valor": Decimal("1520.00"), "competencia": "01/2026"},
    22: {"pagamento_id": 7, "valor": Decimal("0.95"), "competencia": "01/2026 ajuste"},
    16: {"pagamento_id": 4, "valor": Decimal("1641.01"), "competencia": "02/2026"},
    17: {"pagamento_id": 5, "valor": Decimal("2109.11"), "competencia": "03/2026"},
    18: {"pagamento_id": 6, "valor": Decimal("934.49"), "competencia": "04/2026 saldo"},
    24: {"pagamento_id": 9, "valor": Decimal("210.85"), "competencia": "04/2026 parcela"},
}

PIX_DATE = date(2026, 7, 3)
PIX_ENVIOS = {
    23: {
        "pagamento_id": 8,
        "importado_id": 601,
        "valor": Decimal("1000.00"),
        "competencia": "04/2026",
        "descricao": "Repasse à Sede - complemento 04/2026",
        "valor_devido_competencia": Decimal("1000.00"),
    },
    25: {
        "pagamento_id": 10,
        "importado_id": 600,
        "valor": Decimal("1426.00"),
        "competencia": "05/2026",
        "descricao": "Repasse à Sede - acerto 05/2026",
        "valor_devido_competencia": Decimal("1415.59"),
    },
}


def d2(v: Any) -> Decimal:
    return Decimal(str(v or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money(v: Any) -> str:
    return f"{d2(v):.2f}"


def normalizar_url(url: str | None) -> str | None:
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def obs_atualizada(original: Any, extra: str) -> str:
    base = (str(original) if original is not None else "").strip()
    if extra in base:
        return base
    return f"{base} | {extra}" if base else extra


def rows(conn, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute(text(sql), params or {}).mappings().all()]


def saldo_economico(conn, ate: date = date(2026, 8, 31)) -> Decimal:
    return d2(conn.execute(text("""
        SELECT COALESCE(SUM(
            CASE
              WHEN
                CASE
                  WHEN lower(coalesce(origem,''))='importado'
                       AND conciliado IS TRUE
                       AND par_conciliacao_id IS NOT NULL
                    THEN 'Evidência'
                  ELSE tipo
                END = 'Entrada'
                THEN valor
              WHEN
                CASE
                  WHEN lower(coalesce(origem,''))='importado'
                       AND conciliado IS TRUE
                       AND par_conciliacao_id IS NOT NULL
                    THEN 'Evidência'
                  ELSE tipo
                END = 'Saída'
                THEN -valor
              ELSE 0
            END
        ),0)
        FROM lancamentos
        WHERE data <= :ate
    """), {"ate": ate}).scalar_one())


def snapshot(conn) -> dict[str, Any]:
    return {
        "legacy": rows(conn, f"""
            SELECT id,data,tipo,categoria,descricao,valor,conta,origem,observacoes
            FROM lancamentos
            WHERE id IN ({",".join(str(x) for x in sorted(LEGACY))})
            ORDER BY id
        """),
        "envios": rows(conn, """
            SELECT id,pagamento_obrigacao_id,data_pagamento,valor,valor_total,
                   valor_administrativo,valor_despesas_fixas,valor_devido_competencia,
                   forma_pagamento,tipo_pagamento,lancamento_financeiro_id,
                   pagamento_historico_sem_movimentacao,data_pagamento_informada,observacao
            FROM envios_sede
            WHERE id IN (15,16,17,18,22,23,24,25)
            ORDER BY id
        """),
        "pagamentos": rows(conn, """
            SELECT id,data_pagamento,valor_pago,forma_pagamento,tipo_pagamento,
                   lancamento_financeiro_id,observacao
            FROM pagamentos_obrigacao
            WHERE id IN (3,4,5,6,7,8,9,10)
            ORDER BY id
        """),
        "pix_importados": rows(conn, """
            SELECT id,data,tipo,categoria,descricao,valor,conta,origem,conciliado,
                   par_conciliacao_id,observacoes
            FROM lancamentos
            WHERE id IN (600,601)
            ORDER BY id
        """),
        "marker_lancamentos": rows(conn, """
            SELECT id,data,tipo,categoria,descricao,valor,conta,origem,observacoes
            FROM lancamentos
            WHERE observacoes LIKE :marker
            ORDER BY id
        """, {"marker": f"%{MARKER}%"}),
    }


def validar_original(s: dict[str, Any], saldo_atual: Decimal) -> list[str]:
    erros: list[str] = []

    if saldo_atual != CURRENT_BALANCE:
        erros.append(f"saldo atual divergiu: {money(saldo_atual)}")

    if s["marker_lancamentos"]:
        erros.append("marcador D23D73 já existe em lançamentos")

    legacy = {int(r["id"]): r for r in s["legacy"]}
    if set(legacy) != set(LEGACY):
        erros.append("conjunto de lançamentos legados divergiu")
    else:
        for lid, valor in LEGACY.items():
            r = legacy[lid]
            if d2(r["valor"]) != valor:
                erros.append(f"legado {lid}: valor divergente")
            if (r.get("origem") or "").lower() != "automatico":
                erros.append(f"legado {lid}: origem divergente")
            if (r.get("tipo") or "").lower() not in {"saída", "saida"}:
                erros.append(f"legado {lid}: já não é saída")

    if d2(sum(LEGACY.values(), Decimal("0.00"))) != EXPECTED_LEGACY_TOTAL:
        erros.append("configuração do total legado não fecha")

    envios = {int(r["id"]): r for r in s["envios"]}
    for eid, cfg in CASH_ENVIOS.items():
        r = envios.get(eid)
        if not r:
            erros.append(f"envio em dinheiro {eid} ausente")
            continue
        if d2(r["valor_total"]) != cfg["valor"]:
            erros.append(f"envio {eid}: valor divergente")
        if (r.get("tipo_pagamento") or "") != "HISTORICO_SEM_MOVIMENTACAO":
            erros.append(f"envio {eid}: tipo histórico esperado")
        if r.get("lancamento_financeiro_id") is not None:
            erros.append(f"envio {eid}: já possui lançamento financeiro")

    if d2(sum((x["valor"] for x in CASH_ENVIOS.values()), Decimal("0.00"))) != EXPECTED_CASH_TOTAL:
        erros.append("configuração do acerto em dinheiro não fecha")

    pix = {int(r["id"]): r for r in s["pix_importados"]}
    for eid, cfg in PIX_ENVIOS.items():
        imp = pix.get(cfg["importado_id"])
        if not imp:
            erros.append(f"PIX importado {cfg['importado_id']} ausente")
            continue
        if d2(imp["valor"]) != cfg["valor"]:
            erros.append(f"PIX importado {cfg['importado_id']}: valor divergente")
        if imp.get("data") != PIX_DATE:
            erros.append(f"PIX importado {cfg['importado_id']}: data divergente")
        if (imp.get("origem") or "").lower() != "importado":
            erros.append(f"PIX importado {cfg['importado_id']}: origem divergente")
        if bool(imp.get("conciliado")) or imp.get("par_conciliacao_id") is not None:
            erros.append(f"PIX importado {cfg['importado_id']}: já conciliado")

        envio = envios.get(eid)
        if not envio or (envio.get("tipo_pagamento") or "") != "HISTORICO_SEM_MOVIMENTACAO":
            erros.append(f"envio PIX {eid}: estado histórico divergente")

    pagamentos = {int(r["id"]): r for r in s["pagamentos"]}
    for cfg in list(CASH_ENVIOS.values()) + list(PIX_ENVIOS.values()):
        pid = int(cfg["pagamento_id"])
        p = pagamentos.get(pid)
        if not p:
            erros.append(f"pagamento {pid} ausente")
        elif (p.get("tipo_pagamento") or "") != "HISTORICO_SEM_MOVIMENTACAO":
            erros.append(f"pagamento {pid}: tipo histórico divergente")

    return erros


def preview(conn) -> dict[str, Any]:
    s = snapshot(conn)
    saldo = saldo_economico(conn)
    erros = validar_original(s, saldo)
    final = d2(saldo + EXPECTED_LEGACY_TOTAL - EXPECTED_CASH_TOTAL)

    mensal = rows(conn, """
        WITH econ AS (
          SELECT data, valor,
                 CASE
                   WHEN lower(coalesce(origem,''))='importado'
                        AND conciliado IS TRUE
                        AND par_conciliacao_id IS NOT NULL
                     THEN 'Evidência'
                   ELSE tipo
                 END AS tipo_econ
          FROM lancamentos
        ),
        base AS (
          SELECT data,
                 CASE WHEN tipo_econ='Entrada' THEN valor
                      WHEN tipo_econ='Saída' THEN -valor
                      ELSE 0 END AS impacto
          FROM econ
        ),
        neutraliza AS (
          SELECT data, valor AS impacto
          FROM lancamentos
          WHERE id = ANY(:legacy_ids)
        ),
        dinheiro AS (
          SELECT DATE '2026-07-04' AS data, -6416.41::numeric AS impacto
        ),
        cenario AS (
          SELECT * FROM base
          UNION ALL SELECT * FROM neutraliza
          UNION ALL SELECT * FROM dinheiro
        ),
        m AS (
          SELECT EXTRACT(MONTH FROM data)::int mes,
                 SUM(impacto)::numeric(12,2) saldo_mes
          FROM cenario
          WHERE data BETWEEN DATE '2026-01-01' AND DATE '2026-08-31'
          GROUP BY 1
        ),
        meses AS (SELECT generate_series(1,8) mes)
        SELECT meses.mes,
               COALESCE(m.saldo_mes,0)::numeric(12,2) saldo_mes,
               SUM(COALESCE(m.saldo_mes,0)) OVER (ORDER BY meses.mes)::numeric(12,2) saldo_acumulado
        FROM meses LEFT JOIN m USING(mes)
        ORDER BY meses.mes
    """, {"legacy_ids": sorted(LEGACY)})

    return {
        "status": "APTO" if not erros and final == EXPECTED_FINAL_BALANCE else "BLOQUEADO",
        "modo": "CHECK_READ_ONLY",
        "banco_alterado": False,
        "erros": erros,
        "saldo_atual_31_08": money(saldo),
        "neutralizacao_legado": money(EXPECTED_LEGACY_TOTAL),
        "acerto_dinheiro_04_07": money(EXPECTED_CASH_TOTAL),
        "saldo_final_previsto_31_08": money(final),
        "pix_03_07": {
            "04_2026": "1000.00",
            "05_2026": "1426.00",
            "credito_maio": "10.41",
        },
        "ids_legado_neutralizados": sorted(LEGACY),
        "envios_dinheiro_convertidos": sorted(CASH_ENVIOS),
        "envios_pix_convertidos": sorted(PIX_ENVIOS),
        "mensal_pos_regularizacao": [
            {
                "mes": int(r["mes"]),
                "resultado": money(r["saldo_mes"]),
                "saldo_acumulado": money(r["saldo_acumulado"]),
            }
            for r in mensal
        ],
        "apply_exige_token": CONFIRM_TOKEN,
    }


def inserir_lancamento(conn, *, data_lanc, valor: Decimal, conta: str, descricao: str, observacao: str) -> int:
    return int(conn.execute(text("""
        INSERT INTO lancamentos
        (data,tipo,categoria,descricao,valor,conta,observacoes,origem,conciliado,criado_em)
        VALUES (:data,'Saída','CONTRIB. SEDE',:descricao,:valor,:conta,:obs,'manual',FALSE,:agora)
        RETURNING id
    """), {
        "data": data_lanc,
        "valor": valor,
        "conta": conta,
        "descricao": descricao,
        "obs": observacao,
        "agora": datetime.utcnow(),
    }).scalar_one())


def aplicar(conn) -> dict[str, Any]:
    s = snapshot(conn)
    saldo = saldo_economico(conn)
    erros = validar_original(s, saldo)
    if erros:
        raise RuntimeError("Gate D23D73 bloqueado: " + " | ".join(erros))

    agora = datetime.utcnow()
    legacy_by_id = {int(r["id"]): r for r in s["legacy"]}
    envios_by_id = {int(r["id"]): r for r in s["envios"]}
    pagamentos_by_id = {int(r["id"]): r for r in s["pagamentos"]}

    # 1) Obrigações automáticas legadas deixam de impactar caixa, mas ficam preservadas.
    for lid in sorted(LEGACY):
        row = legacy_by_id[lid]
        conn.execute(text("""
            UPDATE lancamentos
            SET tipo='Evidência', observacoes=:obs
            WHERE id=:id
        """), {
            "id": lid,
            "obs": obs_atualizada(
                row.get("observacoes"),
                f"{MARKER}: obrigação automática legada neutralizada; caixa reconhecido apenas no pagamento real."
            ),
        })

    novos_lancamentos_dinheiro: dict[int, int] = {}

    # 2) Acerto em dinheiro, pago integralmente em 04/07/2026.
    for eid, cfg in CASH_ENVIOS.items():
        envio = envios_by_id[eid]
        pid = int(cfg["pagamento_id"])
        pagamento = pagamentos_by_id[pid]
        lanc_id = inserir_lancamento(
            conn,
            data_lanc=CASH_DATE,
            valor=cfg["valor"],
            conta="Dinheiro",
            descricao=f"Acerto histórico Sede - {cfg['competencia']}",
            observacao=f"{MARKER}: parte do acerto em dinheiro de R$ 6.416,41 realizado em 04/07/2026; envio_sede_id={eid}.",
        )
        novos_lancamentos_dinheiro[eid] = lanc_id

        conn.execute(text("""
            UPDATE envios_sede
            SET data_pagamento=:data,
                valor=:valor,
                valor_total=:valor,
                forma_pagamento='Dinheiro',
                tipo_pagamento='PAGAMENTO_BANCARIO',
                lancamento_financeiro_id=:lanc_id,
                pagamento_historico_sem_movimentacao=FALSE,
                data_pagamento_informada=TRUE,
                observacao=:obs,
                updated_at=:agora
            WHERE id=:id
        """), {
            "data": CASH_DATE,
            "valor": cfg["valor"],
            "lanc_id": lanc_id,
            "obs": obs_atualizada(
                envio.get("observacao"),
                f"{MARKER}: data real do acerto em dinheiro confirmada em 04/07/2026."
            ),
            "agora": agora,
            "id": eid,
        })

        conn.execute(text("""
            UPDATE pagamentos_obrigacao
            SET data_pagamento=:data,
                valor_pago=:valor,
                forma_pagamento='Dinheiro',
                tipo_pagamento='PAGAMENTO_BANCARIO',
                lancamento_financeiro_id=:lanc_id,
                observacao=:obs,
                updated_at=:agora,
                atualizado_por=:usuario
            WHERE id=:id
        """), {
            "data": CASH_DATE,
            "valor": cfg["valor"],
            "lanc_id": lanc_id,
            "obs": obs_atualizada(
                pagamento.get("observacao"),
                f"{MARKER}: pagamento real consolidado no acerto em dinheiro de 04/07/2026."
            ),
            "agora": agora,
            "usuario": USUARIO,
            "id": pid,
        })

    # 3) PIX reais de abril e maio: criar representação econômica manual e
    # reconciliar o extrato importado como evidência, sem novo efeito de caixa.
    manual_pix: dict[int, int] = {}
    for eid, cfg in PIX_ENVIOS.items():
        manual_id = inserir_lancamento(
            conn,
            data_lanc=PIX_DATE,
            valor=cfg["valor"],
            conta="Pix",
            descricao=cfg["descricao"],
            observacao=(
                f"{MARKER}: representação econômica do PIX importado ID {cfg['importado_id']} "
                f"referente à competência {cfg['competencia']}."
            ),
        )
        manual_pix[eid] = manual_id

    hist_id = int(conn.execute(text("""
        INSERT INTO conciliacao_historico
        (data_conciliacao,usuario,total_conciliados,total_pendentes,tipo_conciliacao,
         observacao,tempo_execucao,regras_aplicadas)
        VALUES (:agora,:usuario,2,0,'mista',:obs,0.0,:regras)
        RETURNING id
    """), {
        "agora": agora,
        "usuario": USUARIO,
        "obs": f"{MARKER}: PIX de 04/2026 e 05/2026 vinculados ao extrato de 03/07/2026.",
        "regras": json.dumps({"d23d73_pix_historico": 2}),
    }).scalar_one())

    pares: dict[int, int] = {}
    for eid, cfg in PIX_ENVIOS.items():
        manual_id = manual_pix[eid]
        imp_id = int(cfg["importado_id"])
        par_id = int(conn.execute(text("""
            INSERT INTO conciliacao_pares
            (historico_id,lancamento_manual_id,lancamento_importado_id,score_similaridade,
             regra_aplicada,metodo_conciliacao,usuario,criado_em,ativo)
            VALUES (:hist,:manual,:importado,1.0,'d23d73_repasse_historico',
                    'manual',:usuario,:agora,TRUE)
            RETURNING id
        """), {
            "hist": hist_id,
            "manual": manual_id,
            "importado": imp_id,
            "usuario": USUARIO,
            "agora": agora,
        }).scalar_one())
        pares[imp_id] = par_id

        conn.execute(text("""
            UPDATE lancamentos
            SET conciliado=TRUE,conciliado_em=:agora,conciliado_por=:usuario,
                par_conciliacao_id=:par
            WHERE id=:id
        """), {
            "agora": agora, "usuario": USUARIO, "par": par_id, "id": imp_id
        })
        conn.execute(text("""
            UPDATE lancamentos
            SET conciliado=TRUE,conciliado_em=:agora,conciliado_por=:usuario
            WHERE id=:id
        """), {
            "agora": agora, "usuario": USUARIO, "id": manual_id
        })

        envio = envios_by_id[eid]
        pagamento = pagamentos_by_id[int(cfg["pagamento_id"])]
        extra_maio = (
            f" Crédito/ajuste não alocado de R$ 10,41 preservado."
            if eid == 25 else ""
        )

        conn.execute(text("""
            UPDATE envios_sede
            SET data_pagamento=:data,
                valor=:valor,
                valor_total=:valor,
                valor_devido_competencia=:devido,
                forma_pagamento='PIX',
                tipo_pagamento='PAGAMENTO_BANCARIO',
                lancamento_financeiro_id=:lanc_id,
                pagamento_historico_sem_movimentacao=FALSE,
                data_pagamento_informada=TRUE,
                observacao=:obs,
                updated_at=:agora
            WHERE id=:id
        """), {
            "data": PIX_DATE,
            "valor": cfg["valor"],
            "devido": cfg["valor_devido_competencia"],
            "lanc_id": manual_id,
            "obs": obs_atualizada(
                envio.get("observacao"),
                f"{MARKER}: PIX real identificado no extrato em 03/07/2026.{extra_maio}"
            ),
            "agora": agora,
            "id": eid,
        })

        conn.execute(text("""
            UPDATE pagamentos_obrigacao
            SET data_pagamento=:data,
                valor_pago=:valor,
                forma_pagamento='PIX',
                tipo_pagamento='PAGAMENTO_BANCARIO',
                lancamento_financeiro_id=:lanc_id,
                observacao=:obs,
                updated_at=:agora,
                atualizado_por=:usuario
            WHERE id=:id
        """), {
            "data": PIX_DATE,
            "valor": cfg["valor"],
            "lanc_id": manual_id,
            "obs": obs_atualizada(
                pagamento.get("observacao"),
                f"{MARKER}: pagamento real identificado pelo PIX importado ID {cfg['importado_id']}.{extra_maio}"
            ),
            "agora": agora,
            "usuario": USUARIO,
            "id": cfg["pagamento_id"],
        })

    # Atualiza total de pendentes da conciliação apenas como fotografia informativa.
    pendentes = int(conn.execute(text("""
        SELECT (SELECT COUNT(*) FROM lancamentos WHERE origem='manual' AND conciliado IS FALSE)
             + (SELECT COUNT(*) FROM lancamentos WHERE origem='importado' AND conciliado IS FALSE)
    """)).scalar_one())
    conn.execute(text("""
        UPDATE conciliacao_historico SET total_pendentes=:q WHERE id=:id
    """), {"q": pendentes, "id": hist_id})

    final = saldo_economico(conn)
    if final != EXPECTED_FINAL_BALANCE:
        raise RuntimeError(
            f"saldo final divergente após regularização: {money(final)} "
            f"(esperado {money(EXPECTED_FINAL_BALANCE)})"
        )

    julho = d2(conn.execute(text("""
        SELECT COALESCE(SUM(COALESCE(valor_total,valor)),0)
        FROM envios_sede
        WHERE data_pagamento BETWEEN DATE '2026-07-01' AND DATE '2026-07-31'
          AND tipo_pagamento='PAGAMENTO_BANCARIO'
          AND pagamento_historico_sem_movimentacao IS FALSE
    """)).scalar_one())
    if julho != EXPECTED_JULY_REAL_PAYMENTS:
        raise RuntimeError(f"pagamentos reais de julho divergentes: {money(julho)}")

    agosto = d2(conn.execute(text("""
        SELECT COALESCE(SUM(COALESCE(valor_total,valor)),0)
        FROM envios_sede
        WHERE data_pagamento BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
          AND tipo_pagamento='PAGAMENTO_BANCARIO'
          AND pagamento_historico_sem_movimentacao IS FALSE
    """)).scalar_one())
    if agosto != EXPECTED_AUG_REAL_PAYMENTS:
        raise RuntimeError(f"pagamentos reais de agosto divergentes: {money(agosto)}")

    return {
        "status": "APLICADA",
        "saldo_final_31_08": money(final),
        "pagamentos_reais_julho": money(julho),
        "pagamentos_reais_agosto": money(agosto),
        "lancamentos_dinheiro": novos_lancamentos_dinheiro,
        "lancamentos_pix_manuais": manual_pix,
        "pares_conciliacao": pares,
        "historico_conciliacao_id": hist_id,
        "credito_maio": "10.41",
    }


def executar(url: str, apply: bool, confirm: str | None) -> int:
    engine = create_engine(url)

    with engine.connect() as conn:
        pre = preview(conn)

    print("D23D73_PREVIEW")
    print(json.dumps(pre, ensure_ascii=False, indent=2, default=str))

    if pre["status"] != "APTO":
        print("D23D73: BLOQUEADA_PELO_GATE")
        return 2

    if not apply:
        print("D23D73: CHECK_READ_ONLY - BANCO ALTERADO: NAO")
        return 0

    if engine.dialect.name != "postgresql":
        print("D23D73: APPLY BLOQUEADO - somente PostgreSQL")
        return 2

    if confirm != CONFIRM_TOKEN:
        print("D23D73: APPLY BLOQUEADO - token de confirmação inválido")
        print(f"Use --confirm {CONFIRM_TOKEN}")
        return 2

    with engine.begin() as conn:
        result = aplicar(conn)

    print("D23D73_RESULTADO")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    args = parser.parse_args()

    if args.check and args.apply:
        parser.error("use apenas --check ou --apply")

    url = normalizar_url(args.database_url)
    if not url:
        print("D23D73: BLOQUEADA - DATABASE_URL ausente")
        return 2

    return executar(url, bool(args.apply), args.confirm)


if __name__ == "__main__":
    raise SystemExit(main())
