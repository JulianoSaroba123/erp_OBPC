"""A7H.31: HTTP real, login real e dados fictícios no SQLite temporário."""
from datetime import date, time
import io
import re
import secrets

import pytest


SENHA = "Teste-A7h31-123!"
PERFIS = ("master", "administrador", "secretario", "midia", "membro", "tesoureiro", "lider_departamento")
TOKEN = re.compile(rb'name="csrf_token"\s+value="([^"]+)"')


def token(pagina):
    assert pagina.status_code == 200, pagina.status_code
    m = TOKEN.search(pagina.data)
    assert m, "Formulário sem token CSRF renderizado"
    return m.group(1).decode()


@pytest.fixture(scope="module")
def cenario(tmp_path_factory):
    from app import create_app
    from app.agenda_pastoral.agenda_pastoral_model import AgendaPastoral
    from app.config import Config
    from app.escala_ministerial.escala_model import EscalaMinisterial
    from app.extensoes import db
    from app.midia.midia_model import AgendaSemanal, CarteiraMembro, Certificado
    from app.notificacoes import tarefas_agendadas
    from app.usuario.usuario_model import Usuario

    with pytest.MonkeyPatch.context() as m:
        base = tmp_path_factory.mktemp("obpc-a7h31")
        m.setattr(Config, "SECRET_KEY", secrets.token_urlsafe(32))
        m.setattr(Config, "SQLALCHEMY_DATABASE_URI", f"sqlite:///{base / 'teste.sqlite'}")
        m.setattr(Config, "SQLALCHEMY_ENGINE_OPTIONS", {})
        m.setattr(Config, "SESSION_COOKIE_SECURE", False)
        m.setattr(Config, "PREFERRED_URL_SCHEME", "http")
        m.setattr(tarefas_agendadas, "iniciar_scheduler", lambda _app: None)
        app = create_app()
        app.config.update(TESTING=True, ALLOW_DEV_SEED_ROUTES=False)
        app.static_folder = str(base / "static")
        pasta_fotos = base / "static/uploads/fotos_membros"
        pasta_fotos.mkdir(parents=True)
        (pasta_fotos / "ficticia.png").write_bytes(b"foto ficticia")
        (base / "static/normal.css").write_bytes(b"body {}")
        with app.app_context():
            usuarios = {}
            for perfil in PERFIS:
                u = Usuario(nome=f"Teste {perfil}", email=f"{perfil}@example.test",
                            nivel_acesso=perfil, ativo=True)
                u.set_senha(SENHA)
                db.session.add(u)
                usuarios[perfil] = u
            db.session.flush()
            evento = AgendaSemanal(titulo="Culto teste", data_evento=date.today(),
                                  tipo_evento="Culto", hora_inicio=time(19, 0))
            atividade = AgendaPastoral(usuario_id=usuarios["membro"].id,
                                       titulo="Compromisso reservado", data=date.today())
            certificado = Certificado(nome_pessoa="Registro fictício", tipo_certificado="Batismo",
                                      data_evento=date.today(), pastor_responsavel="Teste")
            carteira = CarteiraMembro(numero_carteira="T-001", nome_completo="Pessoa fictícia",
                                      data_nascimento=date(2000, 1, 1),
                                      foto_caminho="uploads/fotos_membros/ficticia.png")
            db.session.add_all([evento, atividade, certificado, carteira])
            db.session.flush()
            escala = EscalaMinisterial(evento_id=evento.id, data_evento=date.today(),
                                       pregador="Pessoa Teste")
            db.session.add(escala)
            db.session.commit()
            ids = dict(evento=evento.id, atividade=atividade.id, certificado=certificado.id,
                       carteira=carteira.id, escala=escala.id, membro=usuarios["membro"].id)
        yield app, ids, pasta_fotos


def entrar(app, perfil):
    cliente = app.test_client()
    resposta = cliente.post("/login", data=dict(
        email=f"{perfil}@example.test", senha=SENHA,
        csrf_token=token(cliente.get("/login")),
    ))
    assert resposta.status_code == 302
    return cliente


@pytest.mark.parametrize("perfil", PERFIS)
def test_permissoes_por_funcao_em_rotas_e_apis(cenario, perfil):
    app, ids, _ = cenario
    cliente = entrar(app, perfil)
    secretaria = perfil in {"master", "administrador", "secretario"}
    midia = perfil in {"master", "administrador", "midia"}
    for rota, permitido in (
        ("/midia/agenda/", midia),
        ("/midia/agenda/novo", midia),
        ("/midia/agenda/pdf", midia),
        (f"/midia/agenda/visualizar/{ids['evento']}", midia),
        ("/midia/api/membros", midia),
        ("/escala-ministerial/", midia),
        ("/escala-ministerial/pdf", midia),
        (f"/api/escala-ministerial/evento/{ids['evento']}", midia),
        ("/api/escala-ministerial/autocomplete/pregador", midia),
        ("/midia/carteiras/", secretaria),
        (f"/midia/carteiras/pdf/{ids['carteira']}", secretaria),
        (f"/midia/carteiras/foto/{ids['carteira']}", secretaria),
        ("/midia/certificados/", secretaria or midia),
        (f"/midia/certificados/pdf/{ids['certificado']}", secretaria or midia),
        ("/agenda-pastoral", True),
        ("/agenda-pastoral/hoje", True),
    ):
        assert cliente.get(rota).status_code == (200 if permitido else 403), (perfil, rota)

    if midia:
        api = cliente.get(f"/api/escala-ministerial/evento/{ids['evento']}").get_json()
        assert api["sucesso"] and api["evento"]["horario"] == "19:00"
        assert cliente.get("/api/escala-ministerial/evento/0").status_code == 404

    if not midia:
        csrf = token(cliente.get("/agenda-pastoral/nova"))
        for rota in ("/midia/agenda/salvar", "/escala-ministerial/salvar"):
            assert cliente.post(rota, data={"csrf_token": csrf}).status_code == 403


