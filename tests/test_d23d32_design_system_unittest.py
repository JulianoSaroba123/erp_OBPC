from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

_tmp_db = tempfile.NamedTemporaryFile(prefix="d23d32_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"

from app import create_app
from app.extensoes import db
from app.configuracoes.configuracoes_model import Configuracao
from app.usuario.usuario_model import Usuario
from app.membros.membros_model import Membro
from app.departamentos.departamentos_model import Departamento
from app.obreiros.obreiros_model import Obreiro
from app.financeiro.obrigacoes_model import (
    ObrigacaoFinanceira,
    PagamentoObrigacao,
    PagamentoObrigacaoItem,
    ObrigacaoEvento,
)


class TestD23D32DesignSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["WTF_CSRF_ENABLED"] = False

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(_tmp_db.name)
        except OSError:
            pass

    def setUp(self):
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.session.rollback()
        self.app.config["LOGIN_DISABLED"] = False
        db.session.query(Membro).delete()
        db.session.query(Departamento).delete()
        db.session.query(Obreiro).delete()
        db.session.query(Usuario).delete()
        db.session.query(Configuracao).delete()
        db.session.commit()

        db.metadata.create_all(
            bind=db.engine,
            tables=[
                ObrigacaoFinanceira.__table__,
                PagamentoObrigacao.__table__,
                PagamentoObrigacaoItem.__table__,
                ObrigacaoEvento.__table__,
            ],
        )

        Configuracao.obter_configuracao()

        self.user = Usuario(
            nome="Admin Design System",
            email="design_system@example.com",
            nivel_acesso="master",
            ativo=True,
        )
        self.user.set_senha("123456")
        db.session.add(self.user)
        db.session.commit()

        self.client = self.app.test_client()
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(self.user.id)
            sess["_fresh"] = True

    def tearDown(self):
        db.session.rollback()
        db.session.remove()
        self.ctx.pop()

    def test_css_global_exists(self):
        css = Path(self.app.root_path) / "static" / "css" / "obpc-design-system.css"
        self.assertTrue(css.exists())

    def test_base_loads_css_before_extra_css(self):
        base = Path(self.app.root_path) / "templates" / "base.html"
        text = base.read_text(encoding="utf-8")
        link_index = text.index("css/obpc-design-system.css")
        extra_index = text.index("{% block extra_css %}{% endblock %}")
        self.assertLess(link_index, extra_index)

    def test_extra_blocks_preserved(self):
        base = Path(self.app.root_path) / "templates" / "base.html"
        text = base.read_text(encoding="utf-8")
        self.assertIn("{% block extra_css %}{% endblock %}", text)
        self.assertIn("{% block extra_js %}{% endblock %}", text)

    def test_namespace_and_tokens_present(self):
        css = Path(self.app.root_path) / "static" / "css" / "obpc-design-system.css"
        text = css.read_text(encoding="utf-8")
        for token in ["--obpc-primary", "--obpc-success", "--obpc-bg-card", "--obpc-shadow-md", "--obpc-radius-lg"]:
            self.assertIn(token, text)
        for component in [".obpc-page", ".obpc-card", ".obpc-kpi", ".obpc-btn", ".obpc-table", ".obpc-badge"]:
            self.assertIn(component, text)

    def test_showcase_template_renders(self):
        template = Path(self.app.root_path) / "templates" / "design_system_showcase.html"
        self.assertTrue(template.exists())
        text = template.read_text(encoding="utf-8")
        self.assertIn("Design System OBPC", text)
        self.assertIn("obpc-kpi", text)

    def test_dashboard_and_representative_pages_render(self):
        urls = [
            "/financeiro/dashboard",
            "/membros",
            "/departamentos",
            "/obreiros",
            "/secretaria/atas",
            "/secretaria/inventario/lista",
            "/secretaria/oficios/",
            "/secretaria/participacao/",
            "/financeiro/lista-moderna",
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url, follow_redirects=True)
                self.assertEqual(response.status_code, 200)

    def test_dashboard_preserves_kpis_and_chart_canvas(self):
        response = self.client.get("/financeiro/dashboard", follow_redirects=True)
        html = response.get_data(as_text=True)
        self.assertIn("chartFluxo6Meses", html)
        self.assertIn("chartDespesasCategoria", html)
        css = Path(self.app.root_path, "static", "css", "obpc-design-system.css").read_text(encoding="utf-8")
        self.assertIn(".obpc-kpi", css)

    def test_sidebar_present_on_representative_page(self):
        response = self.client.get("/membros")
        html = response.get_data(as_text=True)
        self.assertIn('class="sidebar"', html)

    def test_key_routes_still_registered(self):
        rules = list(self.app.url_map.iter_rules())
        endpoint_methods = {r.endpoint: set(r.methods) for r in rules}

        self.assertIn("financeiro.dashboard_moderno", endpoint_methods)
        self.assertIn("membros.lista_membros", endpoint_methods)
        self.assertIn("inventario.lista_itens", endpoint_methods)
        self.assertIn("midia.listar_certificados", endpoint_methods)

    def test_chartjs_not_global(self):
        base = Path(self.app.root_path) / "templates" / "base.html"
        text = base.read_text(encoding="utf-8")
        self.assertNotIn("chart.umd.min.js", text)


if __name__ == "__main__":
    unittest.main()