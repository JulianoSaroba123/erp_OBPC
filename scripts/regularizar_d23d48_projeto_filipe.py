#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regularizacao historica D23D48 para o repasse de 28/08/2026.

Padrao: --check (somente leitura).
Escrita: --apply --confirm D23D48-PROJETO-FILIPE-30.

Fatos confirmados:
- 06/2026: 2573.31 = 2403.31 + 100 + 50 + 20
- 07/2026: 1292.56 = 1122.56 + 100 + 50 + 20
- Projeto Filipe: um PIX real de 30.00 quitou 05/2026, 06/2026 e 07/2026
- Total bancario preservado: 3895.87
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import create_engine, text

MARKER = "D23D48_REGULARIZACAO_PROJETO_FILIPE_3M"
CONFIRM_TOKEN = "D23D48-PROJETO-FILIPE-30"
USUARIO = "D23D48_REGULARIZACAO"
DATA = date(2026, 8, 28)

MANUAIS_ANTES = {615: Decimal("2583.31"), 616: Decimal("1302.56")}
MANUAIS_DEPOIS = {615: Decimal("2573.31"), 616: Decimal("1292.56")}
PAGAMENTOS = {
    11: (615, Decimal("2583.31"), Decimal("2573.31")),
    12: (616, Decimal("1302.56"), Decimal("1292.56")),
}
ENVIOS = {
    25: (Decimal("1425.59"), Decimal("1415.59"), Decimal("280.00"), Decimal("270.00"), Decimal("1145.59")),
    26: (Decimal("2583.31"), Decimal("2573.31"), Decimal("180.00"), Decimal("170.00"), Decimal("2403.31")),
    27: (Decimal("1302.56"), Decimal("1292.56"), Decimal("180.00"), Decimal("170.00"), Decimal("1122.56")),
}
IMPORTADOS = {
    664: Decimal("30.00"), 666: Decimal("20.00"), 667: Decimal("50.00"),
    668: Decimal("100.00"), 669: Decimal("1122.56"), 670: Decimal("50.00"),
    671: Decimal("20.00"), 672: Decimal("100.00"), 673: Decimal("2403.31"),
}
PARES = {
    615: [673, 672, 670, 671],
    616: [669, 668, 667, 666],
}
LEGADOS = {
    423: Decimal("10.00"),
    516: Decimal("100.00"),
    517: Decimal("50.00"),
    518: Decimal("10.00"),
    519: Decimal("20.00"),
}
TOTAL = Decimal("3895.87")


