from __future__ import annotations

import os
import tempfile
import unittest

_tmp_db = tempfile.NamedTemporaryFile(prefix="d23d33_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"

from app import create_app
from app.extensoes import db
from app.configuracoes.configuracoes_model import Configuracao
from app.usuario.usuario_model import Usuario
from app.financeiro.obrigacoes_model import (
    ObrigacaoFinanceira,
    PagamentoObrigacao,
    PagamentoObrigacaoItem,
    ObrigacaoEvento,
)


class TestD23D33SecretariaVisual(unittest.TestCase):
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

        Usuario.query.filter_by(email="d23d33@example.com").delete()
        db.session.commit()

        self.user = Usuario(
            nome="Admin D23D33",
            email="d23d33@example.com",
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

    def _get_html(self, url: str) -> str:
        resp = self.client.get(url, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        return resp.get_data(as_text=True)

    def test_visao_geral_render_design_system_kpis_quick_actions_attention(self):
        html = self._get_html("/secretaria/visao-geral")
        self.assertIn("obpc-design-system.css", html)
        self.assertIn("KPIs Principais", html)
        self.assertTrue("Ações Rápidas" in html or "Acoes Rapidas" in html)
        self.assertTrue("Atenção da Secretaria" in html or "Atencao da Secretaria" in html)
        self.assertIn("Atividade Recente", html)

    def test_menu_secretaria_structure_and_active_states(self):
        html_geral = self._get_html("/secretaria/visao-geral")
        self.assertIn("Visão Geral", html_geral)
        self.assertIn("Pessoas", html_geral)
        self.assertIn("Documentos", html_geral)
        self.assertIn("Credenciais", html_geral)
        self.assertIn("Patrimônio", html_geral)
        self.assertIn("Relatórios", html_geral)
        self.assertIn("visao-geral", html_geral)
        self.assertIn("submenu-item active", html_geral)

        html_membros = self._get_html("/membros")
        self.assertIn("Pessoas", html_membros)
        self.assertIn("submenu-item active", html_membros)

        html_atas = self._get_html("/secretaria/atas")
        self.assertIn("Documentos", html_atas)

        html_carteiras = self._get_html("/midia/carteiras")
        self.assertIn("Credenciais", html_carteiras)

        html_inventario = self._get_html("/secretaria/inventario/lista")
        self.assertIn("Patrimônio", html_inventario)

        html_participacao = self._get_html("/secretaria/participacao/")
        self.assertIn("Relatórios", html_participacao)

    def test_representative_pages_render_200(self):
        urls = [
            "/membros",
            "/lideres",
            "/obreiros",
            "/secretaria/atas",
            "/secretaria/oficios/",
            "/midia/carteiras",
            "/midia/certificados",
            "/secretaria/inventario/lista",
            "/secretaria/participacao/",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertIn("obpc-page", self._get_html(url))

    def test_post_delete_hardening_still_enforced(self):
        self.assertNotEqual(self.client.get("/membros/excluir/1").status_code, 200)
        self.assertNotEqual(self.client.get("/obreiros/excluir/1").status_code, 200)
        self.assertNotEqual(self.client.get("/secretaria/participacao/excluir/1").status_code, 200)

    def test_pdf_endpoints_registered_and_sidebar_integrity(self):
        endpoints = {r.endpoint for r in self.app.url_map.iter_rules()}
        self.assertIn("atas.gerar_pdf_ata", endpoints)
        self.assertIn("oficios.gerar_pdf_oficio", endpoints)
        self.assertIn("inventario.gerar_pdf_inventario", endpoints)
        self.assertIn("participacao.gerar_pdf_participacao", endpoints)
        self.assertIn("midia.certificado_pdf", endpoints)
        self.assertIn("midia.carteira_pdf", endpoints)

        html = self._get_html("/secretaria/visao-geral")
        self.assertIn('class="sidebar"', html)

    def test_financeiro_behavior_not_affected(self):
        html = self._get_html("/financeiro/dashboard")
        self.assertIn("chartFluxo6Meses", html)
        self.assertIn("chartDespesasCategoria", html)

    def test_visual_class_presence_on_representative_pages(self):
        html_dashboard = self._get_html("/secretaria/visao-geral")
        for css_class in [
            "obpc-page",
            "obpc-page-header",
            "obpc-card",
            "obpc-kpi",
            "obpc-btn",
        ]:
            with self.subTest(css_class=css_class):
                self.assertIn(css_class, html_dashboard)

        html_membros = self._get_html("/membros")
        self.assertTrue("obpc-table" in html_membros or "obpc-empty" in html_membros)


if __name__ == "__main__":
    unittest.main()
