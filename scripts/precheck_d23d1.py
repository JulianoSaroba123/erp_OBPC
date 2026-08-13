from __future__ import annotations

from flask import Flask
from sqlalchemy import inspect, text

from app.config import Config
from app.extensoes import db


def novo_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app


def _normalizar_tipo(coluna_tipo) -> str:
    return str(coluna_tipo).strip().lower()


def _tipo_compativel(origem: str, destino: str) -> bool:
    origem_n = (origem or "").lower()
    destino_n = (destino or "").lower()
    familias_int = ("smallint", "integer", "bigint", "int")
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


def _contagens_basicas() -> dict[str, int]:
    row = db.session.execute(
        text(
            """
            select
                (select count(*) from pagamentos_obrigacao) as pagamentos_obrigacao,
                (select count(*) from pagamentos_obrigacao_itens) as pagamentos_obrigacao_itens,
                (select count(*) from lancamentos) as lancamentos,
                (select count(*) from envios_sede) as envios_sede
            """
        )
    ).mappings().first()
    return {
        "pagamentos_obrigacao": int(row["pagamentos_obrigacao"]),
        "pagamentos_obrigacao_itens": int(row["pagamentos_obrigacao_itens"]),
        "lancamentos": int(row["lancamentos"]),
        "envios_sede": int(row["envios_sede"]),
    }


def _bloquear(motivo: str) -> int:
    print("RESULTADO_PRECHECK_D23D1: BLOQUEADO")
    print(f"ABORTAR_MOTIVO: {motivo}")
    print("=== FIM PRECHECK D.2.3D.1 ===")
    return 1


def main() -> int:
    print("=== PRECHECK D.2.3D.1 ===")
    try:
        app = novo_app()
        with app.app_context():
            resultado = "APROVADO"

            inspector = inspect(db.engine)
            dialeto = (db.engine.dialect.name or "").lower()
            postgresql_ok = dialeto == "postgresql"

            print(f"DIALETO: {dialeto}")
            print(f"POSTGRESQL_OK: {'SIM' if postgresql_ok else 'NAO'}")

            if not postgresql_ok:
                return _bloquear("dialeto nao e postgresql")

            tabelas = set(inspector.get_table_names())
            tabela_envios = "envios_sede" in tabelas
            tabela_pagamentos = "pagamentos_obrigacao" in tabelas

            print(f"TABELA_ENVIOS_SEDE: {'SIM' if tabela_envios else 'NAO'}")
            print(f"TABELA_PAGAMENTOS_OBRIGACAO: {'SIM' if tabela_pagamentos else 'NAO'}")

            if not tabela_envios:
                return _bloquear("schema desatualizado: tabela envios_sede ausente")
            if not tabela_pagamentos:
                return _bloquear("schema desatualizado: tabela pagamentos_obrigacao ausente")

            colunas_envios = {c["name"]: c for c in inspector.get_columns("envios_sede")}
            colunas_pagamentos = {c["name"]: c for c in inspector.get_columns("pagamentos_obrigacao")}

            coluna = colunas_envios.get("pagamento_obrigacao_id")
            coluna_ref = colunas_pagamentos.get("id")
            coluna_existe = coluna is not None
            coluna_nullable = bool(coluna.get("nullable", False)) if coluna_existe else False
            tipo_coluna_compativel = False

            if coluna_existe and coluna_ref is not None:
                tipo_coluna_compativel = _tipo_compativel(
                    _normalizar_tipo(coluna.get("type")),
                    _normalizar_tipo(coluna_ref.get("type")),
                )

            print(f"COLUNA_PAGAMENTO_OBRIGACAO_ID: {'SIM' if coluna_existe else 'NAO'}")
            print(f"COLUNA_NULLABLE: {'SIM' if coluna_nullable else 'NAO'}")
            print(f"TIPO_COLUNA_COMPATIVEL: {'SIM' if tipo_coluna_compativel else 'NAO'}")

            if not coluna_existe:
                return _bloquear("schema desatualizado: pagamento_obrigacao_id ausente")

            if coluna_ref is None:
                return _bloquear("schema desatualizado: coluna id ausente em pagamentos_obrigacao")

            fk = _buscar_fk_envios_para_pagamentos(inspector)
            fk_real = fk is not None
            fk_tabela_destino = "-"
            fk_coluna_destino = "-"
            if fk is not None:
                fk_tabela_destino = str(fk.get("referred_table") or "-")
                cols_ref = fk.get("referred_columns") or []
                fk_coluna_destino = cols_ref[0] if cols_ref else "-"

            unique_real = _tem_unique_coluna(inspector)

            print(f"FK_REAL: {'SIM' if fk_real else 'NAO'}")
            print(f"FK_TABELA_DESTINO: {fk_tabela_destino}")
            print(f"FK_COLUNA_DESTINO: {fk_coluna_destino}")
            print(f"UNIQUE_REAL: {'SIM' if unique_real else 'NAO'}")

            before_counts = _contagens_basicas()

            hist = db.session.execute(
                text(
                    """
                    select
                        count(*) as total_envios_sede,
                        count(pagamento_obrigacao_id) as envios_com_pagamento_obrigacao_id,
                        sum(case when pagamento_obrigacao_id is null then 1 else 0 end) as envios_com_pagamento_obrigacao_id_null
                    from envios_sede
                    """
                )
            ).mappings().first()

            total_envios_sede = int(hist["total_envios_sede"])
            envios_com_fk = int(hist["envios_com_pagamento_obrigacao_id"])
            envios_fk_null = int(hist["envios_com_pagamento_obrigacao_id_null"] or 0)

            print(f"TOTAL_ENVIOS_SEDE: {total_envios_sede}")
            print(f"ENVIOS_COM_PAGAMENTO_OBRIGACAO_ID: {envios_com_fk}")
            print(f"ENVIOS_COM_PAGAMENTO_OBRIGACAO_ID_NULL: {envios_fk_null}")

            orfaos = db.session.execute(
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
            vinculos_orfaos = int(orfaos["vinculos_orfaos"])
            print(f"VINCULOS_ORFAOS: {vinculos_orfaos}")

            after_counts = _contagens_basicas()
            persistencia_alterada = before_counts != after_counts
            print(f"PERSISTENCIA_ALTERADA: {'SIM' if persistencia_alterada else 'NAO'}")

            aprovado = all(
                [
                    postgresql_ok,
                    tabela_envios,
                    tabela_pagamentos,
                    coluna_existe,
                    coluna_nullable,
                    tipo_coluna_compativel,
                    fk_real,
                    unique_real,
                    vinculos_orfaos == 0,
                    not persistencia_alterada,
                ]
            )

            if not aprovado:
                resultado = "BLOQUEADO"

            print(f"RESULTADO_PRECHECK_D23D1: {resultado}")

        print("=== FIM PRECHECK D.2.3D.1 ===")
        return 0 if resultado == "APROVADO" else 1
    except Exception as exc:
        return _bloquear(f"falha controlada: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