def test_anonimo_e_arquivo_estatico(cenario):
    app, ids, pasta_fotos = cenario
    anonimo = app.test_client()
    secretaria = entrar(app, "secretario")
    assert anonimo.get("/midia/agenda/").status_code == 302
    assert anonimo.get("/agenda-pastoral").status_code == 302
    assert anonimo.get(f"/midia/carteiras/foto/{ids['carteira']}").status_code == 302
    for cliente in (anonimo, secretaria):
        assert cliente.get("/static/uploads/fotos_membros/ficticia.png").status_code == 404
        assert cliente.get("/static/normal.css").status_code == 200
    foto = secretaria.get(f"/midia/carteiras/foto/{ids['carteira']}")
    assert foto.data == (pasta_fotos / "ficticia.png").read_bytes()
    assert foto.headers["Cache-Control"] == "private, no-store"
    assert foto.headers["X-Content-Type-Options"] == "nosniff"


def test_agenda_pessoal_csrf_e_isolamento_inclusive_master(cenario):
    from app.agenda_pastoral.agenda_pastoral_model import AgendaPastoral
    from app.extensoes import db

    app, ids, _ = cenario
    id_reservado = ids["atividade"]
    dono = entrar(app, "membro")
    master = entrar(app, "master")
    base = "/agenda-pastoral"
    assert "Compromisso reservado".encode() in dono.get(base).data
    assert "Compromisso reservado".encode() not in master.get(base).data
    assert master.get(f"{base}/{id_reservado}/editar").status_code == 404
    outro_token = token(master.get(f"{base}/nova"))
    for acao in ("editar", "concluir", "excluir"):
        assert master.post(f"{base}/{id_reservado}/{acao}",
                           headers={"X-CSRFToken": outro_token}).status_code == 404

    payload = dict(titulo="Atividade nova", data=date.today().isoformat(), usuario_id=999999)
    assert dono.post(f"{base}/nova", data=payload).status_code == 400
    csrf = token(dono.get(f"{base}/nova"))
    assert dono.post(f"{base}/nova", data=dict(payload, csrf_token=csrf)).status_code == 302
    with app.app_context():
        atividade = AgendaPastoral.query.filter_by(titulo=payload["titulo"]).one()
        assert atividade.usuario_id == ids["membro"]
        novo_id = atividade.id
    for pagina in (base, f"{base}/hoje"):
        html = dono.get(pagina).data
        assert f"{base}/{novo_id}/concluir".encode() in html
        assert b"X-CSRFToken" in html
    assert dono.post(f"{base}/{novo_id}/editar", data=payload).status_code == 400
    payload["titulo"] = "Atividade editada"
    editar_token = token(dono.get(f"{base}/{novo_id}/editar"))
    assert dono.post(f"{base}/{novo_id}/editar",
                     data=dict(payload, csrf_token=editar_token)).status_code == 302
    for acao in ("concluir", "excluir"):
        assert dono.post(f"{base}/{novo_id}/{acao}").status_code == 400
        sucesso = dono.post(f"{base}/{novo_id}/{acao}", headers={"X-CSRFToken": editar_token})
        assert sucesso.status_code == 200 and sucesso.get_json()["success"]
    with app.app_context():
        assert db.session.get(AgendaPastoral, novo_id) is None
        assert not db.session.get(AgendaPastoral, id_reservado).concluida


