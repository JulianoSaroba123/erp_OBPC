import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LISTA = ROOT / "app" / "financeiro" / "templates" / "financeiro" / "lista_lancamentos.html"
BASE = ROOT / "app" / "templates" / "base.html"


class D23D66MenuRelatoriosUnificadoTest(unittest.TestCase):
    def test_movimentacoes_nao_exibe_dropdown_duplicado_de_relatorios(self):
        src = LISTA.read_text(encoding="utf-8")
        self.assertNotIn("> Relatórios\n        </button>", src)
        self.assertNotIn("Relatório Geral", src)
        self.assertNotIn("Relatório de Caixa", src)
        self.assertNotIn("Relatório OBPC (26→25)", src)
        self.assertNotIn("Relatório para Sede", src)

    def test_sidebar_financeiro_e_fonte_unica_dos_relatorios_atuais(self):
        src = BASE.read_text(encoding="utf-8")
        for token in (
            "tipo_relatorio='gerencial'",
            "tipo_relatorio='livro_caixa'",
            "tipo_relatorio='sede'",
            "tipo_relatorio='auditoria'",
            "<span>Gerencial</span>",
            "<span>Livro Caixa</span>",
            "<span>Sede</span>",
            "<span>Auditoria</span>",
        ):
            self.assertIn(token, src)


if __name__ == "__main__":
    unittest.main()
