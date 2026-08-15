from __future__ import annotations

import inspect
import unittest
from decimal import Decimal

import scripts.bootstrap_historico_obrigacoes_d23d16 as exe


class _FakeTx:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.committed = True
        else:
            self.rolled_back = True
        return False


class _FakeEngine:
    def __init__(self, tx: _FakeTx):
        self.tx = tx

    def begin(self):
        return self.tx


def _estado_b_fixture():
    obrigacoes = []
    for alvo in exe.OBRIGACOES_ALVO:
        obrigacoes.append(
            {
                "id": 100 + alvo["mes"],
                "competencia_mes": alvo["mes"],
                "competencia_ano": alvo["ano"],
                "valor_devido": alvo["devido"],
                "status": alvo["status"],
                "data_quitacao": alvo["data_quitacao"],
                "referencia_origem_tipo": "FECHAMENTO_MENSAL",
                "referencia_origem_id": exe.referencia_origem_id(alvo["mes"], alvo["ano"]),
                "origem_obrigacao": "automatico",
                "tipo_obrigacao": "ADMIN_SEDE_30",
            }
        )

    pagamentos = []
    itens = []
    envios = []
    for idx, alvo in enumerate(exe.PAGAMENTOS_ALVO, start=1):
        comp = exe.competencia_chave(alvo["mes"], alvo["ano"])
        pid = 200 + idx
        oid = 100 + alvo["mes"]
        pagamentos.append(
            {
                "id": pid,
                "data_pagamento": alvo["data"],
                "valor_pago": alvo["valor"],
                "forma_pagamento": "Dinheiro",
                "tipo_pagamento": "HISTORICO_SEM_MOVIMENTACAO",
                "observacao": exe.observacao_pagamento(alvo["mes"], alvo["ano"]),
                "lancamento_financeiro_id": None,
            }
        )
        itens.append(
            {
                "id": 300 + idx,
                "pagamento_obrigacao_id": pid,
                "obrigacao_financeira_id": oid,
                "valor_alocado": alvo["valor"],
            }
        )
        envios.append(
            {
                "id": alvo["envio_id"],
                "pagamento_obrigacao_id": pid,
            }
        )

    eventos = []
    for ob in obrigacoes:
        eventos.append({"id": 400 + ob["id"], "obrigacao_financeira_id": ob["id"], "evento_tipo": "CRIACAO"})
    for item in itens:
        eventos.append(
            {
                "id": 500 + item["id"],
                "obrigacao_financeira_id": item["obrigacao_financeira_id"],
                "evento_tipo": "PAGAMENTO",
            }
        )

    existing = {
        "obrigacoes": obrigacoes,
        "pagamentos": pagamentos,
        "itens": itens,
        "eventos": eventos,
    }
    return existing, envios


