from __future__ import annotations

import unittest
from decimal import Decimal

import scripts.regularizar_historico_sede_d23d22 as exe


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


def _fixture_baseline_d23d21():
    obrigacoes = [
        {"id": 6, "competencia_mes": 1, "competencia_ano": 2026, "valor_devido": Decimal("1240.95"), "status": "PARCIAL", "origem_obrigacao": "automatico", "tipo_obrigacao": "ADMIN_SEDE_30"},
        {"id": 7, "competencia_mes": 2, "competencia_ano": 2026, "valor_devido": Decimal("1361.01"), "status": "PAGO", "origem_obrigacao": "automatico", "tipo_obrigacao": "ADMIN_SEDE_30"},
        {"id": 8, "competencia_mes": 3, "competencia_ano": 2026, "valor_devido": Decimal("1829.11"), "status": "PAGO", "origem_obrigacao": "automatico", "tipo_obrigacao": "ADMIN_SEDE_30"},
        {"id": 9, "competencia_mes": 4, "competencia_ano": 2026, "valor_devido": Decimal("1865.34"), "status": "PARCIAL", "origem_obrigacao": "automatico", "tipo_obrigacao": "ADMIN_SEDE_30"},
        {"id": 10, "competencia_mes": 5, "competencia_ano": 2026, "valor_devido": Decimal("1145.59"), "status": "PENDENTE", "origem_obrigacao": "automatico", "tipo_obrigacao": "ADMIN_SEDE_30"},
        {"id": 11, "competencia_mes": 6, "competencia_ano": 2026, "valor_devido": Decimal("2403.31"), "status": "PENDENTE", "origem_obrigacao": "automatico", "tipo_obrigacao": "ADMIN_SEDE_30"},
        {"id": 12, "competencia_mes": 7, "competencia_ano": 2026, "valor_devido": Decimal("1122.56"), "status": "PENDENTE", "origem_obrigacao": "automatico", "tipo_obrigacao": "ADMIN_SEDE_30"},
    ]

    pagamentos = [
        {"id": 3, "data_pagamento": "2026-01-01", "valor_pago": Decimal("1240.00"), "forma_pagamento": "Dinheiro", "tipo_pagamento": "HISTORICO_SEM_MOVIMENTACAO", "observacao": "BOOTSTRAP_D23D16_COMP_01_2026", "lancamento_financeiro_id": None},
        {"id": 4, "data_pagamento": "2026-02-01", "valor_pago": Decimal("1361.01"), "forma_pagamento": "Dinheiro", "tipo_pagamento": "HISTORICO_SEM_MOVIMENTACAO", "observacao": "BOOTSTRAP_D23D16_COMP_02_2026", "lancamento_financeiro_id": None},
        {"id": 5, "data_pagamento": "2026-07-04", "valor_pago": Decimal("1829.11"), "forma_pagamento": "Dinheiro", "tipo_pagamento": "HISTORICO_SEM_MOVIMENTACAO", "observacao": "BOOTSTRAP_D23D16_COMP_03_2026", "lancamento_financeiro_id": None},
        {"id": 6, "data_pagamento": "2026-07-04", "valor_pago": Decimal("654.49"), "forma_pagamento": "Dinheiro", "tipo_pagamento": "HISTORICO_SEM_MOVIMENTACAO", "observacao": "BOOTSTRAP_D23D16_COMP_04_2026", "lancamento_financeiro_id": None},
    ]

    itens = [
        {"id": 3, "pagamento_obrigacao_id": 3, "obrigacao_financeira_id": 6, "valor_alocado": Decimal("1240.00"), "competencia_mes": 1, "competencia_ano": 2026},
        {"id": 4, "pagamento_obrigacao_id": 4, "obrigacao_financeira_id": 7, "valor_alocado": Decimal("1361.01"), "competencia_mes": 2, "competencia_ano": 2026},
        {"id": 5, "pagamento_obrigacao_id": 5, "obrigacao_financeira_id": 8, "valor_alocado": Decimal("1829.11"), "competencia_mes": 3, "competencia_ano": 2026},
        {"id": 6, "pagamento_obrigacao_id": 6, "obrigacao_financeira_id": 9, "valor_alocado": Decimal("654.49"), "competencia_mes": 4, "competencia_ano": 2026},
    ]

    envios = [
        {"id": 15, "pagamento_obrigacao_id": 3, "competencia_mes": 1, "competencia_ano": 2026, "competencia_mes_ref": 1, "competencia_ano_ref": 2026, "valor_despesas_fixas": Decimal("280.00"), "valor_administrativo": Decimal("1240.00"), "valor_total": Decimal("1520.00")},
        {"id": 16, "pagamento_obrigacao_id": 4, "competencia_mes": 2, "competencia_ano": 2026, "competencia_mes_ref": 2, "competencia_ano_ref": 2026, "valor_despesas_fixas": Decimal("280.00"), "valor_administrativo": Decimal("1361.01"), "valor_total": Decimal("1641.01")},
        {"id": 17, "pagamento_obrigacao_id": 5, "competencia_mes": 3, "competencia_ano": 2026, "competencia_mes_ref": 3, "competencia_ano_ref": 2026, "valor_despesas_fixas": Decimal("280.00"), "valor_administrativo": Decimal("1829.11"), "valor_total": Decimal("2109.11")},
        {"id": 18, "pagamento_obrigacao_id": 6, "competencia_mes": 4, "competencia_ano": 2026, "competencia_mes_ref": 4, "competencia_ano_ref": 2026, "valor_despesas_fixas": Decimal("280.00"), "valor_administrativo": Decimal("654.49"), "valor_total": Decimal("934.49")},
    ]

    return {
        "obrigacoes": obrigacoes,
        "pagamentos": pagamentos,
        "itens": itens,
        "envios": envios,
    }


