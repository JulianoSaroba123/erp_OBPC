from decimal import Decimal
import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "regularizar_d23d48_projeto_filipe.py"
spec = importlib.util.spec_from_file_location("regularizar_d23d48_projeto_filipe", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class TestD23D48RegularizacaoHistorica(unittest.TestCase):
    def test_configuracao_estatica_fecha_com_banco(self):
        self.assertEqual(mod.validar_configuracao(), [])
        self.assertEqual(sum(mod.IMPORTADOS.values(), Decimal("0.00")), Decimal("3895.87"))
        self.assertEqual(
            mod.MANUAIS_DEPOIS[615] + mod.MANUAIS_DEPOIS[616] + mod.IMPORTADOS[664],
            Decimal("3895.87"),
        )

    def test_componentes_repasse_ficam_sem_projeto_filipe(self):
        self.assertEqual(
            sum(mod.IMPORTADOS[i] for i in mod.PARES[615]),
            Decimal("2573.31"),
        )
        self.assertEqual(
            sum(mod.IMPORTADOS[i] for i in mod.PARES[616]),
            Decimal("1292.56"),
        )
        self.assertNotIn(664, mod.PARES[615] + mod.PARES[616])
        self.assertEqual(mod.IMPORTADOS[664], Decimal("30.00"))

    def test_ajustes_envio_retiraram_exatamente_dez_reais(self):
        for _eid, (antes_total, depois_total, antes_fixas, depois_fixas, admin) in mod.ENVIOS.items():
            self.assertEqual(antes_total - depois_total, Decimal("10.00"))
            self.assertEqual(antes_fixas - depois_fixas, Decimal("10.00"))
            self.assertEqual(depois_total, admin + depois_fixas)

    def test_legados_neutralizados_sao_apenas_os_substituidos(self):
        self.assertEqual(set(mod.LEGADOS), {423, 516, 517, 518, 519})
        self.assertNotIn(515, mod.LEGADOS)

    def test_observacao_e_idempotente(self):
        base = "Importado via extrato"
        extra = f"{mod.MARKER}: teste"
        primeira = mod.obs_atualizada(base, extra)
        segunda = mod.obs_atualizada(primeira, extra)
        self.assertEqual(primeira, segunda)

    def test_normaliza_url_legada_postgres(self):
        self.assertEqual(
            mod.normalizar_url("postgres://usuario:senha@host/banco"),
            "postgresql://usuario:senha@host/banco",
        )


if __name__ == "__main__":
    unittest.main()