def test_midia_carteira_certificado_agenda_e_escala_com_token(cenario):
    from app.extensoes import db
    from app.escala_ministerial.escala_model import EscalaMinisterial
    from app.midia.midia_model import AgendaSemanal, CarteiraMembro, Certificado

    app, ids, _ = cenario
    midia = entrar(app, "midia")
    secretaria = entrar(app, "secretario")
    folha = midia.get("/escala-ministerial/")
    assert f"/escala-ministerial/excluir/{ids['escala']}".encode() in folha.data
    editar = midia.get(f"/escala-ministerial/editar/{ids['escala']}")
    assert f'name="id" value="{ids["escala"]}"'.encode() in editar.data
    assert f"/api/escala-ministerial/evento/{ids['evento']}".encode() in editar.data
    csrf = token(editar)
    payload = dict(id=ids["escala"], data_evento=date.today().isoformat(),
                   evento_id=ids["evento"], pregador="Pregador alterado")
    assert midia.post("/escala-ministerial/salvar", data=payload).status_code == 400
    assert midia.post("/escala-ministerial/salvar", data=dict(payload, csrf_token=csrf)).status_code == 302
    with app.app_context():
        assert db.session.get(EscalaMinisterial, ids["escala"]).pregador == "Pregador alterado"
    exclusao_escala = f"/escala-ministerial/excluir/{ids['escala']}"
    assert midia.post(exclusao_escala).status_code == 400
    assert midia.post(exclusao_escala, data={"csrf_token": csrf}).status_code == 302
    with app.app_context():
        assert not db.session.get(EscalaMinisterial, ids["escala"]).ativo

    dados_agenda = dict(titulo="Evento fictício novo", data_evento=date.today().isoformat(),
                        tipo_evento="Culto")
    assert midia.post("/midia/agenda/salvar", data=dados_agenda).status_code == 400
    assert midia.post("/midia/agenda/salvar", data=dict(dados_agenda, csrf_token=csrf)).status_code == 302
    with app.app_context():
        evento_id = AgendaSemanal.query.filter_by(titulo=dados_agenda["titulo"]).one().id
    assert midia.post(f"/midia/agenda/excluir/{evento_id}").status_code == 400
    assert midia.post(f"/midia/agenda/excluir/{evento_id}", data={"csrf_token": csrf}).status_code == 302

    csrf_secretaria = token(secretaria.get("/midia/carteiras/nova"))
    dados_carteira = dict(numero_carteira="T-002", nome_completo="Carteira nova",
                         data_nascimento="2000-01-02")
    assert secretaria.post("/midia/carteiras/salvar", data=dados_carteira).status_code == 400
    rejeitado = secretaria.post("/midia/carteiras/salvar", data=dict(
        dados_carteira, csrf_token=csrf_secretaria,
        foto=(io.BytesIO(b"arquivo que nao e imagem"), "invalida.png"),
    ))
    assert rejeitado.headers["Location"] == "/midia/carteiras/nova"
    with app.app_context():
        assert CarteiraMembro.query.filter_by(numero_carteira="T-002").count() == 0

    from PIL import Image
    foto = io.BytesIO()
    Image.new("RGB", (3, 3), "white").save(foto, format="PNG")
    foto.seek(0)
    assert secretaria.post("/midia/carteiras/salvar", data=dict(
        dados_carteira, csrf_token=csrf_secretaria, foto=(foto, "foto.png"),
    )).status_code == 302
    with app.app_context():
        carteira = CarteiraMembro.query.filter_by(numero_carteira="T-002").one()
        carteira_id = carteira.id
        assert carteira.foto_caminho
    assert secretaria.get(f"/midia/carteiras/foto/{carteira_id}").mimetype == "image/png"
    assert midia.get(f"/midia/carteiras/foto/{carteira_id}").status_code == 403

    dados_certificado = dict(nome_pessoa="Certificado novo", tipo_certificado="Batismo",
                             data_evento=date.today().isoformat(), pastor_responsavel="Teste")
    assert midia.post("/midia/certificados/salvar", data=dados_certificado).status_code == 400
    assert midia.post("/midia/certificados/salvar",
                      data=dict(dados_certificado, csrf_token=csrf)).status_code == 302
    with app.app_context():
        certificado_id = Certificado.query.filter_by(nome_pessoa="Certificado novo").one().id
    for grupo, item_id in (("carteiras", carteira_id), ("certificados", certificado_id)):
        rota = f"/midia/{grupo}/excluir/{item_id}"
        pagina = secretaria.get(f"/midia/{grupo}/")
        assert f'action="{rota}"'.encode() in pagina.data
        assert secretaria.get(rota).status_code == 405
        assert secretaria.post(rota).status_code == 400
        assert secretaria.post(rota, data={"csrf_token": token(pagina)}).status_code == 302
    with app.app_context():
        assert not db.session.get(CarteiraMembro, carteira_id).ativo
        assert db.session.get(Certificado, certificado_id) is None


@pytest.mark.parametrize("sufixo", ("criar-exemplos", "criar_exemplos"))
def test_seeds_somente_post_admin_com_token_e_flag(cenario, monkeypatch, sufixo):
    from app.midia.midia_model import Certificado

    app, _, _ = cenario
    master = entrar(app, "master")
    midia = entrar(app, "midia")
    rota = "/midia/certificados/" + sufixo
    csrf = token(master.get("/midia/certificados/novo"))
    with app.app_context():
        inicial = Certificado.query.count()
    assert master.get(rota).status_code == 405
    assert master.post(rota, data={"csrf_token": csrf}).status_code == 404
    monkeypatch.setitem(app.config, "ALLOW_DEV_SEED_ROUTES", True)
    csrf_midia = token(midia.get("/midia/certificados/novo"))
    assert midia.post(rota, data={"csrf_token": csrf_midia}).status_code == 403
    assert master.post(rota).status_code == 400
    with app.app_context():
        assert Certificado.query.count() == inicial
    assert master.post(rota, data={"csrf_token": csrf}).status_code == 302
