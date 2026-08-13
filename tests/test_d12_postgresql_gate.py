from __future__ import annotations

import unittest

import scripts.precheck_d12 as precheck_d12
import scripts.smoke_d12 as smoke_d12


class TestD12PostgresqlGate(unittest.TestCase):
    def test_precheck_postgresql_continua(self):
        self.assertEqual(precheck_d12.avaliar_gate_postgresql("postgresql"), (True, None))

    def test_precheck_sqlite_bloqueia(self):
        self.assertEqual(precheck_d12.avaliar_gate_postgresql("sqlite"), (False, "dialeto nao e postgresql"))

    def test_precheck_mysql_bloqueia(self):
        self.assertEqual(precheck_d12.avaliar_gate_postgresql("mysql"), (False, "dialeto nao e postgresql"))

    def test_smoke_postgresql_continua(self):
        self.assertEqual(smoke_d12.avaliar_gate_postgresql("postgresql"), (True, None))

    def test_smoke_sqlite_bloqueia(self):
        self.assertEqual(smoke_d12.avaliar_gate_postgresql("sqlite"), (False, "dialeto nao e postgresql"))

    def test_smoke_mysql_bloqueia(self):
        self.assertEqual(smoke_d12.avaliar_gate_postgresql("mysql"), (False, "dialeto nao e postgresql"))


if __name__ == "__main__":
    unittest.main()
