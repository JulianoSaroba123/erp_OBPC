from __future__ import annotations

import argparse
from dataclasses import dataclass

from flask import Flask
from sqlalchemy import inspect, text

from app.config import Config
from app.extensoes import db

FK_NAME = "fk_envios_sede_pagamento_obrigacao_id"
UNIQUE_NAME = "uq_envios_sede_pagamento_obrigacao_id"

ESTADO_A = "ESTADO_A_SCHEMA_AUSENTE_APTO"
ESTADO_B = "ESTADO_B_SCHEMA_COMPLETO_JA_APLICADO"
ESTADO_C = "ESTADO_C_SCHEMA_PARCIAL_BLOQUEADO"
ESTADO_D = "ESTADO_D_SCHEMA_INCOMPATIVEL_BLOQUEADO"


@dataclass
class Snapshot:
    pagamentos_obrigacao: int
    pagamentos_obrigacao_itens: int
    lancamentos: int
    envios_sede: int
    saldo_lancamentos: float


@dataclass
class SchemaStatus:
    dialeto: str
    postgresql_ok: bool
    tabela_envios_sede: bool
    tabela_pagamentos_obrigacao: bool
    coluna_existe: bool
    coluna_nullable: bool
    tipo_coluna_compativel: bool
    fk_real: bool
    unique_real: bool
    fk_tabela_destino: str
    fk_coluna_destino: str
    id_type_sql: str
    estado_schema: str
    apto_para_aplicar: bool
    motivo_bloqueio: str | None


def novo_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app


def _normalizar_tipo(coluna_tipo) -> str:
    return str(coluna_tipo).strip().lower()


def _tipo_compativel(origem: str, destino: str) -> bool:
    familias_int = ("smallint", "integer", "bigint", "int")
    origem_n = (origem or "").lower()
    destino_n = (destino or "").lower()
    return any(t in origem_n for t in familias_int) and any(t in destino_n for t in familias_int)


def _buscar_fk_envios_para_pagamentos(inspector):
    for fk in inspector.get_foreign_keys("envios_sede"):
        colunas = fk.get("constrained_columns") or []
        tabela_ref = fk.get("referred_table")
        colunas_ref = fk.get("referred_columns") or []
        if colunas == ["pagamento_obrigacao_id"] and tabela_ref == "pagamentos_obrigacao" and colunas_ref == ["id"]:
            return fk
    return None


def _tem_unique_coluna(inspector) -> bool:
    for uq in inspector.get_unique_constraints("envios_sede"):
        cols = uq.get("column_names") or []
        if cols == ["pagamento_obrigacao_id"]:
            return True

    for idx in inspector.get_indexes("envios_sede"):
        cols = idx.get("column_names") or []
        if idx.get("unique") and cols == ["pagamento_obrigacao_id"]:
            return True

    return False


def _inferir_tipo_id_sql(coluna_tipo: str) -> str:
    tipo = (coluna_tipo or "").lower()
    if "bigint" in tipo:
        return "BIGINT"
    if "smallint" in tipo:
        return "SMALLINT"
    return "INTEGER"


def _snapshot() -> Snapshot:
    row = db.session.execute(
        text(
            """
            select
                (select count(*) from pagamentos_obrigacao) as pagamentos_obrigacao,
                (select count(*) from pagamentos_obrigacao_itens) as pagamentos_obrigacao_itens,
                (select count(*) from lancamentos) as lancamentos,
                (select count(*) from envios_sede) as envios_sede,
                (
                    coalesce((select sum(valor) from lancamentos where lower(tipo) = 'entrada'), 0)
                    - coalesce((select sum(valor) from lancamentos where lower(tipo) in ('saída', 'saida')), 0)
                ) as saldo_lancamentos
            """
        )
    ).mappings().first()
    return Snapshot(
        pagamentos_obrigacao=int(row["pagamentos_obrigacao"]),
        pagamentos_obrigacao_itens=int(row["pagamentos_obrigacao_itens"]),
        lancamentos=int(row["lancamentos"]),
        envios_sede=int(row["envios_sede"]),
        saldo_lancamentos=float(row["saldo_lancamentos"] or 0.0),
    )


def _contar_orfaos() -> int:
    row = db.session.execute(
        text(
            """
            select count(*) as vinculos_orfaos
            from envios_sede es
            left join pagamentos_obrigacao po
              on po.id = es.pagamento_obrigacao_id
            where es.pagamento_obrigacao_id is not null
              and po.id is null
            """
        )
    ).mappings().first()
    return int(row["vinculos_orfaos"])


