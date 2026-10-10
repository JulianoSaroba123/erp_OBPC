import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVRO = ROOT / "app" / "financeiro" / "templates" / "financeiro" / "relatorio_livro_caixa.html"


class D23D67AssinaturasLivroCaixaTest(unittest.TestCase):
    def test_assinaturas_ficam_lado_a_lado_com_largura_controlada(self):
        src = LIVRO.read_text(encoding="utf-8-sig")
        self.assertIn(".signature-grid", src)
        self.assertIn("display: flex", src)
        self.assertIn("justify-content: center", src)
        self.assertIn("flex: 0 0 72mm", src)
        self.assertIn("Pastor Responsável", src)
        self.assertIn("Tesoureiro", src)

    def test_bloco_de_assinaturas_fica_fora_do_fechamento(self):
        src = LIVRO.read_text(encoding="utf-8-sig")
        fechamento_fim = src.index('</div>\n\n        <div class="signature-grid">')
        self.assertGreater(fechamento_fim, 0)


if __name__ == "__main__":
    unittest.main()
