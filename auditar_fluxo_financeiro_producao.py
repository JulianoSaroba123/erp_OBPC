#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from collections import defaultdict
from datetime import date, datetime
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy import create_engine, inspect, text


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except Exception:
        return 0.0


def _to_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _to_date(value: Any):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except Exception:
        return None


def _tipo_norm(tipo: Any) -> str:
    t = _to_str(tipo).strip().lower()
    if t == "entrada":
        return "entrada"
    if t in ("saida", "saída"):
        return "saida"
    return t


def _origem_norm(origem: Any) -> str:
    o = _to_str(origem).strip().lower()
    if not o:
        return "<null>"
    return o


def _bool_norm(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    s = _to_str(value).strip().lower()
    return s in ("1", "true", "t", "sim", "yes")


def _categoria_norm(value: Any) -> str:
    return _to_str(value).strip().lower()


def _descricao_norm(value: Any) -> str:
    return _to_str(value).strip().lower()


def _is_destinacao(categoria: Any) -> bool:
    cat = _categoria_norm(categoria)
    termos = (
        "destinacao",
        "destinação",
        "transferencia interna",
        "transferência interna",
    )
    return any(t in cat for t in termos)


def _is_categoria_contrib_sede(categoria: Any) -> bool:
    cat = _categoria_norm(categoria)
    return cat in ("contrib. sede", "repasse à sede", "repasse a sede")


_RE_DESC_30_ASSINATURA = re.compile(r"^\d{1,3}%\s+Administrativo\s+-\s+Conselho\s+Sede\s+(0[1-9]|1[0-2])/\d{4}$", re.IGNORECASE)
_RE_DESC_DESPESA_FIXA_ASSINATURA = re.compile(r"^.+\s+-\s+Despesa\s+Fixa\s+(0[1-9]|1[0-2])/\d{4}$", re.IGNORECASE)


def _is_descricao_30_assinatura(descricao: Any) -> bool:
    d = _to_str(descricao).strip()
    return bool(_RE_DESC_30_ASSINATURA.match(d))


def _is_descricao_despesa_fixa_assinatura(descricao: Any) -> bool:
    d = _to_str(descricao).strip()
    return bool(_RE_DESC_DESPESA_FIXA_ASSINATURA.match(d))


def _is_data_primeiro_dia(data_valor: Any) -> bool:
    d = _to_date(data_valor)
    return d is not None and d.day == 1


def _is_conta_dinheiro(conta: Any) -> bool:
    return _to_str(conta).strip().lower() == "dinheiro"


def eh_obrigacao_30_automatica(lancamento: dict) -> bool:
    # Assinatura comprovada de gerar_lancamento_administrativo()
    return all(
        [
            _origem_norm(lancamento.get("origem")) == "automatico",
            _tipo_norm(lancamento.get("tipo")) == "saida",
            _categoria_norm(lancamento.get("categoria")) == "contrib. sede",
            _is_conta_dinheiro(lancamento.get("conta")),
            _is_data_primeiro_dia(lancamento.get("data")),
            _is_descricao_30_assinatura(lancamento.get("descricao")),
        ]
    )


def eh_obrigacao_despesa_fixa_automatica(lancamento: dict) -> bool:
    # Assinatura comprovada de gerar_lancamentos_despesas_fixas()
    return all(
        [
            _origem_norm(lancamento.get("origem")) == "automatico",
            _tipo_norm(lancamento.get("tipo")) == "saida",
            _is_conta_dinheiro(lancamento.get("conta")),
            _is_data_primeiro_dia(lancamento.get("data")),
            _is_descricao_despesa_fixa_assinatura(lancamento.get("descricao")),
            not eh_obrigacao_30_automatica(lancamento),
        ]
    )


def classificar_lancamento_automatico(lancamento: dict) -> str:
    if _origem_norm(lancamento.get("origem")) != "automatico":
        return "NAO_AUTOMATICO"
    if eh_obrigacao_30_automatica(lancamento):
        return "A_30_ADMINISTRATIVO_COMPROVADO"
    if eh_obrigacao_despesa_fixa_automatica(lancamento):
        return "B_DESPESA_FIXA_OBRIGACAO_COMPROVADA"
    return "AUTOMATICO_NAO_CLASSIFICADO_COM_SEGURANCA"


def _rodar_testes_sinteticos_classificador():
    casos = {
        "CASO_A": {
            "id": "A",
            "data": date(2026, 8, 1),
            "tipo": "Saída",
            "categoria": "DESP. FIXAS",
            "descricao": "Internet Sede - Despesa Fixa 08/2026",
            "valor": 150.0,
            "conta": "Dinheiro",
            "origem": "automatico",
            "projeto_id": None,
        },
        "CASO_B": {
            "id": "B",
            "data": date(2026, 8, 1),
            "tipo": "Saída",
            "categoria": "DESP. FIXAS",
            "descricao": "Internet Sede - Pagamento avulso 08/2026",
            "valor": 150.0,
            "conta": "Dinheiro",
            "origem": "automatico",
            "projeto_id": None,
        },
        "CASO_C": {
            "id": "C",
            "data": date(2026, 8, 15),
            "tipo": "Saída",
            "categoria": "DESP. FIXAS",
            "descricao": "Internet Sede - Despesa Fixa 08/2026",
            "valor": 150.0,
            "conta": "Banco",
            "origem": "automatico",
            "projeto_id": None,
        },
        "CASO_D": {
            "id": "D",
            "data": date(2026, 8, 1),
            "tipo": "Saída",
            "categoria": "DESP. FIXAS",
            "descricao": "Internet Sede - Despesa Fixa 08/2026",
            "valor": 150.0,
            "conta": "Dinheiro",
            "origem": "manual",
            "projeto_id": None,
        },
        "CASO_E": {
            "id": "E",
            "data": date(2026, 8, 1),
            "tipo": "Saída",
            "categoria": "REPASSE À SEDE",
            "descricao": "Repasse à Sede - Competência 08/2026",
            "valor": 700.0,
            "conta": "Dinheiro",
            "origem": "automatico",
            "projeto_id": None,
        },
        "CASO_F": {
            "id": "F",
            "data": date(2026, 8, 1),
            "tipo": "Saída",
            "categoria": "CONTRIB. SEDE",
            "descricao": "30% Administrativo - Conselho Sede 08/2026",
            "valor": 900.0,
            "conta": "Dinheiro",
            "origem": "automatico",
            "projeto_id": None,
        },
    }

    print("\nPARTE 6B - TESTES SINTETICOS DO CLASSIFICADOR (EM MEMORIA)")
    resultados = {}
    for nome, registro in casos.items():
        resultados[nome] = classificar_lancamento_automatico(registro)
        print(f"{nome}: {resultados[nome]}")

    return resultados


def _similaridade(a: Any, b: Any) -> float:
    return SequenceMatcher(None, _to_str(a).lower(), _to_str(b).lower()).ratio()


def _fmt_money(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fetch_all(conn, sql: str, params: dict | None = None) -> list[dict]:
    rows = conn.execute(text(sql), params or {}).mappings().all()
    return [dict(r) for r in rows]


def _pick_config_table(table_names: set[str]) -> str | None:
    preferidas = ["configuracoes_igreja", "configuracoes"]
    for t in preferidas:
        if t in table_names:
            return t
    for t in sorted(table_names):
        if "configur" in t:
            return t
    return None


def _safe_col(table_cols: set[str], col: str) -> bool:
    return col in table_cols


def _print_group_records(title: str, rows: list[dict]):
    print(f"\n{title}")
    if not rows:
        print("SEM REGISTROS")
        return
    for r in rows:
        print(
            " | ".join(
                [
                    f"id={r.get('id')}",
                    f"data={r.get('data')}",
                    f"tipo={r.get('tipo')}",
                    f"categoria={r.get('categoria')}",
                    f"descricao={r.get('descricao')}",
                    f"valor={_fmt_money(_to_float(r.get('valor')))}",
                    f"conta={r.get('conta')}",
                    f"origem={r.get('origem')}",
                    f"conciliado={r.get('conciliado')}",
                    f"criado_em={r.get('criado_em')}",
                    f"documento_ref={r.get('documento_ref')}",
                    f"projeto_id={r.get('projeto_id')}",
                ]
            )
        )


def _slice_old_new(rows: list[dict], limit: int = 100) -> list[dict]:
    if len(rows) <= limit:
        return rows
    ordered = sorted(rows, key=lambda x: (_to_date(x.get("data")) or date.min, x.get("id") or 0))
    old = ordered[:50]
    new = ordered[-50:]
    return old + new


def _fmt_date(value: Any) -> str:
    d = _to_date(value)
    if d is None:
        return ""
    return d.strftime("%Y-%m-%d")


def _fmt_datetime(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return _to_str(value)


def _fmt_cell(value: Any) -> str:
    if isinstance(value, bool):
        return "SIM" if value else "NAO"
    if isinstance(value, (datetime, date)):
        return _fmt_datetime(value)
    if isinstance(value, float):
        return f"{value:.2f}"
    return _to_str(value)


def _table_exists(insp, table_name: str) -> bool:
    return table_name in set(insp.get_table_names())


def _table_columns(insp, table_name: str) -> set[str]:
    if not _table_exists(insp, table_name):
        return set()
    return {col["name"] for col in insp.get_columns(table_name)}


def _select_table_rows(conn, insp, table_name: str, wanted_columns: list[str], order_by: str = "id", where_sql: str = "", params: dict | None = None) -> tuple[list[dict], list[str]]:
    columns = _table_columns(insp, table_name)
    if not columns:
        return [], []

    selected = [column for column in wanted_columns if column in columns]
    if order_by and order_by in columns and order_by not in selected:
        selected.append(order_by)
    if not selected:
        return [], []

    sql = f"SELECT {', '.join(selected)} FROM {table_name}"
    if where_sql:
        sql += f" WHERE {where_sql}"
    if order_by and order_by in columns:
        sql += f" ORDER BY {order_by}"
    return _fetch_all(conn, sql, params), selected


def _print_table_rows(title: str, rows: list[dict], fields: list[str]):
    print(f"\n{title}")
    if not rows:
        print("SEM REGISTROS")
        return
    for row in rows:
        partes = []
        for field in fields:
            partes.append(f"{field}={_fmt_cell(row.get(field))}")
        print(" | ".join(partes))


def _classificar_candidato_envio_lancamento(envio: dict, lancamento: dict | None) -> tuple[str, str]:
    if lancamento is None:
        return "SEM_CORRESPONDENCIA", "nenhum lançamento vinculado ou candidato encontrado"

    score = 0.0
    motivos = []

    lancamento_id = envio.get("lancamento_financeiro_id")
    if lancamento_id and lancamento_id == lancamento.get("id"):
        score += 0.60
        motivos.append("lancamento_financeiro_id")

    valor_envio = _to_float(envio.get("valor_total")) if envio.get("valor_total") is not None else _to_float(envio.get("valor"))
    valor_lancamento = _to_float(lancamento.get("valor"))
    if abs(valor_envio - valor_lancamento) <= 0.01:
        score += 0.20
        motivos.append("valor exato")

    data_envio = _to_date(envio.get("data_pagamento")) or _to_date(envio.get("data"))
    data_lancamento = _to_date(lancamento.get("data"))
    if data_envio and data_lancamento:
        diff_dias = abs((data_envio - data_lancamento).days)
        if diff_dias <= 3:
            score += 0.10
            motivos.append("data próxima")
        elif diff_dias <= 7:
            score += 0.05
            motivos.append("data razoavelmente próxima")

    desc_envio = _to_str(envio.get("observacao")) + " " + _to_str(envio.get("competencia"))
    desc_lancamento = _to_str(lancamento.get("descricao")) + " " + _to_str(lancamento.get("observacoes"))
    sim_desc = SequenceMatcher(None, desc_envio.lower(), desc_lancamento.lower()).ratio()
    if sim_desc >= 0.75:
        score += 0.08
        motivos.append("descrição semelhante")

    documento_envio = _to_str(envio.get("comprovante"))
    documento_lancamento = _to_str(lancamento.get("documento_ref"))
    if documento_envio and documento_lancamento and documento_envio == documento_lancamento:
        score += 0.10
        motivos.append("documento_ref coincidente")

    origem_lancamento = _origem_norm(lancamento.get("origem"))
    conta_lancamento = _to_str(lancamento.get("conta")).strip().lower()
    if origem_lancamento in ("manual", "importado", "automatico"):
        score += 0.02
        motivos.append(f"origem={origem_lancamento}")
    if conta_lancamento in ("dinheiro", "banco", "pix"):
        score += 0.01
        motivos.append(f"conta={conta_lancamento}")

    if score >= 0.80:
        confidence = "ALTA"
    elif score >= 0.50:
        confidence = "MEDIA"
    elif score > 0:
        confidence = "BAIXA"
    else:
        confidence = "SEM_CORRESPONDENCIA"

    motivo = "; ".join(motivos) if motivos else "sem critérios fortes"
    return confidence, motivo


def _build_envio_match_rows(conn, insp, envios: list[dict], lancamentos: list[dict]) -> list[dict]:
    lanc_by_id = {l.get("id"): l for l in lancamentos}
    rows = []
    for envio in sorted(envios, key=lambda e: e.get("id") or 0):
        lancamento_vinculado = lanc_by_id.get(envio.get("lancamento_financeiro_id")) if envio.get("lancamento_financeiro_id") else None
        if lancamento_vinculado is not None:
            confidence, motivo = _classificar_candidato_envio_lancamento(envio, lancamento_vinculado)
            rows.append({
                "ENVIO_ID": envio.get("id"),
                "COMPETENCIA": envio.get("competencia"),
                "VALOR_ENVIO": _to_float(envio.get("valor_total")) if envio.get("valor_total") is not None else _to_float(envio.get("valor")),
                "TIPO_PAGAMENTO": envio.get("tipo_pagamento"),
                "HISTORICO_SEM_MOVIMENTO": _bool_norm(envio.get("pagamento_historico_sem_movimentacao")),
                "LANCAMENTO_FINANCEIRO_ID": envio.get("lancamento_financeiro_id"),
                "CANDIDATO_LANCAMENTO_ID": lancamento_vinculado.get("id"),
                "VALOR_CANDIDATO": _to_float(lancamento_vinculado.get("valor")),
                "DATA_CANDIDATO": lancamento_vinculado.get("data"),
                "ORIGEM_CANDIDATO": lancamento_vinculado.get("origem"),
                "CONFIANCA": confidence,
                "MOTIVO": motivo,
            })
            continue

        valor_envio = _to_float(envio.get("valor_total")) if envio.get("valor_total") is not None else _to_float(envio.get("valor"))
        data_envio = _to_date(envio.get("data_pagamento"))
        candidatos = []
        for lancamento in lancamentos:
            if _tipo_norm(lancamento.get("tipo")) != "saida":
                continue
            valor_lancamento = _to_float(lancamento.get("valor"))
            data_lancamento = _to_date(lancamento.get("data"))
            documento_lancamento = _to_str(lancamento.get("documento_ref"))
            descricao_lancamento = _to_str(lancamento.get("descricao"))
            observacoes_lancamento = _to_str(lancamento.get("observacoes"))
            origem_lancamento = _origem_norm(lancamento.get("origem"))
            conta_lancamento = _to_str(lancamento.get("conta")).strip().lower()

            pontuacao = 0.0
            motivos = []
            if abs(valor_envio - valor_lancamento) <= 0.01:
                pontuacao += 0.50
                motivos.append("valor exato")
            elif abs(valor_envio - valor_lancamento) <= max(1.0, valor_envio * 0.02):
                pontuacao += 0.25
                motivos.append("valor próximo")

            if data_envio and data_lancamento:
                diff_dias = abs((data_envio - data_lancamento).days)
                if diff_dias <= 3:
                    pontuacao += 0.20
                    motivos.append("data próxima")
                elif diff_dias <= 7:
                    pontuacao += 0.10
                    motivos.append("data razoável")

            texto_envio = (_to_str(envio.get("competencia")) + " " + _to_str(envio.get("observacao"))).lower()
            texto_lancamento = (descricao_lancamento + " " + observacoes_lancamento).lower()
            similaridade = SequenceMatcher(None, texto_envio, texto_lancamento).ratio()
            if similaridade >= 0.70:
                pontuacao += 0.15
                motivos.append("descrição semelhante")

            if documento_lancamento and _to_str(envio.get("comprovante")) and documento_lancamento == _to_str(envio.get("comprovante")):
                pontuacao += 0.10
                motivos.append("documento_ref")

            if origem_lancamento in ("manual", "importado", "automatico"):
                pontuacao += 0.03
                motivos.append(f"origem={origem_lancamento}")
            if conta_lancamento in ("dinheiro", "banco", "pix"):
                pontuacao += 0.02
                motivos.append(f"conta={conta_lancamento}")

            if pontuacao >= 0.75:
                confidence = "ALTA"
            elif pontuacao >= 0.45:
                confidence = "MEDIA"
            elif pontuacao > 0:
                confidence = "BAIXA"
            else:
                confidence = "SEM_CORRESPONDENCIA"

            candidatos.append((pontuacao, lancamento, confidence, "; ".join(motivos) if motivos else "sem critérios fortes"))

        if candidatos:
            candidatos.sort(key=lambda item: item[0], reverse=True)
            melhor = candidatos[0]
            lancamento = melhor[1]
            confidence = melhor[2]
            motivo = melhor[3]
            rows.append({
                "ENVIO_ID": envio.get("id"),
                "COMPETENCIA": envio.get("competencia"),
                "VALOR_ENVIO": valor_envio,
                "TIPO_PAGAMENTO": envio.get("tipo_pagamento"),
                "HISTORICO_SEM_MOVIMENTO": _bool_norm(envio.get("pagamento_historico_sem_movimentacao")),
                "LANCAMENTO_FINANCEIRO_ID": envio.get("lancamento_financeiro_id"),
                "CANDIDATO_LANCAMENTO_ID": lancamento.get("id"),
                "VALOR_CANDIDATO": _to_float(lancamento.get("valor")),
                "DATA_CANDIDATO": lancamento.get("data"),
                "ORIGEM_CANDIDATO": lancamento.get("origem"),
                "CONFIANCA": confidence,
                "MOTIVO": motivo,
            })
        else:
            rows.append({
                "ENVIO_ID": envio.get("id"),
                "COMPETENCIA": envio.get("competencia"),
                "VALOR_ENVIO": valor_envio,
                "TIPO_PAGAMENTO": envio.get("tipo_pagamento"),
                "HISTORICO_SEM_MOVIMENTO": _bool_norm(envio.get("pagamento_historico_sem_movimentacao")),
                "LANCAMENTO_FINANCEIRO_ID": envio.get("lancamento_financeiro_id"),
                "CANDIDATO_LANCAMENTO_ID": None,
                "VALOR_CANDIDATO": None,
                "DATA_CANDIDATO": None,
                "ORIGEM_CANDIDATO": None,
                "CONFIANCA": "SEM_CORRESPONDENCIA",
                "MOTIVO": "nenhum candidato encontrado",
            })

    return rows


def main():
    database_url = os.environ.get("DATABASE_URL")

    print("=== AUDITORIA FINANCEIRO PRODUÇÃO ===")
    print("DIALETO:", end=" ")
    print("DESCONHECIDO" if not database_url else "(A VALIDAR)")
    print("DATABASE_URL_DEFINIDA:", "SIM" if database_url else "NAO")
    print("MODO: SOMENTE LEITURA")

    if not database_url:
        print("AUDITORIA CANCELADA: DATABASE_URL NÃO DEFINIDA")
        return

    engine = create_engine(database_url, pool_pre_ping=True, future=True)

    if engine.dialect.name != "postgresql":
        print("DIALETO:", engine.dialect.name)
        print("AUDITORIA CANCELADA: BANCO NÃO É POSTGRESQL")
        return

    print("DIALETO:", engine.dialect.name)

    with engine.connect() as conn:
        tx = conn.begin()
        conn.execute(text("SET TRANSACTION READ ONLY"))

        insp = inspect(conn)
        table_names = set(insp.get_table_names())

        print("\nPARTE 1 - IDENTIFICACAO DO BANCO")
        esperadas = [
            "lancamentos",
            "envios_sede",
            "despesas_fixas_conselho",
            "projetos",
            "conciliacao_pares",
            "configuracoes_igreja",
            "configuracoes",
        ]
        for t in esperadas:
            print(f"TABELA {t}:", "EXISTE" if t in table_names else "NAO EXISTE")

        if "lancamentos" not in table_names:
            print("AUDITORIA CANCELADA: TABELA lancamentos AUSENTE")
            tx.rollback()
            return

        lanc_cols = {c["name"] for c in insp.get_columns("lancamentos")}

        lanc_sql = """
        SELECT
            id,
            data,
            tipo,
            categoria,
            descricao,
            valor,
            conta,
            origem,
            conciliado,
            criado_em,
            documento_ref,
            projeto_id
        FROM lancamentos
        """
        lancamentos = _fetch_all(conn, lanc_sql)
        envios: list[dict] = []
        pares: list[dict] = []
        envios_cols: set[str] = set()
        pares_cols: set[str] = set()

        print("\nPARTE 2 - TOTAL DE LANCAMENTOS")
        total_lancamentos = len(lancamentos)
        print("TOTAL_LANCAMENTOS:", total_lancamentos)

        # Agrupamentos solicitados
        def _agrupa_dim(campo: str):
            agg = defaultdict(lambda: {"qtd": 0, "soma": 0.0, "entradas": 0.0, "saidas": 0.0})
            for l in lancamentos:
                k = l.get(campo)
                if k is None or _to_str(k).strip() == "":
                    k = "<NULL>"
                valor = _to_float(l.get("valor"))
                tipo_n = _tipo_norm(l.get("tipo"))
                agg[k]["qtd"] += 1
                agg[k]["soma"] += valor
                if tipo_n == "entrada":
                    agg[k]["entradas"] += valor
                elif tipo_n == "saida":
                    agg[k]["saidas"] += valor
            return agg

        for dim in ["tipo", "origem", "categoria", "conta", "conciliado"]:
            print(f"\nAGRUPAMENTO POR {dim.upper()}:")
            agg = _agrupa_dim(dim)
            for k in sorted(agg.keys(), key=lambda x: str(x).lower()):
                v = agg[k]
                print(
                    f"{k} | QUANTIDADE={v['qtd']} | SOMA={_fmt_money(v['soma'])} | "
                    f"ENTRADAS={_fmt_money(v['entradas'])} | SAIDAS={_fmt_money(v['saidas'])}"
                )

        # Por origem conforme exemplo
        print("\nRESUMO POR ORIGEM:")
        origem_agg = _agrupa_dim("origem")
        for origem in ["manual", "importado", "automatico", "<NULL>"]:
            if origem not in origem_agg:
                continue
            v = origem_agg[origem]
            print(f"ORIGEM {origem}:")
            print(f"QUANTIDADE: {v['qtd']}")
            print(f"ENTRADAS: {_fmt_money(v['entradas'])}")
            print(f"SAIDAS: {_fmt_money(v['saidas'])}")

        print("\nPARTE 3 - LANCAMENTOS AUTOMATICOS")
        automaticos = [l for l in lancamentos if _origem_norm(l.get("origem")) == "automatico"]

        grupos_auto = {
            "A_30_ADMINISTRATIVO_COMPROVADO": [],
            "B_DESPESA_FIXA_OBRIGACAO_COMPROVADA": [],
            "AUTOMATICO_NAO_CLASSIFICADO_COM_SEGURANCA": [],
        }

        for l in automaticos:
            grupo = classificar_lancamento_automatico(l)
            if grupo != "NAO_AUTOMATICO":
                grupos_auto[grupo].append(l)

        for nome, rows in grupos_auto.items():
            if rows:
                datas = sorted([_to_date(r.get("data")) for r in rows if _to_date(r.get("data")) is not None])
                contas = sorted(set([_to_str(r.get("conta")) or "<NULL>" for r in rows]))
                soma = sum(_to_float(r.get("valor")) for r in rows)
                print(f"\n{nome}:")
                print(f"quantidade={len(rows)}")
                print(f"menor_data={datas[0] if datas else None}")
                print(f"maior_data={datas[-1] if datas else None}")
                print(f"soma_total={_fmt_money(soma)}")
                print(f"contas_utilizadas={', '.join(contas)}")
            else:
                print(f"\n{nome}: quantidade=0")

            rows_to_print = _slice_old_new(rows, 100)
            _print_group_records(f"REGISTROS {nome} (ATE 100)", rows_to_print)

        # Casos sintéticos para validar os classificadores sem acessar banco de produção
        resultados_sinteticos = _rodar_testes_sinteticos_classificador()

        print("\nPARTE 4 - CONTRIBUICAO ADMINISTRATIVA AUTOMATICA")

        contrib_auto = []
        contrib_manual = []

        for l in lancamentos:
            tipo_n = _tipo_norm(l.get("tipo"))
            if tipo_n != "saida":
                continue
            cat = l.get("categoria")
            desc = l.get("descricao")
            ori = _origem_norm(l.get("origem"))

            if ori == "automatico" and eh_obrigacao_30_automatica(l):
                contrib_auto.append(l)
                continue

            is_contrib_like = _is_categoria_contrib_sede(cat) or _is_descricao_30_assinatura(desc)
            if ori == "manual" and is_contrib_like:
                contrib_manual.append(l)

        envios = []
        envios_cols = set()
        if "envios_sede" in table_names:
            envios_cols = {c["name"] for c in insp.get_columns("envios_sede")}
            envios = _fetch_all(conn, "SELECT * FROM envios_sede")

        lanc_by_id = {l.get("id"): l for l in lancamentos}

        repasse_real = []
        for e in envios:
            hist = _bool_norm(e.get("pagamento_historico_sem_movimentacao"))
            lanc_id = e.get("lancamento_financeiro_id")
            if hist:
                continue
            if lanc_id is None:
                continue
            l = lanc_by_id.get(lanc_id)
            if l is not None:
                repasse_real.append(l)

        def _sumario_grupo(nome: str, rows: list[dict]):
            print(f"\n{nome}:")
            print("quantidade:", len(rows))
            print("soma:", _fmt_money(sum(_to_float(r.get("valor")) for r in rows)))
            ds = sorted([_to_date(r.get("data")) for r in rows if _to_date(r.get("data")) is not None])
            print("periodo:", f"{ds[0]} ate {ds[-1]}" if ds else "-")
            print("conta:", ", ".join(sorted(set((_to_str(r.get("conta")) or "<NULL>") for r in rows))) if rows else "-")
            print("origem:", ", ".join(sorted(set((_to_str(r.get("origem")) or "<NULL>") for r in rows))) if rows else "-")

        _sumario_grupo("CONTRIB_SEDE_AUTOMATICO", contrib_auto)
        _sumario_grupo("CONTRIB_SEDE_MANUAL", contrib_manual)
        _sumario_grupo("REPASSE_SEDE_REAL", repasse_real)

        print("\nPARTE 5 - REPASSES REAIS A SEDE")
        if "envios_sede" not in table_names:
            print("Tabela envios_sede nao existe")
        else:
            classificacoes = {
                "A_PAGAMENTO_REAL_COM_LANCAMENTO": [],
                "B_HISTORICO_SEM_MOVIMENTACAO": [],
                "C_REGISTRO_SEM_VINCULO_INESPERADO": [],
                "D_VINCULO_PARA_LANCAMENTO_INEXISTENTE": [],
            }

            divergencias = []
            for e in sorted(envios, key=lambda x: (x.get("data_pagamento") or date.min, x.get("id") or 0)):
                lanc_id = e.get("lancamento_financeiro_id")
                hist = _bool_norm(e.get("pagamento_historico_sem_movimentacao"))
                vinculado = lanc_by_id.get(lanc_id) if lanc_id is not None else None

                if hist:
                    if lanc_id is None:
                        classificacoes["B_HISTORICO_SEM_MOVIMENTACAO"].append(e)
                    else:
                        classificacoes["D_VINCULO_PARA_LANCAMENTO_INEXISTENTE"].append(e)
                else:
                    if lanc_id is None:
                        classificacoes["C_REGISTRO_SEM_VINCULO_INESPERADO"].append(e)
                    elif vinculado is None:
                        classificacoes["D_VINCULO_PARA_LANCAMENTO_INEXISTENTE"].append(e)
                    else:
                        classificacoes["A_PAGAMENTO_REAL_COM_LANCAMENTO"].append(e)

                        valor_envio = _to_float(e.get("valor_total")) if e.get("valor_total") is not None else _to_float(e.get("valor"))
                        valor_lanc = _to_float(vinculado.get("valor"))
                        data_envio = _to_date(e.get("data_pagamento"))
                        data_lanc = _to_date(vinculado.get("data"))

                        if abs(valor_envio - valor_lanc) > 0.01:
                            divergencias.append(
                                {
                                    "envio_id": e.get("id"),
                                    "lanc_id": vinculado.get("id"),
                                    "valor_envio": valor_envio,
                                    "valor_lanc": valor_lanc,
                                    "data_envio": data_envio,
                                    "data_lanc": data_lanc,
                                    "categoria": vinculado.get("categoria"),
                                    "conta": vinculado.get("conta"),
                                }
                            )

                print(
                    " | ".join(
                        [
                            f"id={e.get('id')}",
                            f"data_pagamento={e.get('data_pagamento')}",
                            f"competencia={e.get('competencia')}",
                            f"valor={e.get('valor')}",
                            f"valor_total={e.get('valor_total')}",
                            f"valor_administrativo={e.get('valor_administrativo')}",
                            f"valor_despesas_fixas={e.get('valor_despesas_fixas')}",
                            f"tipo_pagamento={e.get('tipo_pagamento')}",
                            f"pagamento_historico_sem_movimentacao={e.get('pagamento_historico_sem_movimentacao')}",
                            f"lancamento_financeiro_id={e.get('lancamento_financeiro_id')}",
                            f"created_at={e.get('created_at')}",
                        ]
                    )
                )

            for nome, rows in classificacoes.items():
                print(f"{nome}: {len(rows)}")

            print("\nDIVERGENCIAS ENVIO x LANCAMENTO (> R$ 0,01):")
            if not divergencias:
                print("SEM DIVERGENCIAS")
            else:
                for d in divergencias:
                    print(
                        f"envio_id={d['envio_id']} | lanc_id={d['lanc_id']} | "
                        f"valor_envio={_fmt_money(d['valor_envio'])} | valor_lanc={_fmt_money(d['valor_lanc'])} | "
                        f"data_envio={d['data_envio']} | data_lanc={d['data_lanc']} | "
                        f"categoria={d['categoria']} | conta={d['conta']}"
                    )

        print("\nPARTE 6 - DESPESAS FIXAS AUTOMATICAS")
        despesas_fixas_auto = grupos_auto["B_DESPESA_FIXA_OBRIGACAO_COMPROVADA"]
        for l in despesas_fixas_auto:
            print(
                f"id={l.get('id')} | data={l.get('data')} | categoria={l.get('categoria')} | "
                f"descricao={l.get('descricao')} | valor={_fmt_money(_to_float(l.get('valor')))} | "
                f"conta={l.get('conta')} | origem={l.get('origem')} | conciliado={l.get('conciliado')}"
            )

        # Buscar candidatos de possivel dupla representacao
        saidas_nao_auto = [
            l
            for l in lancamentos
            if _tipo_norm(l.get("tipo")) == "saida" and _origem_norm(l.get("origem")) != "automatico"
        ]

        candidatos_alta = []
        candidatos_media = []
        sem_evidencia = 0

        print("\nCRITERIOS_CANDIDATOS:")
        print("ALTA: |valor_a - valor_b| <= 0,01 E similaridade_descricao >= 0,75 E distancia_dias <= 3")
        print("MEDIA: diferenca_valor <= max(1,00; 2%) E similaridade_descricao >= 0,45 E distancia_dias <= 7")

        for auto in despesas_fixas_auto:
            best = None
            auto_data = _to_date(auto.get("data"))
            auto_valor = _to_float(auto.get("valor"))
            auto_desc = auto.get("descricao")
            auto_cat = auto.get("categoria")

            for cand in saidas_nao_auto:
                cand_data = _to_date(cand.get("data"))
                if auto_data is None or cand_data is None:
                    continue
                dias = abs((cand_data - auto_data).days)
                if dias > 7:
                    continue

                cand_valor = _to_float(cand.get("valor"))
                diff = abs(cand_valor - auto_valor)
                sim_desc = _similaridade(auto_desc, cand.get("descricao"))
                sim_cat = _similaridade(auto_cat, cand.get("categoria"))
                sim = max(sim_desc, sim_cat)

                nivel = None
                if diff <= 0.01 and sim_desc >= 0.75 and dias <= 3:
                    nivel = "ALTA"
                else:
                    tol = max(1.0, auto_valor * 0.02)
                    if diff <= tol and sim >= 0.45 and dias <= 7:
                        nivel = "MEDIA"

                if nivel is None:
                    continue

                score = (1.0 - min(1.0, diff / max(1.0, auto_valor))) * 0.5 + sim * 0.4 + (1.0 - min(1.0, dias / 7.0)) * 0.1
                item = {
                    "auto": auto,
                    "cand": cand,
                    "nivel": nivel,
                    "diff": diff,
                    "dias": dias,
                    "sim_desc": sim_desc,
                    "sim_cat": sim_cat,
                    "score": score,
                }
                if best is None or item["score"] > best["score"]:
                    best = item

            if best is None:
                sem_evidencia += 1
            elif best["nivel"] == "ALTA":
                candidatos_alta.append(best)
            else:
                candidatos_media.append(best)

        print(f"CANDIDATO_DUPLICIDADE_ALTA: {len(candidatos_alta)}")
        print(f"CANDIDATO_DUPLICIDADE_MEDIA: {len(candidatos_media)}")
        print(f"SEM_EVIDENCIA: {sem_evidencia}")

        for bloco, nome in [(candidatos_alta, "ALTA"), (candidatos_media, "MEDIA")]:
            if not bloco:
                continue
            print(f"\nLISTA_CANDIDATOS_{nome}:")
            for item in bloco[:200]:
                a = item["auto"]
                c = item["cand"]
                print(
                    f"auto_id={a.get('id')} cand_id={c.get('id')} | "
                    f"auto_data={a.get('data')} cand_data={c.get('data')} | "
                    f"auto_valor={_fmt_money(_to_float(a.get('valor')))} cand_valor={_fmt_money(_to_float(c.get('valor')))} | "
                    f"diff={_fmt_money(item['diff'])} dias={item['dias']} sim_desc={item['sim_desc']:.2f} sim_cat={item['sim_cat']:.2f}"
                )

        print("\nPARTE 7 - SALDO ATUAL DO ERP")
        config_table = _pick_config_table(table_names)
        saldo_inicial = 0.0
        if config_table is not None:
            cfg_cols = {c["name"] for c in insp.get_columns(config_table)}
            if _safe_col(cfg_cols, "saldo_inicial"):
                cfg_rows = _fetch_all(conn, f"SELECT saldo_inicial FROM {config_table} ORDER BY id ASC LIMIT 1")
                if cfg_rows:
                    saldo_inicial = _to_float(cfg_rows[0].get("saldo_inicial"))

        total_entradas_erp = sum(_to_float(l.get("valor")) for l in lancamentos if _tipo_norm(l.get("tipo")) == "entrada")
        total_saidas_erp = sum(_to_float(l.get("valor")) for l in lancamentos if _tipo_norm(l.get("tipo")) == "saida")
        saldo_erp = saldo_inicial + total_entradas_erp - total_saidas_erp

        total_saidas_relatorio = sum(
            _to_float(l.get("valor"))
            for l in lancamentos
            if _tipo_norm(l.get("tipo")) == "saida" and not _is_destinacao(l.get("categoria"))
        )
        saldo_relatorio = saldo_inicial + total_entradas_erp - total_saidas_relatorio

        print("SALDO_INICIAL:", _fmt_money(saldo_inicial))
        print("TOTAL_ENTRADAS_ERP:", _fmt_money(total_entradas_erp))
        print("TOTAL_SAIDAS_ERP:", _fmt_money(total_saidas_erp))
        print("SALDO_ERP:", _fmt_money(saldo_erp))
        print("TOTAL_SAIDAS_RELATORIO:", _fmt_money(total_saidas_relatorio))
        print("SALDO_RELATORIO:", _fmt_money(saldo_relatorio))

        print("\nPARTE 8 - SALDO DE CAIXA REAL INVESTIGATIVO")
        obrigacoes_auto = grupos_auto["A_30_ADMINISTRATIVO_COMPROVADO"] + grupos_auto["B_DESPESA_FIXA_OBRIGACAO_COMPROVADA"]
        saidas_automaticas_obrigacao = sum(
            _to_float(l.get("valor"))
            for l in obrigacoes_auto
            if _tipo_norm(l.get("tipo")) == "saida"
        )

        total_saidas_caixa_real_simulado = total_saidas_erp - saidas_automaticas_obrigacao
        saldo_caixa_real_simulado = saldo_inicial + total_entradas_erp - total_saidas_caixa_real_simulado
        diferenca_erp_vs_simulado = saldo_caixa_real_simulado - saldo_erp

        print("SAIDAS_AUTOMATICAS_OBRIGACAO:", _fmt_money(saidas_automaticas_obrigacao))
        print("TOTAL_SAIDAS_CAIXA_REAL_SIMULADO:", _fmt_money(total_saidas_caixa_real_simulado))
        print("SALDO_CAIXA_REAL_SIMULADO:", _fmt_money(saldo_caixa_real_simulado))
        print("DIFERENCA_SALDO_ERP_VS_SIMULADO:", _fmt_money(diferenca_erp_vs_simulado))

        print("\nPARTE 9 - QUEBRA DA DIFERENCA")
        impacto_30 = sum(_to_float(l.get("valor")) for l in grupos_auto["A_30_ADMINISTRATIVO_COMPROVADO"] if _tipo_norm(l.get("tipo")) == "saida")
        impacto_desp_fixas = sum(_to_float(l.get("valor")) for l in grupos_auto["B_DESPESA_FIXA_OBRIGACAO_COMPROVADA"] if _tipo_norm(l.get("tipo")) == "saida")
        impacto_outros = 0.0
        diferenca_total = impacto_30 + impacto_desp_fixas + impacto_outros

        automaticos_nao_classificados = grupos_auto["AUTOMATICO_NAO_CLASSIFICADO_COM_SEGURANCA"]
        automaticos_nao_classificados_valor = sum(
            _to_float(l.get("valor")) for l in automaticos_nao_classificados if _tipo_norm(l.get("tipo")) == "saida"
        )

        print("AUTOMATICOS_NAO_CLASSIFICADOS:", len(automaticos_nao_classificados))
        print("AUTOMATICOS_NAO_CLASSIFICADOS_VALOR:", _fmt_money(automaticos_nao_classificados_valor))

        print("IMPACTO_30_AUTOMATICO:", _fmt_money(impacto_30))
        print("IMPACTO_DESPESAS_FIXAS_AUTOMATICAS:", _fmt_money(impacto_desp_fixas))
        print("IMPACTO_OUTROS_AUTOMATICOS:", _fmt_money(impacto_outros))
        print("DIFERENCA_TOTAL:", _fmt_money(diferenca_total))

        bate_tolerancia = abs(diferenca_total - diferenca_erp_vs_simulado) <= 0.01
        print("VALIDACAO_IMPACTOS_EQ_DIFERENCA (tol R$ 0,01):", "OK" if bate_tolerancia else "DIVERGENTE")

        print("\nPARTE 10 - ANALISE POR MES")
        # Preparar meses com dados
        meses_set = set()
        for l in lancamentos:
            d = _to_date(l.get("data"))
            if d is not None:
                meses_set.add((d.year, d.month))

        # Garantir foco especial em 01..08/2026
        for m in range(1, 9):
            meses_set.add((2026, m))

        # Agregado de pagamentos reais sede por mes
        pagamentos_reais_sede_mes = defaultdict(float)
        for e in envios:
            hist = _bool_norm(e.get("pagamento_historico_sem_movimentacao"))
            if hist:
                continue
            d = _to_date(e.get("data_pagamento"))
            if d is None:
                continue
            valor = _to_float(e.get("valor_total")) if e.get("valor_total") is not None else _to_float(e.get("valor"))
            pagamentos_reais_sede_mes[(d.year, d.month)] += valor

        # Agregado de obrigacoes automaticas por mes
        obrigacoes_auto_mes = defaultdict(float)
        for l in obrigacoes_auto:
            d = _to_date(l.get("data"))
            if d is None:
                continue
            if _tipo_norm(l.get("tipo")) == "saida":
                obrigacoes_auto_mes[(d.year, d.month)] += _to_float(l.get("valor"))

        # Agregado ERP por mes
        entradas_mes = defaultdict(float)
        saidas_mes = defaultdict(float)
        for l in lancamentos:
            d = _to_date(l.get("data"))
            if d is None:
                continue
            key = (d.year, d.month)
            if _tipo_norm(l.get("tipo")) == "entrada":
                entradas_mes[key] += _to_float(l.get("valor"))
            elif _tipo_norm(l.get("tipo")) == "saida":
                saidas_mes[key] += _to_float(l.get("valor"))

        for ano, mes in sorted(meses_set):
            e_erp = entradas_mes[(ano, mes)]
            s_erp = saidas_mes[(ano, mes)]
            obrig = obrigacoes_auto_mes[(ano, mes)]
            pag_real = pagamentos_reais_sede_mes[(ano, mes)]
            s_sim = s_erp - obrig
            saldo_mes_erp = e_erp - s_erp
            saldo_mes_sim = e_erp - s_sim
            dif = saldo_mes_sim - saldo_mes_erp

            print(
                f"{mes:02d}/{ano} | ENTRADAS_ERP={_fmt_money(e_erp)} | SAIDAS_ERP={_fmt_money(s_erp)} | "
                f"OBRIGACOES_AUTOMATICAS={_fmt_money(obrig)} | PAGAMENTOS_REAIS_SEDE={_fmt_money(pag_real)} | "
                f"SAIDAS_CAIXA_REAL_SIMULADAS={_fmt_money(s_sim)} | SALDO_MES_ERP={_fmt_money(saldo_mes_erp)} | "
                f"SALDO_MES_SIMULADO={_fmt_money(saldo_mes_sim)} | DIFERENCA={_fmt_money(dif)}"
            )

        print("\nPARTE 11 - CONCILIACAO")
        stats_conc = {
            "manual_conciliado": 0,
            "manual_nao_conciliado": 0,
            "importado_conciliado": 0,
            "importado_nao_conciliado": 0,
            "automatico_conciliado": 0,
            "automatico_nao_conciliado": 0,
        }

        auto_conciliados = []
        for l in lancamentos:
            ori = _origem_norm(l.get("origem"))
            conc = _bool_norm(l.get("conciliado"))
            if ori in ("manual", "importado", "automatico"):
                chave = f"{ori}_{'conciliado' if conc else 'nao_conciliado'}"
                stats_conc[chave] += 1
            if ori == "automatico" and conc:
                auto_conciliados.append(l)

        print("manual nao conciliado:", stats_conc["manual_nao_conciliado"])
        print("manual conciliado:", stats_conc["manual_conciliado"])
        print("importado nao conciliado:", stats_conc["importado_nao_conciliado"])
        print("importado conciliado:", stats_conc["importado_conciliado"])
        print("automatico conciliado:", stats_conc["automatico_conciliado"])
        print("automatico nao conciliado:", stats_conc["automatico_nao_conciliado"])

        if auto_conciliados:
            print("\nLANCAMENTOS AUTOMATICOS CONCILIADOS:")
            for l in auto_conciliados[:200]:
                print(
                    f"id={l.get('id')} | data={l.get('data')} | tipo={l.get('tipo')} | categoria={l.get('categoria')} | "
                    f"descricao={l.get('descricao')} | valor={_fmt_money(_to_float(l.get('valor')))} | origem={l.get('origem')}"
                )

        pares_envolvendo_auto = []
        if "conciliacao_pares" in table_names:
            pares_cols = {c["name"] for c in insp.get_columns("conciliacao_pares")}
            if "lancamento_manual_id" in pares_cols and "lancamento_importado_id" in pares_cols:
                pares = _fetch_all(
                    conn,
                    "SELECT id, historico_id, lancamento_manual_id, lancamento_importado_id, score_similaridade, regra_aplicada, metodo_conciliacao, usuario, criado_em FROM conciliacao_pares",
                )
                for p in pares:
                    lm = lanc_by_id.get(p.get("lancamento_manual_id"))
                    li = lanc_by_id.get(p.get("lancamento_importado_id"))
                    o1 = _origem_norm(lm.get("origem")) if lm else "<nao_encontrado>"
                    o2 = _origem_norm(li.get("origem")) if li else "<nao_encontrado>"
                    if "automatico" in (o1, o2):
                        pares_envolvendo_auto.append((p, o1, o2))

        print("PARES_CONCILIACAO_ENVOLVENDO_AUTOMATICO:", len(pares_envolvendo_auto))
        for p, o1, o2 in pares_envolvendo_auto[:200]:
            print(
                f"par_id={p.get('id')} | manual_id={p.get('lancamento_manual_id')} origem_manual={o1} | "
                f"importado_id={p.get('lancamento_importado_id')} origem_importado={o2} | regra={p.get('regra_aplicada')}"
            )

        print("\nPARTE 12 - INCONSISTENCIAS ESTRUTURAIS")
        inconsistencias = {}

        inconsistencias["categoria_null"] = [l for l in lancamentos if _to_str(l.get("categoria")).strip() == ""]
        inconsistencias["conta_null"] = [l for l in lancamentos if _to_str(l.get("conta")).strip() == ""]
        inconsistencias["tipo_invalido"] = [
            l for l in lancamentos if _tipo_norm(l.get("tipo")) not in ("entrada", "saida")
        ]
        inconsistencias["valor_menor_ou_igual_zero"] = [l for l in lancamentos if _to_float(l.get("valor")) <= 0]
        inconsistencias["origem_null_ou_desconhecida"] = [
            l for l in lancamentos if _origem_norm(l.get("origem")) not in ("manual", "importado", "automatico")
        ]

        categorias_tipicas_saida = {
            "contrib. sede",
            "desp. fixas",
            "desp. variaveis",
            "desp. variáveis",
            "prebenda",
            "combustível",
            "combustivel",
            "ajuda custo",
            "contas",
            "credito cartao",
            "crédito cartão",
            "destinacao",
            "destinação",
            "gasto projeto",
            "repasse à sede",
            "repasse a sede",
        }
        categorias_tipicas_entrada = {
            "dízimo",
            "dizimo",
            "oferta",
            "oferta omn",
            "outras ofertas",
            "rendimentos",
        }

        inconsistencias["entrada_com_categoria_tipica_saida"] = [
            l
            for l in lancamentos
            if _tipo_norm(l.get("tipo")) == "entrada" and _categoria_norm(l.get("categoria")) in categorias_tipicas_saida
        ]
        inconsistencias["saida_com_categoria_tipica_entrada"] = [
            l
            for l in lancamentos
            if _tipo_norm(l.get("tipo")) == "saida" and _categoria_norm(l.get("categoria")) in categorias_tipicas_entrada
        ]

        inconsistencias["projeto_obrigatorio_sem_projeto_id"] = [
            l
            for l in lancamentos
            if _categoria_norm(l.get("categoria")) in ("destinação", "destinacao", "gasto projeto") and l.get("projeto_id") is None
        ]

        # Vinculos envio/lancamento incompativeis
        inc_lanc_envio_incomp = []
        inc_envio_real_sem_lanc = []
        inc_hist_com_lanc = []

        for e in envios:
            hist = _bool_norm(e.get("pagamento_historico_sem_movimentacao"))
            lanc_id = e.get("lancamento_financeiro_id")
            l = lanc_by_id.get(lanc_id) if lanc_id is not None else None

            if not hist and lanc_id is None:
                inc_envio_real_sem_lanc.append(e)
            if hist and lanc_id is not None:
                inc_hist_com_lanc.append(e)

            if l is not None:
                valor_env = _to_float(e.get("valor_total")) if e.get("valor_total") is not None else _to_float(e.get("valor"))
                valor_l = _to_float(l.get("valor"))
                tipo_l = _tipo_norm(l.get("tipo"))
                cat_l = _categoria_norm(l.get("categoria"))
                if abs(valor_env - valor_l) > 0.01 or tipo_l != "saida" or "repasse" not in cat_l:
                    inc_lanc_envio_incomp.append((e, l))

        inconsistencias["lancamento_vinculado_envio_incompativel"] = inc_lanc_envio_incomp
        inconsistencias["envio_real_sem_lancamento"] = inc_envio_real_sem_lanc
        inconsistencias["historico_sem_movimentacao_com_lancamento"] = inc_hist_com_lanc

        total_inconsistencias = 0
        for nome, itens in inconsistencias.items():
            qtd = len(itens)
            total_inconsistencias += qtd
            print(f"{nome}: {qtd}")

        # PARTE 13
        print("\nPARTE 13 - RESUMO FINAL")
        obrigacoes_30_total = impacto_30
        despesas_fixas_auto_total = impacto_desp_fixas
        obrigacoes_automaticas_total = obrigacoes_30_total + despesas_fixas_auto_total
        pagamentos_reais_sede_total = sum(
            _to_float(e.get("valor_total")) if e.get("valor_total") is not None else _to_float(e.get("valor"))
            for e in envios
            if not _bool_norm(e.get("pagamento_historico_sem_movimentacao"))
        )
        candidatos_duplicidade = len(candidatos_alta) + len(candidatos_media)

        print("=== RESUMO EXECUTIVO ===")
        print(f"TOTAL_LANCAMENTOS: {total_lancamentos}")
        print(f"TOTAL_ENTRADAS_ERP: {_fmt_money(total_entradas_erp)}")
        print(f"TOTAL_SAIDAS_ERP: {_fmt_money(total_saidas_erp)}")
        print(f"SALDO_ERP: {_fmt_money(saldo_erp)}")
        print(f"OBRIGACOES_AUTOMATICAS_TOTAL: {_fmt_money(obrigacoes_automaticas_total)}")
        print(f"OBRIGACOES_30_AUTOMATICAS: {_fmt_money(obrigacoes_30_total)}")
        print(f"DESPESAS_FIXAS_AUTOMATICAS: {_fmt_money(despesas_fixas_auto_total)}")
        print(f"PAGAMENTOS_REAIS_SEDE: {_fmt_money(pagamentos_reais_sede_total)}")
        print(f"SALDO_CAIXA_REAL_SIMULADO: {_fmt_money(saldo_caixa_real_simulado)}")
        print(f"DIFERENCA_ERP_VS_SIMULADO: {_fmt_money(diferenca_erp_vs_simulado)}")
        print(f"CANDIDATOS_DUPLICIDADE: {candidatos_duplicidade}")
        print(f"INCONSISTENCIAS_ESTRUTURAIS: {total_inconsistencias}")
        print(f"AUTOMATICOS_NAO_CLASSIFICADOS: {len(automaticos_nao_classificados)}")
        print(f"AUTOMATICOS_NAO_CLASSIFICADOS_VALOR: {_fmt_money(automaticos_nao_classificados_valor)}")
        print("=== FIM RESUMO ===")

        print("\nTOP 20 REGISTROS QUE MAIS IMPACTAM A DIFERENCA")
        impacto_rows = [
            l
            for l in obrigacoes_auto
            if _tipo_norm(l.get("tipo")) == "saida"
        ]
        impacto_rows = sorted(impacto_rows, key=lambda x: _to_float(x.get("valor")), reverse=True)
        for l in impacto_rows[:20]:
            print(
                f"id={l.get('id')} | data={l.get('data')} | categoria={l.get('categoria')} | "
                f"descricao={l.get('descricao')} | valor={_fmt_money(_to_float(l.get('valor')))} | "
                f"conta={l.get('conta')} | origem={l.get('origem')}"
            )

        # ==================================================================
        # PARTE NOVA - RASTREABILIDADE ATUAL DE PRODUÇÃO
        # ==================================================================
        print("\nPARTE EXTRA - RASTREABILIDADE PRODUCAO ATUAL")

        if _table_exists(insp, "envios_sede"):
            envios_wanted = [
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
                "tipo_pagamento",
                "pagamento_historico_sem_movimentacao",
                "lancamento_financeiro_id",
                "created_at",
                "updated_at",
                "comprovante",
                "observacao",
            ]
            envios, envios_cols = _select_table_rows(conn, insp, "envios_sede", envios_wanted, order_by="id")
        else:
            envios = []

        _print_table_rows(
            "ENVIOS_SEDE_ATUAIS",
            envios,
            [
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
                "tipo_pagamento",
                "pagamento_historico_sem_movimentacao",
                "lancamento_financeiro_id",
                "created_at",
                "updated_at",
            ],
        )
        total_envios_sede_atual = len(envios)
        print("TOTAL_ENVIOS_SEDE_ATUAL:", total_envios_sede_atual)

        envios_by_id = {row.get("id"): row for row in envios}
        for target_id in (15, 16, 17, 18, 19, 20):
            print(f"ID_{target_id}_EXISTE:", "SIM" if target_id in envios_by_id else "NAO")

        ids_missings = [target_id for target_id in (19, 20) if target_id not in envios_by_id]
        if ids_missings:
            audit_like_tables = [
                table_name
                for table_name in table_names
                if any(token in table_name.lower() for token in ("audit", "auditoria", "histor", "hist", "log"))
            ]
            if audit_like_tables:
                print("\nHISTORICO/AUDITORIA PARA IDS AUSENTES")
                for table_name in sorted(audit_like_tables):
                    columns = _table_columns(insp, table_name)
                    id_columns = [
                        column_name
                        for column_name in ("envio_id", "envios_sede_id", "envio_sede_id", "id_envio", "id")
                        if column_name in columns
                    ]
                    if not id_columns:
                        continue
                    selected_rows = []
                    for id_column in id_columns:
                        rows = _fetch_all(
                            conn,
                            f"SELECT * FROM {table_name} WHERE {id_column} IN (:id1, :id2)",
                            {"id1": ids_missings[0], "id2": ids_missings[-1]},
                        )
                        if rows:
                            selected_rows.extend(rows)
                    if selected_rows:
                        print(f"TABELA {table_name}:")
                        for row in selected_rows:
                            print(row)

        lancamentos_julho = [
            l
            for l in lancamentos
            if _tipo_norm(l.get("tipo")) == "saida"
            and (_to_date(l.get("data")) is not None)
            and date(2026, 7, 1) <= _to_date(l.get("data")) <= date(2026, 7, 31)
        ]
        _print_table_rows(
            "SAIDAS_JULHO_2026",
            lancamentos_julho,
            [
                "id",
                "data",
                "tipo",
                "categoria",
                "descricao",
                "valor",
                "conta",
                "origem",
                "conciliado",
                "documento_ref",
                "criado_em",
                "par_conciliacao_id",
                "projeto_id",
            ],
        )
        print("TOTAL_SAIDAS_JULHO:", len(lancamentos_julho))
        print("VALOR_SAIDAS_JULHO:", _fmt_money(sum(_to_float(l.get("valor")) for l in lancamentos_julho)))

        for origem in ("manual", "importado", "automatico", "outros"):
            if origem == "outros":
                grupo = [l for l in lancamentos_julho if _origem_norm(l.get("origem")) not in ("manual", "importado", "automatico")]
            else:
                grupo = [l for l in lancamentos_julho if _origem_norm(l.get("origem")) == origem]
            print(f"\nSAIDAS_JULHO_ORIGEM_{origem.upper()}:")
            _print_table_rows(
                f"SAIDAS_JULHO_{origem.upper()}",
                grupo,
                [
                    "id",
                    "data",
                    "tipo",
                    "categoria",
                    "descricao",
                    "valor",
                    "conta",
                    "origem",
                    "conciliado",
                    "documento_ref",
                    "criado_em",
                    "par_conciliacao_id",
                    "projeto_id",
                ],
            )

        candidatos_juizo = []
        valores_alvo = {1520.00, 1641.01, 2109.11, 934.49, 1000.00, 1425.59, 1240.00, 1361.01, 1829.11, 654.49, 1145.59, 280.00}
        for lancamento in lancamentos_julho:
            if round(_to_float(lancamento.get("valor")), 2) in valores_alvo:
                candidatos_juizo.append(lancamento)
        _print_table_rows(
            "CANDIDATOS_JULHO_POR_VALOR",
            candidatos_juizo,
            [
                "id",
                "data",
                "tipo",
                "categoria",
                "descricao",
                "valor",
                "conta",
                "origem",
                "conciliado",
                "documento_ref",
                "criado_em",
                "par_conciliacao_id",
                "projeto_id",
            ],
        )

        if _table_exists(insp, "envios_sede"):
            envios_match_rows = _build_envio_match_rows(conn, insp, envios, lancamentos)
        else:
            envios_match_rows = []

        print("\nCORRELACAO_ENVIOS_SEDE")
        if not envios_match_rows:
            print("SEM REGISTROS")
        else:
            for row in envios_match_rows:
                print(
                    " | ".join(
                        [
                            f"ENVIO_ID={row.get('ENVIO_ID')}",
                            f"COMPETENCIA={row.get('COMPETENCIA')}",
                            f"VALOR_ENVIO={_fmt_money(_to_float(row.get('VALOR_ENVIO')))}",
                            f"TIPO_PAGAMENTO={row.get('TIPO_PAGAMENTO')}",
                            f"HISTORICO_SEM_MOVIMENTO={row.get('HISTORICO_SEM_MOVIMENTO')}",
                            f"LANCAMENTO_FINANCEIRO_ID={row.get('LANCAMENTO_FINANCEIRO_ID')}",
                            f"CANDIDATO_LANCAMENTO_ID={row.get('CANDIDATO_LANCAMENTO_ID')}",
                            f"VALOR_CANDIDATO={_fmt_money(_to_float(row.get('VALOR_CANDIDATO')))}" if row.get('VALOR_CANDIDATO') is not None else "VALOR_CANDIDATO=",
                            f"DATA_CANDIDATO={_fmt_date(row.get('DATA_CANDIDATO'))}",
                            f"ORIGEM_CANDIDATO={row.get('ORIGEM_CANDIDATO')}",
                            f"CONFIANCA={row.get('CONFIANCA')}",
                            f"MOTIVO={row.get('MOTIVO')}",
                        ]
                    )
                )

        lancamento_by_id = {l.get("id"): l for l in lancamentos}
        if _table_exists(insp, "conciliacao_pares"):
            pares_wanted = [
                "id",
                "historico_id",
                "lancamento_manual_id",
                "lancamento_importado_id",
                "score_similaridade",
                "regra_aplicada",
                "metodo_conciliacao",
                "usuario",
                "criado_em",
                "ativo",
            ]
            pares, pares_cols = _select_table_rows(conn, insp, "conciliacao_pares", pares_wanted, order_by="id")
        else:
            pares = []

        print("\nCONCILIACAO_PARES_ESTRUTURA")
        if pares_cols:
            print("TOTAL_PARES_CONCILIACAO:", len(pares))
            print("COLUNAS:", ", ".join(sorted(pares_cols)))
        else:
            print("TOTAL_PARES_CONCILIACAO: 0")
            print("COLUNAS: SEM TABELA")

        lancamentos_conciliado_true = sum(1 for l in lancamentos if _bool_norm(l.get("conciliado")))
        lancamentos_com_par_conciliacao = sum(1 for l in lancamentos if l.get("par_conciliacao_id") is not None)
        pares_ativos = sum(1 for p in pares if isinstance(p, dict) and _bool_norm(p.get("ativo")))
        pares_desfeitos = len(pares) - pares_ativos

        print("LANCAMENTOS_CONCILIADO_TRUE:", lancamentos_conciliado_true)
        print("LANCAMENTOS_COM_PAR_CONCILIACAO:", lancamentos_com_par_conciliacao)
        print("PARES_ATIVOS:", pares_ativos)
        print("PARES_DESFEITOS:", pares_desfeitos)

        pares_by_launch = set()
        for par in pares:
            pares_by_launch.add(par.get("lancamento_manual_id"))
            pares_by_launch.add(par.get("lancamento_importado_id"))

        tem_divergencia_conciliacao = any(
            (l.get("par_conciliacao_id") is not None and not _bool_norm(l.get("conciliado")))
            or (_bool_norm(l.get("conciliado")) and l.get("id") not in pares_by_launch)
            for l in lancamentos
        )
        if tem_divergencia_conciliacao:
            campo_fonte = "PARCIAL"
            justificativa_conciliacao = "existe divergencia entre campo booleano, pares e referencias de par_conciliacao_id"
        elif lancamentos_com_par_conciliacao == lancamentos_conciliado_true and pares_ativos > 0:
            campo_fonte = "SIM"
            justificativa_conciliacao = "campo booleano e pares ativos apontam na mesma direção"
        else:
            campo_fonte = "PARCIAL"
            justificativa_conciliacao = "há indicios de fonte duplicada e o par pode não refletir todo o estado dos lancamentos"

        print("CAMPO_CONCILIADO_E_FONTE_DE_VERDADE:", campo_fonte)
        print("JUSTIFICATIVA_CONCILIACAO:", justificativa_conciliacao)

        lanc79 = lancamento_by_id.get(79)
        print("\nID_79_DETALHE")
        if lanc79 is None:
            print("ID_79_CLASSIFICACAO: INDETERMINADO")
            print("ID_79_ENCONTRADO: NAO")
        else:
            _print_table_rows(
                "ID_79_REGISTRO",
                [lanc79],
                [
                    "id",
                    "data",
                    "tipo",
                    "categoria",
                    "descricao",
                    "valor",
                    "conta",
                    "origem",
                    "conciliado",
                    "documento_ref",
                    "criado_em",
                    "observacoes",
                    "updated_at",
                    "par_conciliacao_id",
                    "projeto_id",
                ],
            )
            if eh_obrigacao_30_automatica(lanc79):
                classificacao_id79 = "OBRIGACAO_COMPROVADA"
            elif lanc79.get("lancamento_financeiro_id") is not None or _bool_norm(lanc79.get("conciliado")):
                classificacao_id79 = "MOVIMENTO_REAL_COMPROVADO"
            else:
                classificacao_id79 = "INDETERMINADO"
            print("ID_79_CLASSIFICACAO:", classificacao_id79)

        saldo_erp_atual = round(total_entradas_erp - total_saidas_erp, 2)
        valor_id79 = _to_float(lanc79.get("valor")) if lanc79 else 0.0
        saldo_caixa_comprovado = round(saldo_erp_atual + obrigacoes_automaticas_total, 2)
        saldo_caixa_conservador = saldo_caixa_comprovado
        saldo_hipotese_id79 = round(saldo_caixa_comprovado + valor_id79, 2) if lanc79 else saldo_caixa_comprovado

        print("\n=== RASTREABILIDADE PRODUCAO ===")
        print(f"TOTAL_ENVIOS_SEDE_ATUAL: {total_envios_sede_atual}")
        print(f"ID_19_EXISTE: {'SIM' if 19 in envios_by_id else 'NAO'}")
        print(f"ID_20_EXISTE: {'SIM' if 20 in envios_by_id else 'NAO'}")
        if 19 in envios_by_id and 20 in envios_by_id:
            causa_divergencia = "os IDs 19 e 20 existem na tabela atual; a divergencia anterior foi recorte/filtro do script anterior"
        elif 19 not in envios_by_id and 20 not in envios_by_id and ids_missings:
            causa_divergencia = "os IDs 19 e 20 não estão na tabela atual; foi encontrada apenas ausência atual, sem excluir hipótese de histórico"
        else:
            causa_divergencia = "divergencia atual ainda não fechada somente com as tabelas presentes"
        print(f"CAUSA_DIVERGENCIA_4_VS_6: {causa_divergencia}")
        print(f"TOTAL_SAIDAS_JULHO: {len(lancamentos_julho)}")
        print(f"VALOR_SAIDAS_JULHO: {_fmt_money(sum(_to_float(l.get('valor')) for l in lancamentos_julho))}")
        pagamentos_julho = [
            row for row in envios_match_rows
            if _to_date(envios_by_id.get(row.get('ENVIO_ID'), {}).get('data_pagamento')) is not None
            and date(2026, 7, 1) <= _to_date(envios_by_id.get(row.get('ENVIO_ID'), {}).get('data_pagamento')) <= date(2026, 7, 31)
            and row.get('CONFIANCA') in ("ALTA", "MEDIA")
        ]
        valor_pagamentos_julho = sum(_to_float(row.get("VALOR_ENVIO")) for row in pagamentos_julho)
        print(f"PAGAMENTOS_SEDE_JULHO_COMPROVADOS: {len(pagamentos_julho)}")
        print(f"VALOR_PAGAMENTOS_SEDE_JULHO: {_fmt_money(valor_pagamentos_julho)}")
        print(f"ENVIOS_COM_LANCAMENTO: {sum(1 for row in envios_match_rows if row.get('LANCAMENTO_FINANCEIRO_ID') is not None and not row.get('HISTORICO_SEM_MOVIMENTO'))}")
        print(f"ENVIOS_HISTORICOS_SEM_MOVIMENTO: {sum(1 for row in envios_match_rows if row.get('HISTORICO_SEM_MOVIMENTO'))}")
        print(f"ENVIOS_REAIS_SEM_LANCAMENTO: {sum(1 for row in envios_match_rows if not row.get('HISTORICO_SEM_MOVIMENTO') and row.get('LANCAMENTO_FINANCEIRO_ID') is None)}")
        print(f"TOTAL_PARES_CONCILIACAO: {len(pares)}")
        print(f"CAMPO_CONCILIADO_E_FONTE_DE_VERDADE: {campo_fonte}")
        print(f"ID_79_CLASSIFICACAO: {classificacao_id79 if lanc79 else 'INDETERMINADO'}")
        print(f"SALDO_ERP_ATUAL: {_fmt_money(saldo_erp_atual)}")
        print(f"SALDO_CAIXA_COMPROVADO: {_fmt_money(saldo_caixa_comprovado)}")
        print(f"SALDO_CAIXA_CONSERVADOR: {_fmt_money(saldo_caixa_conservador)}")
        print(f"SALDO_HIPOTESE_ID79_OBRIGACAO: {_fmt_money(saldo_hipotese_id79)}")
        correcao_codigo_necessaria = "SIM" if campo_fonte != "SIM" or classificacao_id79 == "INDETERMINADO" else "NÃO"
        correcao_dados_historicos_necessaria = "INDETERMINADO" if ids_missings else "NÃO"
        print(f"CORRECAO_DE_CODIGO_NECESSARIA: {correcao_codigo_necessaria}")
        print(f"CORRECAO_DE_DADOS_HISTORICOS_NECESSARIA: {correcao_dados_historicos_necessaria}")
        print("=== FIM RASTREABILIDADE ===")

        tx.rollback()


if __name__ == "__main__":
    main()