def _classificar_estado(
    *,
    tabela_envios: bool,
    tabela_pagamentos: bool,
    coluna_existe: bool,
    coluna_nullable: bool,
    tipo_coluna_compativel: bool,
    fk_real: bool,
    unique_real: bool,
) -> tuple[str, bool, str | None]:
    if not tabela_envios:
        return ESTADO_D, False, "schema incompatível: tabela envios_sede ausente"
    if not tabela_pagamentos:
        return ESTADO_D, False, "schema incompatível: tabela pagamentos_obrigacao ausente"

    if not coluna_existe:
        if fk_real or unique_real:
            return ESTADO_D, False, "schema incompatível: constraints existem sem coluna"
        return ESTADO_A, True, None

    if not coluna_nullable or not tipo_coluna_compativel:
        return ESTADO_D, False, "schema incompatível: coluna existente com definição divergente"

    if coluna_existe and fk_real and unique_real:
        return ESTADO_B, False, None

    if coluna_existe and (not fk_real or not unique_real):
        return ESTADO_C, False, "schema parcial: coluna existe sem FK/UNIQUE completo"

    return ESTADO_D, False, "schema incompatível"


def inspecionar_schema() -> SchemaStatus:
    inspector = inspect(db.engine)
    dialeto = (db.engine.dialect.name or "").lower()
    postgresql_ok = dialeto == "postgresql"

    tabelas = set(inspector.get_table_names())
    tabela_envios = "envios_sede" in tabelas
    tabela_pagamentos = "pagamentos_obrigacao" in tabelas

    coluna_existe = False
    coluna_nullable = False
    tipo_coluna_compativel = False
    fk_real = False
    unique_real = False
    fk_tabela_destino = "-"
    fk_coluna_destino = "-"
    id_type_sql = "INTEGER"

    if tabela_pagamentos:
        colunas_pagamentos = {c["name"]: c for c in inspector.get_columns("pagamentos_obrigacao")}
        id_col = colunas_pagamentos.get("id")
        if id_col is not None:
            id_type_sql = _inferir_tipo_id_sql(_normalizar_tipo(id_col.get("type")))

    if tabela_envios and tabela_pagamentos:
        colunas_envios = {c["name"]: c for c in inspector.get_columns("envios_sede")}
        colunas_pagamentos = {c["name"]: c for c in inspector.get_columns("pagamentos_obrigacao")}

        coluna = colunas_envios.get("pagamento_obrigacao_id")
        coluna_ref = colunas_pagamentos.get("id")

        coluna_existe = coluna is not None
        if coluna_existe:
            coluna_nullable = bool(coluna.get("nullable", False))

        if coluna_existe and coluna_ref is not None:
            tipo_coluna_compativel = _tipo_compativel(
                _normalizar_tipo(coluna.get("type")),
                _normalizar_tipo(coluna_ref.get("type")),
            )

        fk = _buscar_fk_envios_para_pagamentos(inspector)
        fk_real = fk is not None
        if fk is not None:
            fk_tabela_destino = str(fk.get("referred_table") or "-")
            cols_ref = fk.get("referred_columns") or []
            fk_coluna_destino = cols_ref[0] if cols_ref else "-"

        unique_real = _tem_unique_coluna(inspector)

    estado, apto, motivo = _classificar_estado(
        tabela_envios=tabela_envios,
        tabela_pagamentos=tabela_pagamentos,
        coluna_existe=coluna_existe,
        coluna_nullable=coluna_nullable,
        tipo_coluna_compativel=tipo_coluna_compativel,
        fk_real=fk_real,
        unique_real=unique_real,
    )

    return SchemaStatus(
        dialeto=dialeto,
        postgresql_ok=postgresql_ok,
        tabela_envios_sede=tabela_envios,
        tabela_pagamentos_obrigacao=tabela_pagamentos,
        coluna_existe=coluna_existe,
        coluna_nullable=coluna_nullable,
        tipo_coluna_compativel=tipo_coluna_compativel,
        fk_real=fk_real,
        unique_real=unique_real,
        fk_tabela_destino=fk_tabela_destino,
        fk_coluna_destino=fk_coluna_destino,
        id_type_sql=id_type_sql,
        estado_schema=estado,
        apto_para_aplicar=apto,
        motivo_bloqueio=motivo,
    )


def _print_status(status: SchemaStatus, snap: Snapshot) -> None:
    print(f"DIALETO: {status.dialeto}")
    print(f"POSTGRESQL_OK: {'SIM' if status.postgresql_ok else 'NAO'}")
    print(f"ESTADO_SCHEMA: {status.estado_schema}")
    print(f"TABELA_ENVIOS_SEDE: {'SIM' if status.tabela_envios_sede else 'NAO'}")
    print(f"TABELA_PAGAMENTOS_OBRIGACAO: {'SIM' if status.tabela_pagamentos_obrigacao else 'NAO'}")
    print(f"COLUNA_PAGAMENTO_OBRIGACAO_ID: {'SIM' if status.coluna_existe else 'NAO'}")
    print(f"COLUNA_NULLABLE: {'SIM' if status.coluna_nullable else 'NAO'}")
    print(f"TIPO_COLUNA_COMPATIVEL: {'SIM' if status.tipo_coluna_compativel else 'NAO'}")
    print(f"FK_REAL: {'SIM' if status.fk_real else 'NAO'}")
    print(f"FK_TABELA_DESTINO: {status.fk_tabela_destino}")
    print(f"FK_COLUNA_DESTINO: {status.fk_coluna_destino}")
    print(f"UNIQUE_REAL: {'SIM' if status.unique_real else 'NAO'}")
    print(f"TOTAL_ENVIOS: {snap.envios_sede}")
    print(f"TOTAL_PAGAMENTOS: {snap.pagamentos_obrigacao}")
    print(f"TOTAL_LANCAMENTOS: {snap.lancamentos}")
    print(f"SALDO_LANCAMENTOS: {snap.saldo_lancamentos:.2f}")
    print(f"APTO_PARA_APLICAR: {'SIM' if status.apto_para_aplicar else 'NAO'}")
    if status.motivo_bloqueio:
        print(f"MOTIVO_BLOQUEIO: {status.motivo_bloqueio}")


