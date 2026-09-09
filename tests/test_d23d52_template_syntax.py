import unittest
from pathlib import Path

from jinja2 import Environment, TemplateSyntaxError

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "app" / "financeiro" / "templates" / "financeiro"

FILES = [
    "lista_lancamentos.html",
    "lista_lancamentos_moderno.html",
    "cadastro_lancamento.html",
    "importar_extrato.html",
    "import_preview.html",
    "lista_projetos.html",
    "cadastro_projeto.html",
    "caixa_destinacoes.html",
    "conciliacao.html",
    "conciliacao_moderno.html",
    "gerenciar_despesas_fixas.html",
    "lista_recibos.html",
    "emitir_recibo.html",
    "editar_recibo.html",
    "visualizar_recibo.html",
    "relatorio.html",
]


class D23D52TemplateSyntaxTest(unittest.TestCase):
    def test_templates_financeiros_parseiam(self):
        env = Environment()
        failures = []
        for filename in FILES:
            path = TEMPLATES / filename
            try:
                env.parse(path.read_text(encoding="utf-8-sig"))
            except TemplateSyntaxError as exc:
                failures.append(f"{filename}:{exc.lineno}: {exc.message}")
        self.assertEqual([], failures, "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
