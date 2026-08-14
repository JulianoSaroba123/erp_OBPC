from __future__ import annotations

import unittest
import io
from contextlib import redirect_stdout
from unittest.mock import patch

import scripts.apply_d23d1_schema as exe


def _snap() -> exe.Snapshot:
    return exe.Snapshot(
        pagamentos_obrigacao=10,
        pagamentos_obrigacao_itens=20,
        lancamentos=30,
        envios_sede=40,
        saldo_lancamentos=123.45,
    )


def _status(*, estado: str, postgresql_ok: bool = True, apto: bool = False, motivo: str | None = None) -> exe.SchemaStatus:
    return exe.SchemaStatus(
        dialeto="postgresql" if postgresql_ok else "sqlite",
        postgresql_ok=postgresql_ok,
        tabela_envios_sede=True,
        tabela_pagamentos_obrigacao=True,
        coluna_existe=(estado != exe.ESTADO_A),
        coluna_nullable=(estado != exe.ESTADO_A),
        tipo_coluna_compativel=(estado != exe.ESTADO_A),
        fk_real=(estado == exe.ESTADO_B),
        unique_real=(estado == exe.ESTADO_B),
        fk_tabela_destino="pagamentos_obrigacao" if estado == exe.ESTADO_B else "-",
        fk_coluna_destino="id" if estado == exe.ESTADO_B else "-",
        id_type_sql="INTEGER",
        estado_schema=estado,
        apto_para_aplicar=apto,
        motivo_bloqueio=motivo,
    )