class TestRegularizarHistoricoSedeD23D22(unittest.TestCase):
    def test_01_check_sql_readonly(self):
        self.assertTrue(exe.assert_sql_set_readonly(exe.CHECK_SQL_STATEMENTS))

    def test_02_janeiro_fecha_095(self):
        existing = _fixture_baseline_d23d21()
        ops = exe._build_operations(existing)
        sim = exe._simulate_apply(existing, ops)
        state = exe._build_state_table(sim)
        self.assertEqual(state[1]["saldo"], Decimal("0.00"))

    def test_03_abril_fecha_1210_85(self):
        existing = _fixture_baseline_d23d21()
        ops = exe._build_operations(existing)
        sim = exe._simulate_apply(existing, ops)
        state = exe._build_state_table(sim)
        self.assertEqual(state[4]["saldo"], Decimal("0.00"))

    def test_04_composicao_abril_1000_pix_210_85_especie(self):
        existing = _fixture_baseline_d23d21()
        ops = exe._build_operations(existing)
        abr_ops = [o for o in ops if o.competencia_mes == 4]
        self.assertEqual(len(abr_ops), 2)
        self.assertEqual(sum((o.valor_admin for o in abr_ops), Decimal("0.00")), Decimal("1210.85"))
        self.assertEqual(sorted([o.forma_pagamento for o in abr_ops]), ["Dinheiro", "PIX"])

    def test_05_maio_admin_1145_59(self):
        existing = _fixture_baseline_d23d21()
        ops = exe._build_operations(existing)
        maio = [o for o in ops if o.codigo == "D23D22_MAI_ADMIN_114559_FIXAS_280"]
        self.assertEqual(len(maio), 1)
        self.assertEqual(maio[0].valor_admin, Decimal("1145.59"))

    def test_06_maio_fixas_280_separadas(self):
        existing = _fixture_baseline_d23d21()
        ops = exe._build_operations(existing)
        maio = [o for o in ops if o.codigo == "D23D22_MAI_ADMIN_114559_FIXAS_280"][0]
        self.assertEqual(maio.valor_fixas, Decimal("280.00"))

    def test_07_maio_total_envio_1425_59(self):
        existing = _fixture_baseline_d23d21()
        ops = exe._build_operations(existing)
        maio = [o for o in ops if o.codigo == "D23D22_MAI_ADMIN_114559_FIXAS_280"][0]
        self.assertEqual(maio.valor_total_envio, Decimal("1425.59"))

    def test_08_nenhuma_saida_financeira_nova_no_plano(self):
        existing = _fixture_baseline_d23d21()
        ops = exe._build_operations(existing)
        self.assertTrue(all(o.codigo.startswith("D23D22_") for o in ops))

    def test_09_junho_permanece_2403_31(self):
        existing = _fixture_baseline_d23d21()
        ops = exe._build_operations(existing)
        sim = exe._simulate_apply(existing, ops)
        state = exe._build_state_table(sim)
        self.assertEqual(state[6]["saldo"], Decimal("2403.31"))

    def test_10_julho_intacto(self):
        existing = _fixture_baseline_d23d21()
        ops = exe._build_operations(existing)
        self.assertTrue(all(o.competencia_mes in {1, 4, 5} for o in ops))

    def test_11_idempotencia(self):
        existing = _fixture_baseline_d23d21()
        ops_1 = exe._build_operations(existing)
        sim = exe._simulate_apply(existing, ops_1)
        ops_2 = exe._build_operations(sim)
        self.assertEqual(len(ops_2), 0)

    def test_12_rollback_total(self):
        tx = _FakeTx()
        engine = _FakeEngine(tx)

        def _falha(_conn):
            raise RuntimeError("falha")

        with self.assertRaises(RuntimeError):
            exe.executar_em_transacao(engine, _falha)
        self.assertTrue(tx.rolled_back)
        self.assertFalse(tx.committed)


if __name__ == "__main__":
    unittest.main()
