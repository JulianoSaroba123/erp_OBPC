from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date

# Force an isolated temporary database for this test module.
_tmp_db = tempfile.NamedTemporaryFile(prefix="d23d31_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"

from app import create_app
from app.extensoes import db
from app.configuracoes.configuracoes_model import Configuracao
from app.usuario.usuario_model import Usuario
from app.membros.membros_model import Membro
from app.obreiros.obreiros_model import Obreiro
from app.departamentos.departamentos_model import Departamento
from app.secretaria.participacao.participacao_model import ParticipacaoObreiro
from app.secretaria.atas.atas_model import Ata
from app.secretaria.oficios.oficios_model import Oficio


class TestD23D31SecretariaHardening(unittest.TestCase):
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

        self.app.config["LOGIN_DISABLED"] = False
        self.app.config["ALLOW_DEV_SEED_ROUTES"] = False

        db.session.rollback()
        db.session.query(ParticipacaoObreiro).delete()
        db.session.query(Obreiro).delete()
        db.session.query(Membro).delete()
        db.session.query(Departamento).delete()
        db.session.query(Ata).delete()
        db.session.query(Oficio).delete()
        db.session.query(Usuario).delete()
        db.session.query(Configuracao).delete()
        db.session.commit()

        self.user = Usuario(
            nome="Admin Teste",
            email="admin_d23d31@example.com",
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

    def _seed_membro(self):
        membro = Membro(nome="Membro Teste", status="Ativo", tipo="Membro")
        db.session.add(membro)
        db.session.commit()
        return membro.id

    def _seed_obreiro(self):
        obreiro = Obreiro(nome="Obreiro Teste", status="Ativo")
        db.session.add(obreiro)
        db.session.commit()
        return obreiro.id

    def _seed_departamento(self):
        departamento = Departamento(nome="Departamento Teste", status="Ativo")
        db.session.add(departamento)
        db.session.commit()
        return departamento.id

    def _seed_participacao(self):
        obreiro = Obreiro(nome="Obreiro Participacao", status="Ativo")
        db.session.add(obreiro)
        db.session.flush()

        participacao = ParticipacaoObreiro(
            obreiro_id=obreiro.id,
            data_reuniao=date.today(),
            tipo_reuniao="Sede",
            presenca="Presente",
        )
        db.session.add(participacao)
        db.session.commit()

        return participacao.id

    def _seed_pdf_entities(self):
        Configuracao.obter_configuracao()

        ata = Ata(
            titulo="Ata Teste",
            data=date.today(),
            local="Sala A",
            responsavel="Secretaria",
            descricao="Conteudo de teste",
        )
        oficio = Oficio(
            numero="OF-2099-001",
            data=date.today(),
            destinatario="Destinatario Teste",
            assunto="Assunto Teste",
            descricao="Descricao teste",
            status="Emitido",
        )

        db.session.add_all([ata, oficio])
        db.session.commit()
        return ata.id, oficio.id

    def test_seed_and_test_routes_blocked_outside_development(self):
        resp_inv = self.client.get("/inventario-teste")
        resp_seed_a = self.client.get("/midia/certificados/criar-exemplos")
        resp_seed_b = self.client.get("/midia/certificados/criar_exemplos")

        self.assertEqual(resp_inv.status_code, 404)
        self.assertEqual(resp_seed_a.status_code, 404)
        self.assertEqual(resp_seed_b.status_code, 404)

    def test_seed_and_test_routes_allowed_when_flag_enabled(self):
        self.app.config["ALLOW_DEV_SEED_ROUTES"] = True

        resp_inv = self.client.get("/inventario-teste")
        resp_seed = self.client.get("/midia/certificados/criar-exemplos", follow_redirects=False)

        self.assertNotEqual(resp_inv.status_code, 404)
        self.assertNotEqual(resp_seed.status_code, 404)

    def test_get_delete_routes_are_rejected(self):
        membro_id = self._seed_membro()
        obreiro_id = self._seed_obreiro()
        departamento_id = self._seed_departamento()
        participacao_id = self._seed_participacao()

        self.assertEqual(self.client.get(f"/membros/excluir/{membro_id}").status_code, 405)
        self.assertEqual(self.client.get(f"/obreiros/excluir/{obreiro_id}").status_code, 405)
        self.assertEqual(self.client.get(f"/departamentos/excluir/{departamento_id}").status_code, 405)
        self.assertEqual(self.client.get(f"/secretaria/participacao/excluir/{participacao_id}").status_code, 405)

    def test_post_delete_routes_are_authorized_and_work(self):
        membro_id = self._seed_membro()
        obreiro_id = self._seed_obreiro()
        departamento_id = self._seed_departamento()
        participacao_id = self._seed_participacao()

        r1 = self.client.post(f"/membros/excluir/{membro_id}", follow_redirects=False)
        r2 = self.client.post(f"/obreiros/excluir/{obreiro_id}", follow_redirects=False)
        r3 = self.client.post(f"/departamentos/excluir/{departamento_id}", follow_redirects=False)
        r4 = self.client.post(f"/secretaria/participacao/excluir/{participacao_id}", follow_redirects=False)

        self.assertIn(r1.status_code, (302, 303))
        self.assertIn(r2.status_code, (302, 303))
        self.assertIn(r3.status_code, (302, 303))
        self.assertIn(r4.status_code, (302, 303))

        self.assertIsNone(Membro.query.get(membro_id))
        self.assertIsNone(Obreiro.query.get(obreiro_id))
        self.assertIsNone(Departamento.query.get(departamento_id))
        self.assertIsNone(ParticipacaoObreiro.query.get(participacao_id))

    def test_permissions_still_protected_with_login_required(self):
        with self.client.session_transaction() as sess:
            sess.clear()

        client = self.app.test_client()

        resp = client.get("/secretaria/atas", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))

    def test_main_secretaria_pages_still_render(self):
        urls = [
            "/membros",
            "/obreiros",
            "/departamentos",
            "/secretaria/atas",
            "/secretaria/inventario/lista",
            "/secretaria/oficios/",
            "/secretaria/participacao/",
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_pdf_routes_still_available(self):
        ata_id, oficio_id = self._seed_pdf_entities()

        resp_ata = self.client.get(f"/secretaria/atas/pdf/{ata_id}")
        resp_oficio = self.client.get(f"/secretaria/oficios/pdf/{oficio_id}")

        self.assertEqual(resp_ata.status_code, 200)
        self.assertEqual(resp_oficio.status_code, 200)


if __name__ == "__main__":
    unittest.main()