def d2(v: Any) -> Decimal:
    return Decimal(str(v or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def normalizar_url(url: str | None) -> str | None:
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def obs_atualizada(original: Any, extra: str) -> str:
    base = (str(original) if original is not None else "").strip()
    if extra in base:
        return base
    return f"{base} | {extra}" if base else extra


def rows(conn, sql: str) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute(text(sql)).mappings().all()]


def by_id(lista: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(r["id"]): r for r in lista}


def validar_configuracao() -> list[str]:
    erros = []
    if sum(IMPORTADOS.values(), Decimal("0.00")) != TOTAL:
        erros.append("soma das linhas bancarias nao fecha em 3895.87")
    if MANUAIS_DEPOIS[615] + MANUAIS_DEPOIS[616] + IMPORTADOS[664] != TOTAL:
        erros.append("representacao economica final nao fecha")
    if sum(IMPORTADOS[i] for i in PARES[615]) != MANUAIS_DEPOIS[615]:
        erros.append("componentes de 06/2026 nao fecham")
    if sum(IMPORTADOS[i] for i in PARES[616]) != MANUAIS_DEPOIS[616]:
        erros.append("componentes de 07/2026 nao fecham")
    if 664 in PARES[615] + PARES[616]:
        erros.append("PIX de 30 nao pode ser evidencia do repasse")
    return erros


def snapshot(conn) -> dict[str, Any]:
    return {
        "lanc": rows(conn, """
            SELECT id,data,tipo,categoria,descricao,valor,conta,origem,conciliado,
                   conciliado_em,conciliado_por,par_conciliacao_id,observacoes
            FROM lancamentos
            WHERE id IN (423,516,517,518,519,615,616,664,666,667,668,669,670,671,672,673)
            ORDER BY id
        """),
        "pag": rows(conn, """
            SELECT id,data_pagamento,valor_pago,forma_pagamento,tipo_pagamento,
                   observacao,lancamento_financeiro_id
            FROM pagamentos_obrigacao
            WHERE id IN (11,12) OR lancamento_financeiro_id=664
            ORDER BY id
        """),
        "itens": rows(conn, """
            SELECT i.id,i.pagamento_obrigacao_id,i.obrigacao_financeira_id,i.valor_alocado,
                   o.competencia_mes,o.competencia_ano,o.status
            FROM pagamentos_obrigacao_itens i
            JOIN obrigacoes_financeiras o ON o.id=i.obrigacao_financeira_id
            WHERE i.pagamento_obrigacao_id IN (
                SELECT id FROM pagamentos_obrigacao
                WHERE id IN (11,12) OR lancamento_financeiro_id=664
            )
            ORDER BY i.id
        """),
        "envios": rows(conn, """
            SELECT id,pagamento_obrigacao_id,data_pagamento,valor,valor_total,
                   valor_administrativo,valor_despesas_fixas,competencia,
                   competencia_mes,competencia_ano,competencia_mes_ref,competencia_ano_ref,
                   tipo_pagamento,lancamento_financeiro_id,observacao,
                   pagamento_historico_sem_movimentacao
            FROM envios_sede
            WHERE id IN (25,26,27) OR lancamento_financeiro_id=664
            ORDER BY id
        """),
        "proj": rows(conn, """
            SELECT id,tipo_obrigacao,origem_obrigacao,referencia_origem_tipo,
                   referencia_origem_id,descricao,competencia_mes,competencia_ano,
                   valor_devido,status,data_quitacao
            FROM obrigacoes_financeiras
            WHERE tipo_obrigacao='DESPESA_FIXA'
              AND referencia_origem_tipo='DESPESA_FIXA_CONSELHO'
              AND referencia_origem_id=3
              AND competencia_ano=2026 AND competencia_mes IN (5,6,7)
            ORDER BY competencia_mes,id
        """),
        "pares": rows(conn, """
            SELECT id,lancamento_manual_id,lancamento_importado_id,ativo
            FROM conciliacao_pares
            WHERE ativo IS TRUE
              AND (lancamento_manual_id IN (615,616)
                   OR lancamento_importado_id IN (664,666,667,668,669,670,671,672,673))
            ORDER BY id
        """),
    }


def ja_aplicado(s: dict[str, Any]) -> bool:
    pagamentos = [p for p in s["pag"] if int(p.get("lancamento_financeiro_id") or 0) == 664]
    if len(pagamentos) != 1 or d2(pagamentos[0]["valor_pago"]) != Decimal("30.00"):
        return False
    return MARKER in (pagamentos[0].get("observacao") or "")


def validar_estado_original(s: dict[str, Any]) -> list[str]:
    erros: list[str] = []
    lanc = by_id(s["lanc"])
    pags = by_id(s["pag"])
    envios = by_id(s["envios"])

    for lid, valor in MANUAIS_ANTES.items():
        r = lanc.get(lid)
        if not r or d2(r["valor"]) != valor or r["data"] != DATA or (r.get("origem") or "").lower() != "manual":
            erros.append(f"manual {lid} divergente")
        elif bool(r.get("conciliado")) or r.get("par_conciliacao_id") is not None:
            erros.append(f"manual {lid} ja conciliado")

    for pid, (lanc_id, antes, _depois) in PAGAMENTOS.items():
        p = pags.get(pid)
        if not p or int(p.get("lancamento_financeiro_id") or 0) != lanc_id or d2(p.get("valor_pago")) != antes:
            erros.append(f"pagamento {pid} divergente")

    itens = {(int(i["pagamento_obrigacao_id"]), int(i["obrigacao_financeira_id"])): d2(i["valor_alocado"]) for i in s["itens"]}
    esperado = {
        (11,11): Decimal("2403.31"), (11,17): Decimal("100.00"),
        (11,18): Decimal("50.00"), (11,19): Decimal("10.00"), (11,20): Decimal("20.00"),
        (12,12): Decimal("1122.56"), (12,21): Decimal("100.00"),
        (12,22): Decimal("50.00"), (12,23): Decimal("10.00"), (12,24): Decimal("20.00"),
    }
    if itens != esperado:
        erros.append("componentes dos pagamentos 11/12 divergentes")

    for eid, (antes_total, _depois_total, antes_fixas, _depois_fixas, admin) in ENVIOS.items():
        e = envios.get(eid)
        if not e or d2(e.get("valor_total")) != antes_total or d2(e.get("valor_despesas_fixas")) != antes_fixas or d2(e.get("valor_administrativo")) != admin:
            erros.append(f"envio {eid} divergente")

    for iid, valor in IMPORTADOS.items():
        r = lanc.get(iid)
        if not r or r["data"] != DATA or d2(r["valor"]) != valor or (r.get("origem") or "").lower() != "importado":
            erros.append(f"importado {iid} divergente")
        elif bool(r.get("conciliado")) or r.get("par_conciliacao_id") is not None:
            erros.append(f"importado {iid} ja conciliado")

    for lid, valor in LEGADOS.items():
        r = lanc.get(lid)
        if not r or d2(r["valor"]) != valor or (r.get("origem") or "").lower() != "automatico":
            erros.append(f"legado {lid} divergente")
        elif (r.get("tipo") or "").strip().lower() not in {"saída","saida"}:
            erros.append(f"legado {lid} ja nao e Saida")

    if s["pares"]:
        erros.append("ja existem pares ativos no alvo")
    if any(int(p.get("lancamento_financeiro_id") or 0) == 664 for p in s["pag"]):
        erros.append("PIX 664 ja possui PagamentoObrigacao")

    maio = [o for o in s["proj"] if int(o.get("competencia_mes") or 0) == 5]
    junho = [o for o in s["proj"] if int(o.get("competencia_mes") or 0) == 6]
    julho = [o for o in s["proj"] if int(o.get("competencia_mes") or 0) == 7]
    if maio:
        erros.append("ja existe obrigacao explicita Projeto Filipe 05/2026")
    if len(junho) != 1 or int(junho[0]["id"]) != 19 or d2(junho[0]["valor_devido"]) != Decimal("10.00"):
        erros.append("obrigacao Projeto Filipe 06/2026 divergente")
    if len(julho) != 1 or int(julho[0]["id"]) != 23 or d2(julho[0]["valor_devido"]) != Decimal("10.00"):
        erros.append("obrigacao Projeto Filipe 07/2026 divergente")
    return erros


def inserir_evento(conn, ob_id: int, tipo: str, payload: dict[str, Any], now: datetime):
    conn.execute(text("""
        INSERT INTO obrigacao_eventos
        (obrigacao_financeira_id,evento_tipo,payload_json,usuario,created_at)
        VALUES (:ob,:tipo,:payload,:usuario,:now)
    """), {"ob": ob_id, "tipo": tipo, "payload": json.dumps(payload, ensure_ascii=False), "usuario": USUARIO, "now": now})


def aplicar(conn) -> dict[str, Any]:
    s = snapshot(conn)
    erros = validar_estado_original(s)
    if erros:
        raise RuntimeError("Gate bloqueado: " + " | ".join(erros))

    now = datetime.utcnow()
    lanc = by_id(s["lanc"])
    envios = by_id(s["envios"])

    for lid, valor in MANUAIS_DEPOIS.items():
        conn.execute(text("""
            UPDATE lancamentos
            SET valor=:valor, descricao='Pagamento composto de 4 obrigação(ões)', observacoes=:obs
            WHERE id=:id
        """), {"id": lid, "valor": valor, "obs": obs_atualizada(lanc[lid].get("observacoes"), f"{MARKER}: Projeto Filipe retirado do composto e quitado no PIX ID 664.")})

    for pid, (_lid, _antes, depois) in PAGAMENTOS.items():
        atual = next(p for p in s["pag"] if int(p["id"]) == pid)
        conn.execute(text("""
            UPDATE pagamentos_obrigacao
            SET valor_pago=:valor, observacao=:obs, updated_at=:now, atualizado_por=:usuario
            WHERE id=:id
        """), {"id": pid, "valor": depois, "obs": obs_atualizada(atual.get("observacao"), f"{MARKER}: Projeto Filipe realocado para PIX acumulado ID 664."), "now": now, "usuario": USUARIO})

    for item_id, pag_id, ob_id in [(14,11,19),(19,12,23)]:
        apagado = conn.execute(text("""
            DELETE FROM pagamentos_obrigacao_itens
            WHERE id=:id AND pagamento_obrigacao_id=:pag AND obrigacao_financeira_id=:ob AND valor_alocado=10.00
            RETURNING id
        """), {"id": item_id, "pag": pag_id, "ob": ob_id}).scalar()
        if apagado != item_id:
            raise RuntimeError(f"item {item_id} nao removido")

    for eid, (_antes_total, depois_total, _antes_fixas, depois_fixas, _admin) in ENVIOS.items():
        conn.execute(text("""
            UPDATE envios_sede
            SET valor=:total, valor_total=:total, valor_despesas_fixas=:fixas,
                observacao=:obs, updated_at=:now
            WHERE id=:id
        """), {"id": eid, "total": depois_total, "fixas": depois_fixas, "obs": obs_atualizada(envios[eid].get("observacao"), f"{MARKER}: Projeto Filipe R$ 10,00 removido desta competencia; pago acumulado em 28/08/2026."), "now": now})

    ob_maio = int(conn.execute(text("""
        INSERT INTO obrigacoes_financeiras
        (tipo_obrigacao,origem_obrigacao,referencia_origem_tipo,referencia_origem_id,
         categoria,descricao,competencia_mes,competencia_ano,valor_devido,status,
         data_quitacao,historico_sem_movimentacao,observacao,created_at,updated_at,criado_por,atualizado_por)
        VALUES ('DESPESA_FIXA','migracao','DESPESA_FIXA_CONSELHO',3,
                'DESP. FIXAS','Projeto Filipe - Despesa Fixa 05/2026',5,2026,10.00,'PENDENTE',
                NULL,FALSE,:obs,:now,:now,:usuario,:usuario)
        RETURNING id
    """), {"obs": f"{MARKER}: competencia historica criada para o PIX acumulado de R$ 30,00.", "now": now, "usuario": USUARIO}).scalar_one())
    inserir_evento(conn, ob_maio, "CRIACAO", {"marker": MARKER, "competencia": "05/2026", "valor": "10.00"}, now)

    pag_proj = int(conn.execute(text("""
        INSERT INTO pagamentos_obrigacao
        (data_pagamento,valor_pago,forma_pagamento,tipo_pagamento,observacao,
         lancamento_financeiro_id,created_at,updated_at,criado_por,atualizado_por)
        VALUES (:data,30.00,'PIX','PAGAMENTO_BANCARIO',:obs,664,:now,:now,:usuario,:usuario)
        RETURNING id
    """), {"data": DATA, "obs": f"{MARKER}: PIX unico de R$ 30,00 do Projeto Filipe para 05/2026, 06/2026 e 07/2026.", "now": now, "usuario": USUARIO}).scalar_one())

    for ob_id, comp in [(ob_maio,"05/2026"),(19,"06/2026"),(23,"07/2026")]:
        conn.execute(text("""
            INSERT INTO pagamentos_obrigacao_itens
            (pagamento_obrigacao_id,obrigacao_financeira_id,valor_alocado,created_at)
            VALUES (:pag,:ob,10.00,:now)
        """), {"pag": pag_proj, "ob": ob_id, "now": now})
        conn.execute(text("""
            UPDATE obrigacoes_financeiras
            SET status='PAGO',data_quitacao=:data,updated_at=:now,atualizado_por=:usuario
            WHERE id=:ob
        """), {"data": DATA, "now": now, "usuario": USUARIO, "ob": ob_id})
        inserir_evento(conn, ob_id, "AJUSTE" if ob_id in (19,23) else "PAGAMENTO", {"marker": MARKER, "competencia": comp, "valor": "10.00", "pagamento_obrigacao_id": pag_proj, "lancamento_bancario_id": 664}, now)

    envio_proj = int(conn.execute(text("""
        INSERT INTO envios_sede
        (data_pagamento,valor,valor_administrativo,valor_despesas_fixas,valor_total,
         forma_pagamento,competencia,competencia_mes_ref,competencia_ano_ref,
         competencia_mes,competencia_ano,tipo_pagamento,pagamento_obrigacao_id,
         lancamento_financeiro_id,observacao,pagamento_historico_sem_movimentacao,
         data_pagamento_informada,created_at,updated_at)
        VALUES (:data,30.00,0.00,30.00,30.00,'PIX',
                'Projeto Filipe acumulado 05/2026 a 07/2026',NULL,NULL,NULL,NULL,
                'PAGAMENTO_BANCARIO',:pag,664,:obs,FALSE,TRUE,:now,:now)
        RETURNING id
    """), {"data": DATA, "pag": pag_proj, "obs": f"{MARKER}: pagamento acumulado de tres competencias.", "now": now}).scalar_one())

    conn.execute(text("UPDATE lancamentos SET observacoes=:obs WHERE id=664"), {"obs": obs_atualizada(lanc[664].get("observacoes"), f"{MARKER}: Projeto Filipe 05/2026 + 06/2026 + 07/2026.")})

    for lid in LEGADOS:
        conn.execute(text("""
            UPDATE lancamentos SET tipo='Evidência',observacoes=:obs WHERE id=:id
        """), {"id": lid, "obs": obs_atualizada(lanc[lid].get("observacoes"), f"{MARKER}: automatico legado neutralizado; fato economico ja representado pelo pagamento efetivo.")})

    hist_id = int(conn.execute(text("""
        INSERT INTO conciliacao_historico
        (data_conciliacao,usuario,total_conciliados,total_pendentes,tipo_conciliacao,
         observacao,tempo_execucao,regras_aplicadas)
        VALUES (:now,:usuario,8,0,'mista',:obs,0.0,:regras)
        RETURNING id
    """), {"now": now, "usuario": USUARIO, "obs": f"{MARKER}: 8 linhas bancarias vinculadas aos repasses 06/2026 e 07/2026.", "regras": json.dumps({"d23d48_regularizacao_historica": 8})}).scalar_one())

    for manual_id, importados in PARES.items():
        for imp_id in importados:
            par_id = int(conn.execute(text("""
                INSERT INTO conciliacao_pares
                (historico_id,lancamento_manual_id,lancamento_importado_id,score_similaridade,
                 regra_aplicada,metodo_conciliacao,usuario,criado_em,ativo)
                VALUES (:hist,:manual,:imp,1.0,'d23d48_regularizacao_historica_componentes',
                        'manual',:usuario,:now,TRUE)
                RETURNING id
            """), {"hist": hist_id, "manual": manual_id, "imp": imp_id, "usuario": USUARIO, "now": now}).scalar_one())
            conn.execute(text("""
                UPDATE lancamentos
                SET conciliado=TRUE,conciliado_em=:now,conciliado_por=:usuario,par_conciliacao_id=:par
                WHERE id=:id
            """), {"now": now, "usuario": USUARIO, "par": par_id, "id": imp_id})
        conn.execute(text("""
            UPDATE lancamentos
            SET conciliado=TRUE,conciliado_em=:now,conciliado_por=:usuario
            WHERE id=:id
        """), {"now": now, "usuario": USUARIO, "id": manual_id})

    pendentes = int(conn.execute(text("""
        SELECT (SELECT COUNT(*) FROM lancamentos WHERE origem='manual' AND conciliado IS FALSE)
             + (SELECT COUNT(*) FROM lancamentos WHERE origem='importado' AND conciliado IS FALSE)
    """)).scalar_one())
    conn.execute(text("UPDATE conciliacao_historico SET total_pendentes=:q WHERE id=:id"), {"q": pendentes, "id": hist_id})

    total_banco = d2(conn.execute(text("""
        SELECT SUM(valor) FROM lancamentos
        WHERE id IN (664,666,667,668,669,670,671,672,673)
    """)).scalar_one())
    if total_banco != TOTAL:
        raise RuntimeError(f"total bancario final divergente: {total_banco}")

    total_economico = d2(conn.execute(text("SELECT SUM(valor) FROM lancamentos WHERE id IN (615,616,664)")).scalar_one())
    if total_economico != TOTAL:
        raise RuntimeError(f"total economico final divergente: {total_economico}")

    for pid, (_lid, _antes, depois) in PAGAMENTOS.items():
        soma = d2(conn.execute(text("SELECT COALESCE(SUM(valor_alocado),0) FROM pagamentos_obrigacao_itens WHERE pagamento_obrigacao_id=:id"), {"id": pid}).scalar_one())
        if soma != depois:
            raise RuntimeError(f"itens do pagamento {pid} somam {soma}")
    soma_proj = d2(conn.execute(text("SELECT SUM(valor_alocado) FROM pagamentos_obrigacao_itens WHERE pagamento_obrigacao_id=:id"), {"id": pag_proj}).scalar_one())
    if soma_proj != Decimal("30.00"):
        raise RuntimeError(f"itens do Projeto Filipe somam {soma_proj}")

    return {"historico_id": hist_id, "pagamento_projeto_id": pag_proj, "envio_projeto_id": envio_proj, "obrigacao_maio_id": ob_maio, "total_banco": str(total_banco), "total_economico": str(total_economico)}


def resumo() -> dict[str, Any]:
    return {
        "06_2026": {"antes": "2583.31", "depois": "2573.31"},
        "07_2026": {"antes": "1302.56", "depois": "1292.56"},
        "projeto_filipe": {"pix": "30.00", "competencias": ["05/2026","06/2026","07/2026"]},
        "total_bancario": "3895.87",
        "pares": PARES,
        "legados_neutralizados": sorted(LEGADOS),
    }


def executar(url: str, apply: bool, confirm: str | None) -> int:
    erros_cfg = validar_configuracao()
    if erros_cfg:
        print("D23D48_REGULARIZACAO: BLOQUEADA_CONFIGURACAO")
        for e in erros_cfg:
            print("-", e)
        return 2

    engine = create_engine(url)
    if apply and engine.dialect.name != "postgresql":
        print("D23D48_REGULARIZACAO: BLOQUEADA - apply somente em PostgreSQL")
        return 2

    with engine.connect() as conn:
        s = snapshot(conn)
        if ja_aplicado(s):
            print("D23D48_REGULARIZACAO: JA_APLICADA")
            print(json.dumps(resumo(), ensure_ascii=False, indent=2))
            return 0
        erros = validar_estado_original(s)
        if erros:
            print("D23D48_REGULARIZACAO: BLOQUEADA_ESTADO_INESPERADO")
            for e in erros:
                print("-", e)
            return 2

    print("D23D48_REGULARIZACAO: APTO")
    print(json.dumps(resumo(), ensure_ascii=False, indent=2))
    if not apply:
        print("MODO: CHECK_READ_ONLY")
        print("BANCO_ALTERADO: NAO")
        return 0

    if confirm != CONFIRM_TOKEN:
        print("D23D48_REGULARIZACAO: BLOQUEADA_CONFIRMACAO")
        print(f"Use --confirm {CONFIRM_TOKEN}")
        return 2

    with engine.begin() as conn:
        resultado = aplicar(conn)
    print("D23D48_REGULARIZACAO: APLICADA")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
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
        print("D23D48_REGULARIZACAO: BLOQUEADA - DATABASE_URL ausente")
        return 2
    return executar(url, bool(args.apply), args.confirm)


if __name__ == "__main__":
    raise SystemExit(main())
