from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from flask import Flask
from sqlalchemy import text

from app.config import Config
from app.extensoes import db


TARGET_TABLES = ("envios_sede", "pagamentos_obrigacao")


@dataclass
class LockSummary:
    tem_lock_conflitante_envio_sede: bool
    locks_observados: int
    locks_externos_conflitantes: int
    pid_bloqueador: str
    tipo_lock_bloqueador: str
    state_bloqueador: str
    xact_start_bloqueador: str
    query_start_bloqueador: str
    wait_event_type_bloqueador: str
    wait_event_bloqueador: str
    origem_provavel: str


def novo_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app


def _sanitize_query(q: str | None, limit: int = 140) -> str:
    if not q:
        return "-"
    normal = " ".join(q.split())
    if len(normal) <= limit:
        return normal
    return normal[:limit] + "..."


def _format_interval(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, timedelta):
        return str(value)
    return str(value)


def _snapshot_counts() -> dict[str, int]:
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


def _query_pid_atual() -> int:
    row = db.session.execute(text("select pg_backend_pid() as pid_atual")).mappings().first()
    return int(row["pid_atual"])


def _inferir_origem(application_name: str | None) -> str:
    app_name = (application_name or "").lower()
    if "gunicorn" in app_name:
        return "gunicorn"
    if "psql" in app_name or "shell" in app_name:
        return "shell"
    return "outra"


def _locks_externos_conflitantes(rows, pid_atual: int):
    return [
        r for r in rows
        if r.get("relation_name") == "envios_sede"
        and bool(r.get("granted"))
        and int(r.get("pid") or 0) != int(pid_atual)
    ]


def _metricas_transacoes_externas(activities, pid_atual: int):
    externos = [r for r in activities if int(r.get("pid") or 0) != int(pid_atual)]
    abertas = [r for r in externos if r.get("xact_start") is not None]
    idle = [r for r in abertas if str(r.get("state") or "").lower() == "idle in transaction"]

    mais_antiga = None
    if abertas:
        mais_antiga = min(abertas, key=lambda r: r.get("xact_start"))

    return {
        "transacoes_abertas": len(abertas),
        "transacoes_idle": len(idle),
        "mais_antiga": mais_antiga,
    }


def _detectar_lock_envio_sede(rows, pid_atual: int) -> LockSummary:
    observados = [r for r in rows if r.get("relation_name") == "envios_sede"]
    externos = _locks_externos_conflitantes(rows, pid_atual)

    if not externos:
        return LockSummary(False, len(observados), 0, "-", "-", "-", "-", "-", "-", "-", "-")

    primeiro = externos[0]
    return LockSummary(
        tem_lock_conflitante_envio_sede=True,
        locks_observados=len(observados),
        locks_externos_conflitantes=len(externos),
        pid_bloqueador=str(primeiro.get("pid") or "-"),
        tipo_lock_bloqueador=str(primeiro.get("lock_mode") or "-"),
        state_bloqueador=str(primeiro.get("state") or "-"),
        xact_start_bloqueador=str(primeiro.get("xact_start") or "-"),
        query_start_bloqueador=str(primeiro.get("query_start") or "-"),
        wait_event_type_bloqueador=str(primeiro.get("wait_event_type") or "-"),
        wait_event_bloqueador=str(primeiro.get("wait_event") or "-"),
        origem_provavel=_inferir_origem(primeiro.get("application_name")),
    )


def _query_pg_stat_activity():
    return db.session.execute(
        text(
            """
            select
                a.pid,
                a.usename,
                coalesce(a.application_name, '-') as application_name,
                coalesce(a.client_addr::text, '-') as client_addr,
                a.state,
                a.xact_start,
                a.query_start,
                a.wait_event_type,
                a.wait_event,
                left(regexp_replace(coalesce(a.query, ''), '\\s+', ' ', 'g'), 240) as query_excerpt
            from pg_stat_activity a
            where a.datname = current_database()
            order by a.xact_start nulls last, a.query_start nulls last
            """
        )
    ).mappings().all()


def _query_locks_tables_alvo():
    return db.session.execute(
        text(
            """
            select
                a.pid,
                a.usename,
                coalesce(a.application_name, '-') as application_name,
                a.state,
                a.xact_start,
                a.query_start,
                l.locktype,
                l.mode as lock_mode,
                l.granted,
                coalesce(n.nspname, '-') as schema_name,
                coalesce(c.relname, '-') as relation_name,
                a.wait_event_type,
                a.wait_event,
                left(regexp_replace(coalesce(a.query, ''), '\\s+', ' ', 'g'), 180) as query_excerpt
            from pg_locks l
            join pg_stat_activity a
              on a.pid = l.pid
            left join pg_class c
              on c.oid = l.relation
            left join pg_namespace n
              on n.oid = c.relnamespace
            where a.datname = current_database()
              and (
                   c.relname in ('envios_sede', 'pagamentos_obrigacao')
                   or (c.relname is null and l.locktype in ('transactionid', 'virtualxid'))
              )
            order by c.relname nulls last, l.granted asc, a.query_start nulls last
            """
        )
    ).mappings().all()