class TestApplyD23D1SchemaExecutor(unittest.TestCase):
    def test_a_precheck_fecha_conexao_antes_ddl(self):
        estado = {"check_closed": False}

        class FakeConn:
            def execute(self, stmt):
                sql = str(stmt).lower()
                if "pg_backend_pid" in sql:
                    return _Rows({"pid": 111})
                return _Rows({})

        class Ctx:
            def __init__(self, conn, on_exit=None):
                self.conn = conn
                self.on_exit = on_exit

            def __enter__(self):
                return self.conn

            def __exit__(self, exc_type, exc, tb):
                if self.on_exit:
                    self.on_exit()
                return False

        class Engine:
            def __init__(self):
                self.calls = 0

            def connect(self):
                self.calls += 1
                if self.calls == 1:
                    return Ctx(FakeConn(), on_exit=lambda: estado.__setitem__("check_closed", True))
                return Ctx(FakeConn())

        fake_db = _FakeDB(engine=Engine())
        status_seq = [_status(estado=exe.ESTADO_A, apto=True), _status(estado=exe.ESTADO_B)]

        def _aplicar(_):
            if not estado["check_closed"]:
                raise AssertionError("check ainda aberto antes do DDL")

        with patch.object(exe, "db", fake_db), \
             patch.object(exe, "inspecionar_schema_conn", side_effect=status_seq), \
             patch.object(exe, "_snapshot_conn", side_effect=[_snap(), _snap()]), \
             patch.object(exe, "_contar_orfaos_conn", return_value=0), \
             patch.object(exe, "_print_status"), \
             patch.object(exe, "_aplicar_transacional", side_effect=_aplicar):
            rc = exe.executar_apply()

        self.assertEqual(rc, 0)
        self.assertTrue(estado["check_closed"])

    def test_b_db_session_limpa_antes_ddl(self):
        class FakeConn:
            def execute(self, stmt):
                if "pg_backend_pid" in str(stmt).lower():
                    return _Rows({"pid": 1})
                return _Rows({})

        class Ctx:
            def __enter__(self):
                return FakeConn()

            def __exit__(self, exc_type, exc, tb):
                return False

        class Engine:
            def connect(self):
                return Ctx()

        sess = _FakeSession()
        fake_db = _FakeDB(engine=Engine(), session=sess)

        with patch.object(exe, "db", fake_db), \
             patch.object(exe, "inspecionar_schema_conn", side_effect=[_status(estado=exe.ESTADO_A, apto=True), _status(estado=exe.ESTADO_B)]), \
             patch.object(exe, "_snapshot_conn", side_effect=[_snap(), _snap()]), \
             patch.object(exe, "_contar_orfaos_conn", return_value=0), \
             patch.object(exe, "_print_status"), \
             patch.object(exe, "_aplicar_transacional"):
            rc = exe.executar_apply()

        self.assertEqual(rc, 0)
        self.assertTrue(sess.rollback_called)
        self.assertTrue(sess.remove_called)

    def test_c_ddl_inicia_so_apos_fase_leitura(self):
        trilha = []

        class FakeConn:
            def execute(self, stmt):
                if "pg_backend_pid" in str(stmt).lower():
                    return _Rows({"pid": 1})
                return _Rows({})

        class Ctx:
            def __enter__(self):
                trilha.append("check_enter")
                return FakeConn()

            def __exit__(self, exc_type, exc, tb):
                trilha.append("check_exit")
                return False

        class CtxPost:
            def __enter__(self):
                trilha.append("post_enter")
                return FakeConn()

            def __exit__(self, exc_type, exc, tb):
                trilha.append("post_exit")
                return False

        class Engine:
            def __init__(self):
                self.calls = 0

            def connect(self):
                self.calls += 1
                return Ctx() if self.calls == 1 else CtxPost()

        fake_db = _FakeDB(engine=Engine(), session=_FakeSession())

        def aplicar(_):
            trilha.append("ddl")

        with patch.object(exe, "db", fake_db), \
             patch.object(exe, "inspecionar_schema_conn", side_effect=[_status(estado=exe.ESTADO_A, apto=True), _status(estado=exe.ESTADO_B)]), \
             patch.object(exe, "_snapshot_conn", side_effect=[_snap(), _snap()]), \
             patch.object(exe, "_contar_orfaos_conn", return_value=0), \
             patch.object(exe, "_print_status"), \
             patch.object(exe, "_aplicar_transacional", side_effect=aplicar):
            rc = exe.executar_apply()

        self.assertEqual(rc, 0)
        self.assertEqual(trilha[:3], ["check_enter", "check_exit", "ddl"])

    def test_d_lock_timeout_preservado(self):
        comandos = []

        class FakeConn:
            def execute(self, stmt):
                comandos.append(str(stmt).lower())
                return _Rows({"pid": 77}) if "pg_backend_pid" in str(stmt).lower() else _Rows({})

        class Tx:
            def __enter__(self):
                return FakeConn()

            def __exit__(self, exc_type, exc, tb):
                return False

        class Engine:
            def begin(self):
                return Tx()

        with patch.object(exe, "db", _FakeDB(engine=Engine())):
            exe._aplicar_transacional("INTEGER")

        self.assertTrue(any("set local lock_timeout" in c for c in comandos))

    def test_e_statement_timeout_preservado(self):
        comandos = []

        class FakeConn:
            def execute(self, stmt):
                comandos.append(str(stmt).lower())
                return _Rows({"pid": 77}) if "pg_backend_pid" in str(stmt).lower() else _Rows({})

        class Tx:
            def __enter__(self):
                return FakeConn()

            def __exit__(self, exc_type, exc, tb):
                return False

        class Engine:
            def begin(self):
                return Tx()

        with patch.object(exe, "db", _FakeDB(engine=Engine())):
            exe._aplicar_transacional("INTEGER")

        self.assertTrue(any("set local statement_timeout" in c for c in comandos))

    def test_f_erro_ddl_causa_rollback_total(self):
        estado = {"rollback": False, "commit": False, "count": 0}

        class FakeConn:
            def execute(self, stmt):
                estado["count"] += 1
                if estado["count"] == 3:
                    raise RuntimeError("erro no ddl")
                return _Rows({"pid": 88}) if "pg_backend_pid" in str(stmt).lower() else _Rows({})

        class Tx:
            def __enter__(self):
                return FakeConn()

            def __exit__(self, exc_type, exc, tb):
                if exc_type is None:
                    estado["commit"] = True
                else:
                    estado["rollback"] = True
                return False

        class Engine:
            def begin(self):
                return Tx()

        with patch.object(exe, "db", _FakeDB(engine=Engine())):
            with self.assertRaises(RuntimeError):
                exe._aplicar_transacional("INTEGER")

        self.assertTrue(estado["rollback"])
        self.assertFalse(estado["commit"])

    def test_g_schema_parcial_continua_bloqueado(self):
        class FakeConn:
            def execute(self, stmt):
                if "pg_backend_pid" in str(stmt).lower():
                    return _Rows({"pid": 1})
                return _Rows({})

        class Ctx:
            def __enter__(self):
                return FakeConn()

            def __exit__(self, exc_type, exc, tb):
                return False

        class Engine:
            def connect(self):
                return Ctx()

        with patch.object(exe, "db", _FakeDB(engine=Engine(), session=_FakeSession())), \
             patch.object(exe, "inspecionar_schema_conn", return_value=_status(estado=exe.ESTADO_C, apto=False, motivo="schema parcial")), \
             patch.object(exe, "_snapshot_conn", return_value=_snap()), \
             patch.object(exe, "_print_status"), \
             patch.object(exe, "_aplicar_transacional") as aplicar_mock:
            rc = exe.executar_apply()

        self.assertEqual(rc, 1)
        aplicar_mock.assert_not_called()

    def test_h_reexecucao_segura_ja_aplicado(self):
        class FakeConn:
            def execute(self, stmt):
                if "pg_backend_pid" in str(stmt).lower():
                    return _Rows({"pid": 1})
                return _Rows({})

        class Ctx:
            def __enter__(self):
                return FakeConn()

            def __exit__(self, exc_type, exc, tb):
                return False

        class Engine:
            def connect(self):
                return Ctx()

        with patch.object(exe, "db", _FakeDB(engine=Engine(), session=_FakeSession())), \
             patch.object(exe, "inspecionar_schema_conn", return_value=_status(estado=exe.ESTADO_B)), \
             patch.object(exe, "_snapshot_conn", return_value=_snap()), \
             patch.object(exe, "_print_status"), \
             patch.object(exe, "_aplicar_transacional") as aplicar_mock:
            rc = exe.executar_apply()

        self.assertEqual(rc, 0)
        aplicar_mock.assert_not_called()

    def test_i_zero_insert(self):
        with open("scripts/apply_d23d1_schema.py", "r", encoding="utf-8") as f:
            conteudo = f.read().lower()
        self.assertNotIn("insert into", conteudo)

    def test_j_zero_update(self):
        with open("scripts/apply_d23d1_schema.py", "r", encoding="utf-8") as f:
            conteudo = f.read().lower()
        self.assertNotIn(" update ", f" {conteudo} ")

    def test_k_zero_delete(self):
        with open("scripts/apply_d23d1_schema.py", "r", encoding="utf-8") as f:
            conteudo = f.read().lower()
        self.assertNotIn("delete from", conteudo)

    def test_l_snapshots_financeiros_preservados(self):
        snap_before = _snap()
        snap_after = _snap()

        class FakeConn:
            def execute(self, stmt):
                return _Rows({"pid": 1}) if "pg_backend_pid" in str(stmt).lower() else _Rows({})

        class Ctx:
            def __enter__(self):
                return FakeConn()

            def __exit__(self, exc_type, exc, tb):
                return False

        class Engine:
            def connect(self):
                return Ctx()

        with patch.object(exe, "db", _FakeDB(engine=Engine(), session=_FakeSession())), \
             patch.object(exe, "inspecionar_schema_conn", side_effect=[_status(estado=exe.ESTADO_A, apto=True), _status(estado=exe.ESTADO_B)]), \
             patch.object(exe, "_snapshot_conn", side_effect=[snap_before, snap_after]), \
             patch.object(exe, "_contar_orfaos_conn", return_value=0), \
             patch.object(exe, "_print_status"), \
             patch.object(exe, "_aplicar_transacional"):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = exe.executar_apply()

        self.assertEqual(rc, 0)
        self.assertIn("PERSISTENCIA_ALTERADA: NAO", buf.getvalue())

    def test_m_poscheck_usa_conexao_nova(self):
        conexoes = []

        class FakeConn:
            def __init__(self, nome):
                self.nome = nome

            def execute(self, stmt):
                if "pg_backend_pid" in str(stmt).lower():
                    return _Rows({"pid": 100 if self.nome == "check" else 200})
                return _Rows({})

        class Ctx:
            def __init__(self, conn):
                self.conn = conn

            def __enter__(self):
                conexoes.append(self.conn.nome)
                return self.conn

            def __exit__(self, exc_type, exc, tb):
                return False

        class Engine:
            def __init__(self):
                self.calls = 0

            def connect(self):
                self.calls += 1
                nome = "check" if self.calls == 1 else "poscheck"
                return Ctx(FakeConn(nome))

        with patch.object(exe, "db", _FakeDB(engine=Engine(), session=_FakeSession())), \
             patch.object(exe, "inspecionar_schema_conn", side_effect=[_status(estado=exe.ESTADO_A, apto=True), _status(estado=exe.ESTADO_B)]), \
             patch.object(exe, "_snapshot_conn", side_effect=[_snap(), _snap()]), \
             patch.object(exe, "_contar_orfaos_conn", return_value=0), \
             patch.object(exe, "_print_status"), \
             patch.object(exe, "_aplicar_transacional"):
            rc = exe.executar_apply()

        self.assertEqual(rc, 0)
        self.assertEqual(conexoes, ["check", "poscheck"])

    def test_n_conexao_check_nao_permanece_aberta(self):
        estado = {"aberta": False, "fechada": False}

        class FakeConn:
            def execute(self, stmt):
                if "pg_backend_pid" in str(stmt).lower():
                    return _Rows({"pid": 10})
                return _Rows({})

        class Ctx:
            def __enter__(self):
                estado["aberta"] = True
                return FakeConn()

            def __exit__(self, exc_type, exc, tb):
                estado["aberta"] = False
                estado["fechada"] = True
                return False

        class CtxPost:
            def __enter__(self):
                return FakeConn()

            def __exit__(self, exc_type, exc, tb):
                return False

        class Engine:
            def __init__(self):
                self.calls = 0

            def connect(self):
                self.calls += 1
                return Ctx() if self.calls == 1 else CtxPost()

        def aplicar(_):
            if estado["aberta"]:
                raise AssertionError("conexao de check ainda aberta")

        with patch.object(exe, "db", _FakeDB(engine=Engine(), session=_FakeSession())), \
             patch.object(exe, "inspecionar_schema_conn", side_effect=[_status(estado=exe.ESTADO_A, apto=True), _status(estado=exe.ESTADO_B)]), \
             patch.object(exe, "_snapshot_conn", side_effect=[_snap(), _snap()]), \
             patch.object(exe, "_contar_orfaos_conn", return_value=0), \
             patch.object(exe, "_print_status"), \
             patch.object(exe, "_aplicar_transacional", side_effect=aplicar):
            rc = exe.executar_apply()

        self.assertEqual(rc, 0)
        self.assertTrue(estado["fechada"])

    def test_o_reproducao_explicita_autolock_harness(self):
        class LockSim:
            def __init__(self):
                self.read_lock_aberto = False

            def open_read(self):
                self.read_lock_aberto = True

            def close_read(self):
                self.read_lock_aberto = False

            def alter_table(self):
                if self.read_lock_aberto:
                    raise RuntimeError("canceling statement due to lock timeout")
                return "ok"

        sim = LockSim()
        sim.open_read()
        with self.assertRaises(RuntimeError):
            sim.alter_table()
        sim.close_read()
        self.assertEqual(sim.alter_table(), "ok")

    def test_classificacao_estado_a_apto(self):
        estado, apto, motivo = exe._classificar_estado(
            tabela_envios=True,
            tabela_pagamentos=True,
            coluna_existe=False,
            coluna_nullable=False,
            tipo_coluna_compativel=False,
            fk_real=False,
            unique_real=False,
        )
        self.assertEqual(estado, exe.ESTADO_A)
        self.assertTrue(apto)
        self.assertIsNone(motivo)

    def test_check_schema_completo_retorna_ja_aplicado(self):
        class FakeConn:
            def execute(self, stmt):
                if "pg_backend_pid" in str(stmt).lower():
                    return _Rows({"pid": 1})
                return _Rows({})

        class Ctx:
            def __enter__(self):
                return FakeConn()

            def __exit__(self, exc_type, exc, tb):
                return False

        class Engine:
            def connect(self):
                return Ctx()

        with patch.object(exe, "db", _FakeDB(engine=Engine(), session=_FakeSession())), \
             patch.object(exe, "inspecionar_schema_conn", return_value=_status(estado=exe.ESTADO_B)), \
             patch.object(exe, "_snapshot_conn", return_value=_snap()), \
             patch.object(exe, "_print_status"):
            rc = exe.executar_check()
        self.assertEqual(rc, 0)

    def test_classificacao_schema_parcial_bloqueado(self):
        estado, apto, motivo = exe._classificar_estado(
            tabela_envios=True,
            tabela_pagamentos=True,
            coluna_existe=True,
            coluna_nullable=True,
            tipo_coluna_compativel=True,
            fk_real=False,
            unique_real=True,
        )
        self.assertEqual(estado, exe.ESTADO_C)
        self.assertFalse(apto)
        self.assertIn("schema parcial", motivo or "")

    def test_lock_timeout_abort_controlado(self):
        status_seq = [
            _status(estado=exe.ESTADO_A, apto=True),
            _status(estado=exe.ESTADO_A, apto=True),
        ]
        buf = io.StringIO()
        class FakeConn:
            def execute(self, stmt):
                if "pg_backend_pid" in str(stmt).lower():
                    return _Rows({"pid": 1})
                return _Rows({})

        class Ctx:
            def __enter__(self):
                return FakeConn()

            def __exit__(self, exc_type, exc, tb):
                return False

        class Engine:
            def connect(self):
                return Ctx()

        with patch.object(exe, "db", _FakeDB(engine=Engine(), session=_FakeSession())), \
             patch.object(exe, "inspecionar_schema_conn", side_effect=status_seq), \
             patch.object(exe, "_snapshot_conn", return_value=_snap()), \
             patch.object(exe, "_print_status"), \
             patch.object(exe, "_aplicar_transacional", side_effect=RuntimeError("canceling statement due to lock timeout")):
            with redirect_stdout(buf):
                rc = exe.executar_apply()

        out = buf.getvalue()
        self.assertEqual(rc, 1)
        self.assertIn("LOCK_TIMEOUT_DETECTADO: SIM", out)
        self.assertIn("RESULTADO_APLICACAO_SCHEMA: BLOQUEADO", out)


class _Rows:
    def __init__(self, row):
        self._row = row

    def mappings(self):
        return self

    def first(self):
        return self._row


class _FakeSession:
    def __init__(self):
        self.rollback_called = False
        self.remove_called = False

    def rollback(self):
        self.rollback_called = True

    def remove(self):
        self.remove_called = True


class _FakeDB:
    def __init__(self, engine, session=None):
        self.engine = engine
        self.session = session if session is not None else _FakeSession()


if __name__ == "__main__":
    unittest.main()