def _aplicar_transacional(id_type_sql: str) -> None:
    sql_add = f"ALTER TABLE envios_sede ADD COLUMN pagamento_obrigacao_id {id_type_sql}"
    sql_unique = f"ALTER TABLE envios_sede ADD CONSTRAINT {UNIQUE_NAME} UNIQUE (pagamento_obrigacao_id)"
    sql_fk = (
        f"ALTER TABLE envios_sede "
        f"ADD CONSTRAINT {FK_NAME} FOREIGN KEY (pagamento_obrigacao_id) "
        f"REFERENCES pagamentos_obrigacao(id) ON DELETE SET NULL"
    )

    with db.engine.begin() as conn:
        conn.execute(text(sql_add))
        conn.execute(text(sql_unique))
        conn.execute(text(sql_fk))


def executar_check() -> int:
    status = inspecionar_schema()
    snap = _snapshot()
    _print_status(status, snap)

    if not status.postgresql_ok:
        print("RESULTADO_APLICACAO_SCHEMA: BLOQUEADO")
        return 1

    if status.estado_schema == ESTADO_B:
        print("RESULTADO_APLICACAO_SCHEMA: JA_APLICADO")
        return 0

    if status.estado_schema == ESTADO_A:
        print("RESULTADO_APLICACAO_SCHEMA: BLOQUEADO")
        return 1

    print("RESULTADO_APLICACAO_SCHEMA: BLOQUEADO")
    return 1


def executar_apply() -> int:
    status_before = inspecionar_schema()
    snap_before = _snapshot()
    _print_status(status_before, snap_before)

    if not status_before.postgresql_ok:
        print("RESULTADO_APLICACAO_SCHEMA: BLOQUEADO")
        return 1

    if status_before.estado_schema == ESTADO_B:
        print("RESULTADO_APLICACAO_SCHEMA: JA_APLICADO")
        return 0

    if status_before.estado_schema != ESTADO_A or not status_before.apto_para_aplicar:
        print("RESULTADO_APLICACAO_SCHEMA: BLOQUEADO")
        return 1

    print("CONFIRME BACKUP/SNAPSHOT ANTES DE PROSSEGUIR")

    try:
        _aplicar_transacional(status_before.id_type_sql)
    except Exception as exc:
        print(f"RESULTADO_APLICACAO_SCHEMA: BLOQUEADO")
        print(f"ERRO_APLICACAO: {exc}")
        return 1

    status_after = inspecionar_schema()
    snap_after = _snapshot()
    _print_status(status_after, snap_after)

    orfaos = _contar_orfaos()
    print(f"VINCULOS_ORFAOS: {orfaos}")

    counts_inalteradas = (
        snap_before.pagamentos_obrigacao == snap_after.pagamentos_obrigacao
        and snap_before.pagamentos_obrigacao_itens == snap_after.pagamentos_obrigacao_itens
        and snap_before.lancamentos == snap_after.lancamentos
        and snap_before.envios_sede == snap_after.envios_sede
    )
    print(f"PERSISTENCIA_ALTERADA: {'NAO' if counts_inalteradas else 'SIM'}")

    aprovado = all(
        [
            status_after.estado_schema == ESTADO_B,
            status_after.coluna_existe,
            status_after.coluna_nullable,
            status_after.fk_real,
            status_after.unique_real,
            orfaos == 0,
            counts_inalteradas,
        ]
    )

    print(f"RESULTADO_APLICACAO_SCHEMA: {'APROVADO' if aprovado else 'BLOQUEADO'}")
    return 0 if aprovado else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Executor controlado do schema D.2.3D.1")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="Somente leitura; inspeciona estado do schema")
    group.add_argument("--apply", action="store_true", help="Aplica DDL controlado se e somente se o estado for apto")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    app = novo_app()
    with app.app_context():
        try:
            if args.apply:
                return executar_apply()
            return executar_check()
        except Exception as exc:
            print("RESULTADO_APLICACAO_SCHEMA: BLOQUEADO")
            print(f"ERRO_EXECUCAO: {exc}")
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