def _query_blocking_pairs():
    pid_atual = _query_pid_atual()
    return db.session.execute(
        text(
            """
            select
                blocked.pid as blocked_pid,
                blocker.pid as blocker_pid,
                coalesce(blocker.application_name, '-') as blocker_application_name,
                blocked.wait_event_type,
                blocked.wait_event,
                left(regexp_replace(coalesce(blocked.query, ''), '\\s+', ' ', 'g'), 180) as blocked_query
            from pg_stat_activity blocked
            join lateral unnest(pg_blocking_pids(blocked.pid)) as bpid(blocker_pid) on true
            join pg_stat_activity blocker
              on blocker.pid = bpid.blocker_pid
            where blocked.datname = current_database()
              and blocked.pid <> :pid_atual
              and blocker.pid <> :pid_atual
            order by blocked.query_start nulls last
            """
        ),
        {"pid_atual": pid_atual}
    ).mappings().all()


def main() -> int:
    print("=== DIAGNOSTICO LOCK D.2.3D.1 ===")

    try:
        app = novo_app()
        with app.app_context():
            dialeto = (db.engine.dialect.name or "").lower()
            print(f"DIALETO: {dialeto}")
            print(f"POSTGRESQL_OK: {'SIM' if dialeto == 'postgresql' else 'NAO'}")

            if dialeto != "postgresql":
                print("RESULTADO_DIAGNOSTICO_LOCK: BLOQUEADO")
                print("MOTIVO: dialeto nao e postgresql")
                print("=== FIM DIAGNOSTICO LOCK D.2.3D.1 ===")
                return 1

            before = _snapshot_counts()
            pid_atual = _query_pid_atual()
            print(f"PID_ATUAL: {pid_atual}")

            activities = _query_pg_stat_activity()
            locks = _query_locks_tables_alvo()
            blockers = _query_blocking_pairs()
            tx_info = _metricas_transacoes_externas(activities, pid_atual)
            oldest = tx_info["mais_antiga"]

            print("PG_STAT_ACTIVITY:")
            for row in activities:
                print(
                    " - "
                    f"pid={row['pid']} user={row['usename']} app={row['application_name']} "
                    f"client={row['client_addr']} state={row['state']} "
                    f"xact_start={row['xact_start']} query_start={row['query_start']} "
                    f"wait={row['wait_event_type'] or '-'}:{row['wait_event'] or '-'} "
                    f"query={_sanitize_query(row['query_excerpt'])}"
                )

            print("LOCKS_ALVO:")
            for row in locks:
                print(
                    " - "
                    f"pid={row['pid']} relation={row['relation_name']} mode={row['lock_mode']} "
                    f"granted={row['granted']} state={row['state']} "
                    f"wait={row['wait_event_type'] or '-'}:{row['wait_event'] or '-'} "
                    f"app={row['application_name']} query={_sanitize_query(row['query_excerpt'])}"
                )

            print("BLOQUEIOS:")
            for row in blockers:
                print(
                    " - "
                    f"blocked_pid={row['blocked_pid']} blocker_pid={row['blocker_pid']} "
                    f"blocker_app={row['blocker_application_name']} "
                    f"wait={row['wait_event_type'] or '-'}:{row['wait_event'] or '-'} "
                    f"blocked_query={_sanitize_query(row['blocked_query'])}"
                )

            trans_abertas = int(tx_info["transacoes_abertas"] or 0)
            trans_idle = int(tx_info["transacoes_idle"] or 0)
            print(f"TRANSACOES_ABERTAS: {trans_abertas}")
            print(f"TRANSACOES_IDLE_IN_TRANSACTION: {trans_idle}")

            if oldest is None:
                print("TRANSACAO_MAIS_ANTIGA: -")
            else:
                print(
                    "TRANSACAO_MAIS_ANTIGA: "
                    f"pid={oldest['pid']} started_at={_format_interval(oldest['xact_start'])} "
                    f"state={oldest['state']} app={oldest['application_name']}"
                )

            lock_summary = _detectar_lock_envio_sede(locks, pid_atual)
            print(f"LOCKS_OBSERVADOS: {lock_summary.locks_observados}")
            print(f"LOCKS_EXTERNOS_CONFLITANTES: {lock_summary.locks_externos_conflitantes}")
            print(f"ENVIO_SEDE_TEM_LOCK_CONFLITANTE: {'SIM' if lock_summary.tem_lock_conflitante_envio_sede else 'NAO'}")
            print(f"PID_BLOQUEADOR: {lock_summary.pid_bloqueador}")
            print(f"TIPO_LOCK_BLOQUEADOR: {lock_summary.tipo_lock_bloqueador}")
            print(f"STATE_BLOQUEADOR: {lock_summary.state_bloqueador}")
            print(f"XACT_START_BLOQUEADOR: {lock_summary.xact_start_bloqueador}")
            print(f"QUERY_START_BLOQUEADOR: {lock_summary.query_start_bloqueador}")
            print(f"WAIT_EVENT_TYPE_BLOQUEADOR: {lock_summary.wait_event_type_bloqueador}")
            print(f"WAIT_EVENT_BLOQUEADOR: {lock_summary.wait_event_bloqueador}")
            print(f"ORIGEM_PROVAVEL: {lock_summary.origem_provavel}")

            after = _snapshot_counts()
            persistencia_alterada = before != after
            print(f"PERSISTENCIA_ALTERADA: {'SIM' if persistencia_alterada else 'NAO'}")

            print("RESULTADO_DIAGNOSTICO_LOCK: OK")

        print("=== FIM DIAGNOSTICO LOCK D.2.3D.1 ===")
        return 0
    except Exception as exc:
        print("RESULTADO_DIAGNOSTICO_LOCK: BLOQUEADO")
        print(f"MOTIVO: falha controlada: {exc}")
        print("=== FIM DIAGNOSTICO LOCK D.2.3D.1 ===")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
