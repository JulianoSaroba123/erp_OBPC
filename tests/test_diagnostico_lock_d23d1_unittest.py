from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import scripts.diagnostico_lock_d23d1 as diag


class TestDiagnosticoLockD23D1(unittest.TestCase):
    def test_a_proprio_lock_ignorado(self):
        rows = [
            {
                "relation_name": "envios_sede",
                "granted": True,
                "state": "active",
                "pid": 100,
                "application_name": "gunicorn",
                "lock_mode": "AccessShareLock",
            }
        ]
        summary = diag._detectar_lock_envio_sede(rows, pid_atual=100)
        self.assertFalse(summary.tem_lock_conflitante_envio_sede)
        self.assertEqual(summary.pid_bloqueador, "-")
        self.assertEqual(summary.locks_observados, 1)
        self.assertEqual(summary.locks_externos_conflitantes, 0)

    def test_b_bloqueador_externo_detectado(self):
        rows = [
            {
                "relation_name": "envios_sede",
                "granted": True,
                "state": "active",
                "pid": 200,
                "application_name": "gunicorn: worker",
                "lock_mode": "RowExclusiveLock",
                "xact_start": "2026-08-14 10:00:00",
                "query_start": "2026-08-14 10:00:05",
                "wait_event_type": "Lock",
                "wait_event": "relation",
            }
        ]
        summary = diag._detectar_lock_envio_sede(rows, pid_atual=100)
        self.assertTrue(summary.tem_lock_conflitante_envio_sede)
        self.assertEqual(summary.pid_bloqueador, "200")
        self.assertEqual(summary.tipo_lock_bloqueador, "RowExclusiveLock")
        self.assertEqual(summary.origem_provavel, "gunicorn")
        self.assertEqual(summary.locks_externos_conflitantes, 1)

    def test_c_proprio_e_externo_detecta_externo(self):
        rows = [
            {
                "relation_name": "envios_sede",
                "granted": True,
                "state": "active",
                "pid": 100,
                "application_name": "shell",
                "lock_mode": "AccessShareLock",
            },
            {
                "relation_name": "envios_sede",
                "granted": True,
                "state": "active",
                "pid": 300,
                "application_name": "gunicorn",
                "lock_mode": "RowExclusiveLock",
            },
        ]
        summary = diag._detectar_lock_envio_sede(rows, pid_atual=100)
        self.assertTrue(summary.tem_lock_conflitante_envio_sede)
        self.assertEqual(summary.pid_bloqueador, "300")
        self.assertEqual(summary.locks_observados, 2)
        self.assertEqual(summary.locks_externos_conflitantes, 1)

    def test_d_sem_lock_externo(self):
        rows = [
            {
                "relation_name": "pagamentos_obrigacao",
                "granted": True,
                "state": "active",
                "pid": 200,
                "application_name": "gunicorn",
                "lock_mode": "AccessShareLock",
            }
        ]
        summary = diag._detectar_lock_envio_sede(rows, pid_atual=100)
        self.assertFalse(summary.tem_lock_conflitante_envio_sede)
        self.assertEqual(summary.locks_observados, 0)
        self.assertEqual(summary.locks_externos_conflitantes, 0)

    def test_e_pid_atual_nunca_bloqueador(self):
        rows = [
            {
                "relation_name": "envios_sede",
                "granted": True,
                "state": "active",
                "pid": 100,
                "application_name": "shell",
                "lock_mode": "AccessShareLock",
            },
            {
                "relation_name": "envios_sede",
                "granted": True,
                "state": "active",
                "pid": 200,
                "application_name": "outra",
                "lock_mode": "RowExclusiveLock",
            },
        ]
        summary = diag._detectar_lock_envio_sede(rows, pid_atual=100)
        self.assertNotEqual(summary.pid_bloqueador, "100")

    def test_f_idle_in_transaction_externo_detectado(self):
        activities = [
            {"pid": 100, "state": "active", "xact_start": "2026-08-14 10:00:00", "application_name": "shell"},
            {"pid": 200, "state": "idle in transaction", "xact_start": "2026-08-14 09:59:00", "application_name": "gunicorn"},
        ]
        met = diag._metricas_transacoes_externas(activities, pid_atual=100)
        self.assertEqual(met["transacoes_idle"], 1)
        self.assertEqual(met["transacoes_abertas"], 1)

    def test_g_propria_transacao_nao_contada_como_externa(self):
        activities = [
            {"pid": 100, "state": "idle in transaction", "xact_start": "2026-08-14 10:00:00", "application_name": "shell"},
        ]
        met = diag._metricas_transacoes_externas(activities, pid_atual=100)
        self.assertEqual(met["transacoes_idle"], 0)
        self.assertEqual(met["transacoes_abertas"], 0)

    def test_h_persistencia_permanece_zero_no_fluxo(self):
        class _Ctx:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        class _FakeApp:
            def app_context(self):
                return _Ctx()

        class _Dialect:
            name = "postgresql"

        class _Engine:
            dialect = _Dialect()

        class _DB:
            engine = _Engine()

        with patch.object(diag, "novo_app", return_value=_FakeApp()), \
             patch.object(diag, "db", _DB()), \
             patch.object(diag, "_query_pid_atual", return_value=100), \
             patch.object(diag, "_snapshot_counts", side_effect=[
                 {"pagamentos_obrigacao": 0, "pagamentos_obrigacao_itens": 0, "lancamentos": 10, "envios_sede": 4},
                 {"pagamentos_obrigacao": 0, "pagamentos_obrigacao_itens": 0, "lancamentos": 10, "envios_sede": 4},
             ]), \
             patch.object(diag, "_query_pg_stat_activity", return_value=[]), \
             patch.object(diag, "_query_locks_tables_alvo", return_value=[]), \
             patch.object(diag, "_query_blocking_pairs", return_value=[]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = diag.main()

        self.assertEqual(rc, 0)
        self.assertIn("PERSISTENCIA_ALTERADA: NAO", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
