import importlib.util
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_module(module_name: str, script_path: str):
    path = ROOT / script_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Não foi possível carregar {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestD12LockDiagnostico(unittest.TestCase):
    def _assert_cenario(self, script_name: str, func_name: str, loader_text: str, helper_text: str, expected: str):
        module = load_module(f"d12_{script_name}", f"scripts/{script_name}")

        def fake_getsource(obj):
            nome = getattr(obj, "__name__", "")
            if nome == "_carregar_obrigacao_para_pagamento":
                return loader_text
            if nome == "_registrar_pagamento_obrigacao_sem_commit":
                return helper_text
            raise OSError(f"Fonte não mockada para {nome}")

        with mock.patch.object(module.py_inspect, "getsource", side_effect=fake_getsource):
            resultado = getattr(module, func_name)()
            self.assertEqual(resultado, expected, msg=f"{script_name}:{func_name} -> {resultado!r} != {expected!r}")

    def test_cenario_a_loader_com_lock_e_helper_chama_loader(self):
        loader_text = '''
def _carregar_obrigacao_para_pagamento(obrigacao_id: int):
    query = db.session.query(ObrigacaoFinanceira).filter(ObrigacaoFinanceira.id == obrigacao_id)
    query = query.with_for_update()
    return query.one_or_none()
'''
        helper_text = '''
def _registrar_pagamento_obrigacao_sem_commit(obrigacao_id: int, valor_pago, data_pagamento, forma_pagamento, tipo_pagamento):
    obrigacao = _carregar_obrigacao_para_pagamento(obrigacao_id)
    return obrigacao
'''

        self._assert_cenario("precheck_d12.py", "helper_usa_lock_pessimista", loader_text, helper_text, "SIM")
        self._assert_cenario("smoke_d12.py", "lock_pessimista_ativo", loader_text, helper_text, "SIM")

    def test_cenario_b_loader_sem_lock(self):
        loader_text = '''
def _carregar_obrigacao_para_pagamento(obrigacao_id: int):
    query = db.session.query(ObrigacaoFinanceira).filter(ObrigacaoFinanceira.id == obrigacao_id)
    return query.one_or_none()
'''
        helper_text = '''
def _registrar_pagamento_obrigacao_sem_commit(obrigacao_id: int, valor_pago, data_pagamento, forma_pagamento, tipo_pagamento):
    obrigacao = _carregar_obrigacao_para_pagamento(obrigacao_id)
    return obrigacao
'''

        self._assert_cenario("precheck_d12.py", "helper_usa_lock_pessimista", loader_text, helper_text, "NAO")
        self._assert_cenario("smoke_d12.py", "lock_pessimista_ativo", loader_text, helper_text, "NAO")

    def test_cenario_c_helper_nao_chama_loader(self):
        loader_text = '''
def _carregar_obrigacao_para_pagamento(obrigacao_id: int):
    query = db.session.query(ObrigacaoFinanceira).filter(ObrigacaoFinanceira.id == obrigacao_id)
    query = query.with_for_update()
    return query.one_or_none()
'''
        helper_text = '''
def _registrar_pagamento_obrigacao_sem_commit(obrigacao_id: int, valor_pago, data_pagamento, forma_pagamento, tipo_pagamento):
    return {"status": "ok"}
'''

        self._assert_cenario("precheck_d12.py", "helper_usa_lock_pessimista", loader_text, helper_text, "NAO")
        self._assert_cenario("smoke_d12.py", "lock_pessimista_ativo", loader_text, helper_text, "NAO")


if __name__ == "__main__":
    unittest.main(verbosity=2)