class TestBootstrapHistoricoD23D16(unittest.TestCase):
    def test_a_estado_vazio_apto(self):
        snapshot = {
            "TOTAL_OBRIGACOES": Decimal("0.00"),
            "TOTAL_PAGAMENTOS": Decimal("0.00"),
            "TOTAL_ITENS": Decimal("0.00"),
        }
        existing = {"obrigacoes": [], "pagamentos": [], "itens": [], "eventos": []}
        envios = [{"id": 15}, {"id": 16}, {"id": 17}, {"id": 18}]
        estado, _ = exe.classificar_estado(snapshot, True, envios, existing)
        self.assertEqual(estado, exe.ESTADO_A)

    def test_b_estado_ja_aplicado(self):
        snapshot = {
            "TOTAL_OBRIGACOES": Decimal("7.00"),
            "TOTAL_PAGAMENTOS": Decimal("4.00"),
            "TOTAL_ITENS": Decimal("4.00"),
        }
        existing, envios = _estado_b_fixture()
        estado, _ = exe.classificar_estado(snapshot, True, envios, existing)
        self.assertEqual(estado, exe.ESTADO_B)

    def test_c_estado_parcial_bloqueado(self):
        snapshot = {
            "TOTAL_OBRIGACOES": Decimal("1.00"),
            "TOTAL_PAGAMENTOS": Decimal("0.00"),
            "TOTAL_ITENS": Decimal("0.00"),
        }
        existing = {"obrigacoes": [], "pagamentos": [], "itens": [], "eventos": []}
        envios = [{"id": 15}, {"id": 16}, {"id": 17}, {"id": 18}]
        estado, _ = exe.classificar_estado(snapshot, True, envios, existing)
        self.assertEqual(estado, exe.ESTADO_C)

    def test_d_schema_incompativel_bloqueado(self):
        schema = {}
        fks = {}
        ok, problemas = exe.validate_schema(schema, fks)
        self.assertFalse(ok)
        self.assertTrue(any("tabela ausente" in p for p in problemas))

    def test_e_cria_7_obrigacoes_no_plano(self):
        envios = [
            {"id": 15, "pagamento_obrigacao_id": None, "valor_administrativo": 1240.00},
            {"id": 16, "pagamento_obrigacao_id": None, "valor_administrativo": 1361.01},
            {"id": 17, "pagamento_obrigacao_id": None, "valor_administrativo": 1829.11},
            {"id": 18, "pagamento_obrigacao_id": None, "valor_administrativo": 654.49},
        ]
        plan = exe.build_apply_plan(envios)
        self.assertEqual(len(plan["obrigacoes"]), 7)

    def test_f_cria_4_pagamentos_no_plano(self):
        envios = [
            {"id": 15, "pagamento_obrigacao_id": None, "valor_administrativo": 1240.00},
            {"id": 16, "pagamento_obrigacao_id": None, "valor_administrativo": 1361.01},
            {"id": 17, "pagamento_obrigacao_id": None, "valor_administrativo": 1829.11},
            {"id": 18, "pagamento_obrigacao_id": None, "valor_administrativo": 654.49},
        ]
        plan = exe.build_apply_plan(envios)
        self.assertEqual(len(plan["pagamentos"]), 4)

    def test_g_cria_4_itens_no_plano(self):
        envios = [
            {"id": 15, "pagamento_obrigacao_id": None, "valor_administrativo": 1240.00},
            {"id": 16, "pagamento_obrigacao_id": None, "valor_administrativo": 1361.01},
            {"id": 17, "pagamento_obrigacao_id": None, "valor_administrativo": 1829.11},
            {"id": 18, "pagamento_obrigacao_id": None, "valor_administrativo": 654.49},
        ]
        plan = exe.build_apply_plan(envios)
        self.assertEqual(len(plan["itens"]), 4)

    def test_h_eventos_corretos_no_plano(self):
        envios = [
            {"id": 15, "pagamento_obrigacao_id": None, "valor_administrativo": 1240.00},
            {"id": 16, "pagamento_obrigacao_id": None, "valor_administrativo": 1361.01},
            {"id": 17, "pagamento_obrigacao_id": None, "valor_administrativo": 1829.11},
            {"id": 18, "pagamento_obrigacao_id": None, "valor_administrativo": 654.49},
        ]
        plan = exe.build_apply_plan(envios)
        self.assertEqual(len(plan["eventos"]), 11)
        self.assertEqual(len([e for e in plan["eventos"] if e["tipo"] == "CRIACAO"]), 7)
        self.assertEqual(len([e for e in plan["eventos"] if e["tipo"] == "PAGAMENTO"]), 4)

    def test_i_reutiliza_envios_15_18(self):
        envios = [
            {"id": 15, "pagamento_obrigacao_id": None, "valor_administrativo": 1240.00},
            {"id": 16, "pagamento_obrigacao_id": None, "valor_administrativo": 1361.01},
            {"id": 17, "pagamento_obrigacao_id": None, "valor_administrativo": 1829.11},
            {"id": 18, "pagamento_obrigacao_id": None, "valor_administrativo": 654.49},
        ]
        plan = exe.build_apply_plan(envios)
        self.assertEqual(sorted([v["envio_id"] for v in plan["vinculos_envio"]]), [15, 16, 17, 18])

    def test_j_nao_cria_envio_novo(self):
        envios = [
            {"id": 15, "pagamento_obrigacao_id": None, "valor_administrativo": 1240.00},
            {"id": 16, "pagamento_obrigacao_id": None, "valor_administrativo": 1361.01},
            {"id": 17, "pagamento_obrigacao_id": None, "valor_administrativo": 1829.11},
            {"id": 18, "pagamento_obrigacao_id": None, "valor_administrativo": 654.49},
        ]
        plan = exe.build_apply_plan(envios)
        self.assertEqual(len(plan["vinculos_envio"]), 4)

    def test_k_nao_cria_lancamento(self):
        src = inspect.getsource(exe.aplicar_bootstrap)
        self.assertNotIn("INSERT INTO lancamentos", src)

    def test_l_movimentacao_caixa_preservada_por_regra(self):
        src = inspect.getsource(exe.aplicar_bootstrap)
        self.assertIn("MOVIMENTACAO_CAIXA_DETECTADA", src)
        self.assertIn("NOVOS_LANCAMENTOS_DETECTADOS", src)

    def test_m_status_corretos(self):
        expected = {
            "01/2026": "PARCIAL",
            "02/2026": "PAGO",
            "03/2026": "PAGO",
            "04/2026": "PARCIAL",
            "05/2026": "PENDENTE",
            "06/2026": "PENDENTE",
            "07/2026": "PENDENTE",
        }
        got = {exe.competencia_chave(x["mes"], x["ano"]): x["status"] for x in exe.OBRIGACOES_ALVO}
        self.assertEqual(got, expected)

    def test_n_datas_quitacao_corretas(self):
        comp = {exe.competencia_chave(x["mes"], x["ano"]): x["data_quitacao"] for x in exe.OBRIGACOES_ALVO}
        self.assertEqual(str(comp["02/2026"]), "2026-02-01")
        self.assertEqual(str(comp["03/2026"]), "2026-07-04")
        self.assertIsNone(comp["01/2026"])

    def test_o_valor_administrativo_e_base_do_item(self):
        envios = [
            {"id": 15, "pagamento_obrigacao_id": None, "valor_administrativo": 1240.00, "valor_total": 1520.00},
            {"id": 16, "pagamento_obrigacao_id": None, "valor_administrativo": 1361.01, "valor_total": 1641.01},
            {"id": 17, "pagamento_obrigacao_id": None, "valor_administrativo": 1829.11, "valor_total": 2109.11},
            {"id": 18, "pagamento_obrigacao_id": None, "valor_administrativo": 654.49, "valor_total": 934.49},
        ]
        plan = exe.build_apply_plan(envios)
        self.assertTrue(all(item["fonte_valor"] == "valor_administrativo" for item in plan["itens"]))

    def test_p_despesas_fixas_nao_entram(self):
        self.assertTrue(all(ob["tipo_obrigacao"] == "ADMIN_SEDE_30" for ob in [
            {
                "tipo_obrigacao": x["tipo_obrigacao"],
            }
            for x in exe.build_apply_plan([
                {"id": 15, "pagamento_obrigacao_id": None, "valor_administrativo": 1240.00},
                {"id": 16, "pagamento_obrigacao_id": None, "valor_administrativo": 1361.01},
                {"id": 17, "pagamento_obrigacao_id": None, "valor_administrativo": 1829.11},
                {"id": 18, "pagamento_obrigacao_id": None, "valor_administrativo": 654.49},
            ])["obrigacoes"]
        ]))

    def test_q_rollback_total_em_falha_intermediaria(self):
        tx = _FakeTx()
        engine = _FakeEngine(tx)

        def _falha(_conn):
            raise RuntimeError("falha")

        with self.assertRaises(RuntimeError):
            exe.executar_em_transacao(engine, _falha)
        self.assertTrue(tx.rolled_back)
        self.assertFalse(tx.committed)

    def test_r_segunda_execucao_idempotente_classifica_estado_b(self):
        snapshot = {
            "TOTAL_OBRIGACOES": Decimal("7.00"),
            "TOTAL_PAGAMENTOS": Decimal("4.00"),
            "TOTAL_ITENS": Decimal("4.00"),
        }
        existing, envios = _estado_b_fixture()
        estado, _ = exe.classificar_estado(snapshot, True, envios, existing)
        self.assertEqual(estado, exe.ESTADO_B)

    def test_s_postgresql_gate(self):
        self.assertEqual(exe.avaliar_gate_postgresql("postgresql"), (True, None))
        self.assertEqual(exe.avaliar_gate_postgresql("sqlite"), (False, "dialeto nao e postgresql"))

    def test_t_check_readonly(self):
        self.assertTrue(exe.assert_sql_set_readonly(exe.CHECK_SQL_STATEMENTS))

    def test_u_poscheck_total_5883_26(self):
        total_devido = sum((x["devido"] for x in exe.OBRIGACOES_ALVO), Decimal("0.00"))
        total_pago = sum((x["valor"] for x in exe.PAGAMENTOS_ALVO), Decimal("0.00"))
        self.assertEqual((total_devido - total_pago).quantize(Decimal("0.01")), Decimal("5883.26"))


if __name__ == "__main__":
    unittest.main()
