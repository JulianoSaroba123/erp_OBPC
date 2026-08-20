from __future__ import annotations

import os
import re
import tempfile
import unittest

_tmp_db = tempfile.NamedTemporaryFile(prefix="d23d46_", suffix=".db", delete=False)
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

# Âncoras dos comentários da sidebar em app/templates/base.html.
MARCA_SECRETARIA = "<!-- Submenu Secretaria"
MARCA_DEPARTAMENTOS = "<!-- Departamentos"
MARCA_MIDIA = "<!-- Menu Mídia"
MARCA_EVENTOS = "<!-- Eventos"
MARCA_AGENDA_PASTORAL = "<!-- Agenda Pastoral"
MARCA_CONFIGURACOES = "<!-- Configurações"

GRUPOS_SECRETARIA = ["Pessoas", "Documentos", "Credenciais", "Patrimônio", "Relatórios"]


class TestD23D46SecretariaNavegacao(unittest.TestCase):
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

        Usuario.query.filter_by(email="d23d46@example.com").delete()
        db.session.commit()

        self.user = Usuario(
            nome="Admin D23D46",
            email="d23d46@example.com",
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

    # ------------------------------------------------------------------ utils

    def _get_html(self, url: str) -> str:
        resp = self.client.get(url, follow_redirects=True)
        self.assertEqual(resp.status_code, 200, f"{url} retornou {resp.status_code}")
        return resp.get_data(as_text=True)

    def _bloco(self, html: str, inicio: str, fim: str) -> str:
        i = html.find(inicio)
        self.assertNotEqual(i, -1, f"âncora inicial ausente: {inicio}")
        f = html.find(fim, i)
        self.assertNotEqual(f, -1, f"âncora final ausente: {fim}")
        return html[i:f]

    def _bloco_secretaria(self, html: str) -> str:
        return self._bloco(html, MARCA_SECRETARIA, MARCA_DEPARTAMENTOS)

    def _bloco_midia(self, html: str) -> str:
        return self._bloco(html, MARCA_MIDIA, MARCA_EVENTOS)

    def _submenu_do_grupo(self, bloco: str, rotulo: str) -> str:
        """Retorna o HTML entre o botão do grupo e o início do próximo grupo."""
        marcador = f"<span>{rotulo}</span>"
        i = bloco.find(marcador)
        self.assertNotEqual(i, -1, f"grupo '{rotulo}' ausente na Secretaria")
        proximos = [
            bloco.find(f"<span>{outro}</span>", i + len(marcador))
            for outro in GRUPOS_SECRETARIA
            if outro != rotulo
        ]
        posicoes = [p for p in proximos if p != -1]
        return bloco[i:min(posicoes)] if posicoes else bloco[i:]

    def _classe_do_botao(self, html: str, rotulo: str) -> str:
        for botao in re.findall(r"<button\b[^>]*>.*?</button>", html, re.S):
            if f"<span>{rotulo}</span>" in botao:
                m = re.search(r'class="([^"]*)"', botao)
                return m.group(1) if m else ""
        self.fail(f"botão do grupo '{rotulo}' não encontrado")

    def _grupo_esta_ativo(self, html: str, rotulo: str) -> bool:
        classe = self._classe_do_botao(self._bloco_secretaria(html), rotulo)
        return "active" in classe.split()

    def _grupo_unico_ativo(self, url: str, rotulo_esperado: str) -> None:
        html = self._get_html(url)
        for rotulo in GRUPOS_SECRETARIA:
            with self.subTest(url=url, grupo=rotulo):
                if rotulo == rotulo_esperado:
                    self.assertTrue(
                        self._grupo_esta_ativo(html, rotulo),
                        f"{url} deveria ativar o grupo {rotulo}",
                    )
                else:
                    self.assertFalse(
                        self._grupo_esta_ativo(html, rotulo),
                        f"{url} não deveria ativar o grupo {rotulo}",
                    )

    # ------------------------------------------------------------ estrutura

    def test_menu_secretaria_possui_visao_geral_e_cinco_grupos(self):
        bloco = self._bloco_secretaria(self._get_html("/secretaria/visao-geral"))
        self.assertIn("<span>Secretaria</span>", bloco)
        self.assertIn("<span>Visão Geral</span>", bloco)
        for rotulo in GRUPOS_SECRETARIA:
            with self.subTest(grupo=rotulo):
                self.assertIn(f"<span>{rotulo}</span>", bloco)

    def test_ordem_dos_grupos_da_secretaria(self):
        bloco = self._bloco_secretaria(self._get_html("/secretaria/visao-geral"))
        posicoes = [bloco.find(f"<span>{r}</span>") for r in GRUPOS_SECRETARIA]
        self.assertEqual(posicoes, sorted(posicoes), "grupos fora da ordem especificada")
        self.assertLess(bloco.find("<span>Visão Geral</span>"), posicoes[0])

    def test_itens_dentro_de_cada_grupo(self):
        bloco = self._bloco_secretaria(self._get_html("/secretaria/visao-geral"))
        esperado = {
            "Pessoas": ["Membros", "Lideranças", "Obreiros"],
            "Documentos": ["Atas", "Ofícios"],
            "Credenciais": ["Carteiras", "Certificados"],
            "Patrimônio": ["Inventário"],
            "Relatórios": ["Participação de Obreiros"],
        }
        for grupo, itens in esperado.items():
            submenu = self._submenu_do_grupo(bloco, grupo)
            for item in itens:
                with self.subTest(grupo=grupo, item=item):
                    self.assertIn(f"<span>{item}</span>", submenu)

    # ------------------------------------------------- exclusividade no menu

    def test_carteiras_aparecem_somente_na_secretaria(self):
        html = self._get_html("/secretaria/visao-geral")
        with self.app.test_request_context():
            from flask import url_for

            url_carteiras = url_for("midia.listar_carteiras")

        self.assertIn(url_carteiras, self._bloco_secretaria(html))

        bloco_midia = self._bloco_midia(html)
        self.assertNotIn(url_carteiras, bloco_midia)
        self.assertNotIn("<span>Carteiras</span>", bloco_midia)

    def test_certificados_aparecem_somente_na_secretaria(self):
        html = self._get_html("/secretaria/visao-geral")
        with self.app.test_request_context():
            from flask import url_for

            url_certificados = url_for("midia.listar_certificados")

        self.assertIn(url_certificados, self._bloco_secretaria(html))

        bloco_midia = self._bloco_midia(html)
        self.assertNotIn(url_certificados, bloco_midia)
        self.assertNotIn("<span>Certificados</span>", bloco_midia)

    def test_departamentos_fora_da_secretaria(self):
        html = self._get_html("/secretaria/visao-geral")
        self.assertNotIn("<span>Departamentos</span>", self._bloco_secretaria(html))
        bloco_departamentos = self._bloco(html, MARCA_DEPARTAMENTOS, MARCA_MIDIA)
        self.assertIn("<span>Departamentos</span>", bloco_departamentos)

    def test_agenda_fora_da_secretaria(self):
        html = self._get_html("/secretaria/visao-geral")
        bloco_secretaria = self._bloco_secretaria(html)
        self.assertNotIn("<span>Agenda Semanal</span>", bloco_secretaria)
        self.assertNotIn("<span>Minha Agenda</span>", bloco_secretaria)

        self.assertIn("<span>Agenda Semanal</span>", self._bloco_midia(html))
        bloco_agenda = self._bloco(html, MARCA_AGENDA_PASTORAL, MARCA_CONFIGURACOES)
        self.assertIn("<span>Minha Agenda</span>", bloco_agenda)

    # ---------------------------------------------------------- active state

    def test_active_state_visao_geral(self):
        html = self._get_html("/secretaria/visao-geral")
        bloco = self._bloco_secretaria(html)
        link = next(
            a
            for a in re.findall(r"<a\b[^>]*>.*?</a>", bloco, re.S)
            if "<span>Visão Geral</span>" in a
        )
        self.assertIn("active", link)
        for rotulo in GRUPOS_SECRETARIA:
            with self.subTest(grupo=rotulo):
                self.assertFalse(self._grupo_esta_ativo(html, rotulo))

    def test_active_state_grupo_pessoas(self):
        for url in ["/membros", "/lideres", "/obreiros"]:
            self._grupo_unico_ativo(url, "Pessoas")

    def test_active_state_grupo_documentos(self):
        for url in ["/secretaria/atas", "/secretaria/oficios/"]:
            self._grupo_unico_ativo(url, "Documentos")

    def test_active_state_grupo_credenciais(self):
        for url in ["/midia/carteiras", "/midia/certificados"]:
            self._grupo_unico_ativo(url, "Credenciais")

    def test_active_state_grupo_patrimonio(self):
        self._grupo_unico_ativo("/secretaria/inventario/lista", "Patrimônio")

    def test_active_state_grupo_relatorios(self):
        self._grupo_unico_ativo("/secretaria/participacao/", "Relatórios")

    def test_secretaria_permanece_aberta_nas_paginas_do_modulo(self):
        for url in [
            "/secretaria/visao-geral",
            "/membros",
            "/secretaria/atas",
            "/midia/carteiras",
            "/secretaria/inventario/lista",
            "/secretaria/participacao/",
        ]:
            with self.subTest(url=url):
                bloco = self._bloco_secretaria(self._get_html(url))
                self.assertIn('aria-expanded="true"', bloco)
                self.assertIn('class="submenu show"', bloco)

    # -------------------------------------------------------- rotas mantidas

    def test_rotas_de_navegacao_preservadas(self):
        endpoints = {r.endpoint for r in self.app.url_map.iter_rules()}
        for endpoint in [
            "secretaria.visao_geral",
            "membros.lista_membros",
            "membros.lista_lideres",
            "obreiros.lista_obreiros",
            "atas.lista_atas",
            "oficios.lista_oficios",
            "midia.listar_carteiras",
            "midia.listar_certificados",
            "midia.listar_agenda",
            "inventario.lista_itens",
            "participacao.listar_participacoes",
            "departamentos.lista_departamentos",
            "agenda_pastoral.lista_agenda",
        ]:
            with self.subTest(endpoint=endpoint):
                self.assertIn(endpoint, endpoints)

    def test_endpoints_de_pdf_preservados(self):
        endpoints = {r.endpoint for r in self.app.url_map.iter_rules()}
        for endpoint in [
            "atas.gerar_pdf_ata",
            "oficios.gerar_pdf_oficio",
            "inventario.gerar_pdf_inventario",
            "participacao.gerar_pdf_participacao",
            "midia.certificado_pdf",
            "midia.carteira_pdf",
        ]:
            with self.subTest(endpoint=endpoint):
                self.assertIn(endpoint, endpoints)


if __name__ == "__main__":
    unittest.main()
