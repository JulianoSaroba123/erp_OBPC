from __future__ import annotations

import unittest

import scripts.diagnostico_lock_d23d1 as diag


class TestDiagnosticoLockD23D1(unittest.TestCase):
    def test_a_sem_lock_conflitante(self):
        rows = [
            {
                "relation_name": "envios_sede",
                "granted": True,
                "state": "idle",
                "pid": 100,
                "application_name": "gunicorn",
                "lock_mode": "AccessShareLock",
            }
        ]
        summary = diag._detectar_lock_envio_sede(rows)
        self.assertFalse(summary.tem_lock_conflitante_envio_sede)
        self.assertEqual(summary.pid_bloqueador, "-")

    def test_b_lock_conflitante_detectado(self):
        rows = [
            {
                "relation_name": "envios_sede",
                "granted": True,
                "state": "active",
                "pid": 321,
                "application_name": "gunicorn: worker",
                "lock_mode": "RowExclusiveLock",
            }
        ]
        summary = diag._detectar_lock_envio_sede(rows)
        self.assertTrue(summary.tem_lock_conflitante_envio_sede)
        self.assertEqual(summary.pid_bloqueador, "321")
        self.assertEqual(summary.tipo_lock_bloqueador, "RowExclusiveLock")
        self.assertEqual(summary.origem_provavel, "gunicorn")


if __name__ == "__main__":
    unittest.main()
