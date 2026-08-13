from __future__ import annotations

import unittest
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
    def test_a_check_nao_executa_ddl(self):
        with patch.object(exe, "inspecionar_schema", return_value=_status(estado=exe.ESTADO_A, apto=True)), \
             patch.object(exe, "_snapshot", return_value=_snap()), \
             patch.object(exe, "_print_status"), \
             patch.object(exe, "_aplicar_transacional") as aplicar_mock:
            rc = exe.executar_check()

        self.assertEqual(rc, 1)
        aplicar_mock.assert_not_called()

    def test_b_schema_ausente_estado_apto(self):
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

    def test_c_schema_completo_retorna_ja_aplicado(self):
        with patch.object(exe, "inspecionar_schema", return_value=_status(estado=exe.ESTADO_B)), \
             patch.object(exe, "_snapshot", return_value=_snap()), \
             patch.object(exe, "_print_status"):
            rc = exe.executar_check()
        self.assertEqual(rc, 0)

    def test_d_schema_parcial_bloqueado(self):
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

    def test_estado_incompativel_constraints_sem_coluna(self):
        estado, apto, motivo = exe._classificar_estado(
            tabela_envios=True,
            tabela_pagamentos=True,
            coluna_existe=False,
            coluna_nullable=False,
            tipo_coluna_compativel=False,
            fk_real=True,
            unique_real=False,
        )
        self.assertEqual(estado, exe.ESTADO_D)
        self.assertFalse(apto)
        self.assertIn("constraints", motivo or "")

    def test_e_dialeto_nao_postgresql_bloqueado(self):
        with patch.object(exe, "inspecionar_schema", return_value=_status(estado=exe.ESTADO_D, postgresql_ok=False, motivo="dialeto")), \
             patch.object(exe, "_snapshot", return_value=_snap()), \
             patch.object(exe, "_print_status"):
            rc = exe.executar_apply()
        self.assertEqual(rc, 1)

    def test_fgh_apply_emite_ddl_coluna_fk_unique(self):
        comandos = []

        class FakeConn:
            def execute(self, stmt):
                comandos.append(str(stmt))

        class FakeTx:
            def __enter__(self):
                return FakeConn()

            def __exit__(self, exc_type, exc, tb):
                return False

        class FakeEngine:
            def begin(self):
                return FakeTx()

        fake_db = type("DB", (), {"engine": FakeEngine()})

        with patch.object(exe, "db", fake_db):
            exe._aplicar_transacional("BIGINT")

        ddl = "\n".join(comandos).lower()
        self.assertIn("add column pagamento_obrigacao_id bigint", ddl)
        self.assertIn(f"add constraint {exe.UNIQUE_NAME}".lower(), ddl)
        self.assertIn(f"add constraint {exe.FK_NAME}".lower(), ddl)

    def test_i_historico_permanece_null_sem_dml(self):
        with open("scripts/apply_d23d1_schema.py", "r", encoding="utf-8") as f:
            conteudo = f.read().lower()

        self.assertNotIn("insert into", conteudo)
        self.assertNotIn(" update ", f" {conteudo} ")
        self.assertNotIn("delete from", conteudo)

    def test_j_zero_dml_de_negocio_no_executor(self):
        with open("scripts/apply_d23d1_schema.py", "r", encoding="utf-8") as f:
            conteudo = f.read().lower()

        self.assertNotIn("registrar_pagamento_obrigacao", conteudo)
        self.assertNotIn("registrar_pagamento_obrigacoes", conteudo)
        self.assertNotIn("_sincronizar_lancamento_repasse_sede", conteudo)

    def test_k_reexecucao_segura_ja_aplicado(self):
        with patch.object(exe, "inspecionar_schema", return_value=_status(estado=exe.ESTADO_B)), \
             patch.object(exe, "_snapshot", return_value=_snap()), \
             patch.object(exe, "_print_status"), \
             patch.object(exe, "_aplicar_transacional") as aplicar_mock:
            rc = exe.executar_apply()

        self.assertEqual(rc, 0)
        aplicar_mock.assert_not_called()

    def test_l_falha_intermediaria_gera_rollback_transacional(self):
        estado = {"rollback": False, "commit": False, "exec_count": 0}

        class FakeConn:
            def execute(self, stmt):
                estado["exec_count"] += 1
                if estado["exec_count"] == 2:
                    raise RuntimeError("falha no segundo DDL")

        class FakeTx:
            def __enter__(self):
                return FakeConn()

            def __exit__(self, exc_type, exc, tb):
                if exc_type is None:
                    estado["commit"] = True
                else:
                    estado["rollback"] = True
                return False

        class FakeEngine:
            def begin(self):
                return FakeTx()

        fake_db = type("DB", (), {"engine": FakeEngine()})

        with patch.object(exe, "db", fake_db):
            with self.assertRaises(RuntimeError):
                exe._aplicar_transacional("INTEGER")

        self.assertTrue(estado["rollback"])
        self.assertFalse(estado["commit"])

    def test_poscheck_automatico_apos_apply(self):
        status_seq = [
            _status(estado=exe.ESTADO_A, apto=True),
            _status(estado=exe.ESTADO_B),
        ]
        snap_seq = [_snap(), _snap()]

        with patch.object(exe, "inspecionar_schema", side_effect=status_seq) as inspec_mock, \
             patch.object(exe, "_snapshot", side_effect=snap_seq), \
             patch.object(exe, "_print_status"), \
             patch.object(exe, "_contar_orfaos", return_value=0), \
             patch.object(exe, "_aplicar_transacional"):
            rc = exe.executar_apply()

        self.assertEqual(rc, 0)
        self.assertEqual(inspec_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()
