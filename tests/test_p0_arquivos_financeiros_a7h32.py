"""Regressão da entrega privada e dos fluxos financeiros reais, com SQLite fictício."""
import io
import secrets
from datetime import date

import pytest

from test_p0_acl_midia_agendas_a7h31 import SENHA, entrar, token


@pytest.fixture
def dados(tmp_path, monkeypatch):
    from app import create_app
    from app.config import Config
    from app.extensoes import db
    from app.financeiro.financeiro_model import Lancamento
    from app.notificacoes import tarefas_agendadas
    from app.usuario.usuario_model import Usuario

    monkeypatch.setattr(Config, "SECRET_KEY", secrets.token_urlsafe(32))
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", f"sqlite:///{tmp_path / 'teste.sqlite'}")
    monkeypatch.setattr(Config, "SQLALCHEMY_ENGINE_OPTIONS", {})
    monkeypatch.setattr(Config, "SESSION_COOKIE_SECURE", False)
    monkeypatch.setattr(Config, "PREFERRED_URL_SCHEME", "http", raising=False)
    monkeypatch.setattr(Config, "FINANCEIRO_ARQUIVOS_DIR", str(tmp_path / "privado"))
    monkeypatch.setattr(tarefas_agendadas, "iniciar_scheduler", lambda _app: None)
    app = create_app()
    app.config["TESTING"] = True
    app.static_folder = str(tmp_path / "static")
    comprovantes = tmp_path / "static/uploads/comprovantes"
    extratos = tmp_path / "static/uploads/extratos"
    comprovantes.mkdir(parents=True)
    extratos.mkdir(parents=True)
    (comprovantes / "ficticio.pdf").write_bytes(b"%PDF-1.4\nlegado ficticio")
    (extratos / "antigo.csv").write_bytes(b"extrato ficticio")
    (tmp_path / "static/normal.css").write_bytes(b"body {}")
    with app.app_context():
        for perfil in ("tesoureiro", "secretario"):
            usuario = Usuario(nome=perfil, email=f"{perfil}@example.test", nivel_acesso=perfil, ativo=True)
            usuario.set_senha(SENHA)
            db.session.add(usuario)
        lancamento = Lancamento(
            data=date(2026, 7, 12), tipo="Entrada", categoria="OFERTAS",
            descricao="Lançamento fictício", valor=31.0, conta="Banco",
            comprovante="/static/uploads/comprovantes/ficticio.pdf",
        )
        db.session.add(lancamento)
        db.session.commit()
        identificador = lancamento.id
    return app, tmp_path, identificador


def test_links_legados_e_novos_exigem_permissao_financeira(dados):
    app, pasta, _ = dados
    anonimo = app.test_client()
    tesoureiro = entrar(app, "tesoureiro")
    secretaria = entrar(app, "secretario")
    (pasta / "static/alias").symlink_to(pasta / "static/uploads/comprovantes", target_is_directory=True)
    for rota in (
        "/static/uploads/comprovantes/ficticio.pdf",
        "/financeiro/arquivos/comprovantes/ficticio.pdf",
    ):
        assert anonimo.get(rota).status_code == 302
        assert secretaria.get(rota).status_code == 403
        resposta = tesoureiro.get(rota)
        assert resposta.status_code == 200 and resposta.data.startswith(b"%PDF")
        assert resposta.headers["Cache-Control"] == "private, no-store"
        assert resposta.headers["X-Content-Type-Options"] == "nosniff"
        assert tesoureiro.head(rota).status_code == 200
    for cliente in (anonimo, tesoureiro, secretaria):
        assert cliente.get("/static/uploads/extratos/antigo.csv").status_code == 404
        assert cliente.get("/static/alias/ficticio.pdf").status_code == 404
        assert cliente.get("/static/normal.css").status_code == 200
    assert tesoureiro.get("/financeiro/arquivos/comprovantes/inexistente.pdf").status_code == 404
    assert tesoureiro.get("/financeiro/arquivos/comprovantes/subpasta/ficticio.pdf").status_code == 404


def test_comprovante_novo_fora_de_static_e_desvinculacao(dados):
    from app.extensoes import db
    from app.financeiro.comprovante_model import Comprovante

    app, pasta, identificador = dados
    tesoureiro = entrar(app, "tesoureiro")
    editor = f"/financeiro/editar/{identificador}"
    upload = f"/financeiro/upload-comprovantes/{identificador}"
    pagina = tesoureiro.get(editor)
    csrf = token(pagina)
    assert b'href="/financeiro/arquivos/comprovantes/ficticio.pdf"' in pagina.data
    assert tesoureiro.post(upload).status_code == 400
    resposta = tesoureiro.post(upload, data={
        "csrf_token": csrf, "comprovantes[]": (io.BytesIO(b"%PDF-1.4\nnovo ficticio"), "novo.pdf"),
    })
    assert resposta.status_code == 302
    with app.app_context():
        anexo = Comprovante.query.one()
        referencia, anexo_id = anexo.arquivo, anexo.id
    assert referencia.startswith("/financeiro/arquivos/comprovantes/")
    nome = referencia.rsplit("/", 1)[-1]
    arquivo = pasta / "privado/comprovantes" / nome
    assert arquivo.is_file()
    assert not (pasta / "static/uploads/comprovantes" / nome).exists()
    assert tesoureiro.get(referencia).data == arquivo.read_bytes()
    assert entrar(app, "secretario").get(referencia).status_code == 403
    assert app.test_client().get(referencia).status_code == 302
    assert tesoureiro.get("/static/uploads/comprovantes/" + nome).status_code == 404
    assert tesoureiro.post(f"/financeiro/excluir-comprovante-multiplo/{anexo_id}",
                           data={"csrf_token": csrf}).status_code == 302
    assert tesoureiro.get(referencia).status_code == 404
    with app.app_context():
        assert db.session.get(Comprovante, anexo_id) is None


def test_importacao_real_csv_e_limpeza(dados, monkeypatch):
    from app.financeiro.financeiro_model import ImportacaoExtrato, Lancamento
    from app.financeiro.utils.conciliacao_avancada import ImportadorExtrato

    app, pasta, _ = dados
    tesoureiro = entrar(app, "tesoureiro")
    csrf = token(tesoureiro.get("/financeiro/conciliacao/importar-extrato"))
    upload = "/financeiro/conciliacao/upload-extrato"
    conteudo = b"data;descricao;valor\n2026-07-13;Importacao ficticia;104.50\n"

    def enviar():
        return tesoureiro.post(upload, data={
            "csrf_token": csrf, "banco": "generico", "arquivo": (io.BytesIO(conteudo), "extrato.csv")
        })

    assert enviar().status_code == 302
    assert enviar().status_code == 302
    with app.app_context():
        registro = ImportacaoExtrato.query.one()
        assert registro.nome_arquivo == "extrato.csv"
        assert Lancamento.query.filter_by(origem="importado", descricao="Importacao ficticia").count() == 1
    assert not list((pasta / "privado/temporarios").iterdir())
    assert list((pasta / "static/uploads/extratos").iterdir()) == [pasta / "static/uploads/extratos/antigo.csv"]

    def falhar(*_args):
        raise RuntimeError("falha simulada do importador")

    monkeypatch.setattr(ImportadorExtrato, "importar_arquivo", falhar)
    assert enviar().status_code == 302
    assert not list((pasta / "privado/temporarios").iterdir())


def test_relatorio_e_pdf_continuam_acessiveis(dados):
    app, _, _ = dados
    tesoureiro = entrar(app, "tesoureiro")
    assert tesoureiro.get("/financeiro/relatorio?tipo_relatorio=livro_caixa&mes=7&ano=2026").status_code == 200
    pdf = tesoureiro.get("/financeiro/relatorio-caixa/pdf?mes=7&ano=2026&formato=livro_caixa")
    assert pdf.status_code == 200 and pdf.data.startswith(b"%PDF")


def test_comprovante_principal_preserva_vinculo_do_repasse(dados):
    from app.extensoes import db
    from app.financeiro.envios_sede_model import EnvioSede
    from app.financeiro.financeiro_model import Lancamento

    app, pasta, identificador = dados
    tesoureiro = entrar(app, "tesoureiro")
    editor = f"/financeiro/editar/{identificador}"
    csrf = token(tesoureiro.get(editor))
    resposta = tesoureiro.post("/financeiro/salvar", data={
        "csrf_token": csrf, "id": identificador, "tipo": "Entrada",
        "categoria": "OFERTAS", "data": "2026-07-12", "valor": "31,00",
        "conta": "Banco", "descricao": "Lançamento fictício",
        "comprovante": (io.BytesIO(b"%PDF-1.4\nnovo principal"), "principal.pdf"),
    })
    assert resposta.status_code == 302
    with app.app_context():
        lancamento = db.session.get(Lancamento, identificador)
        referencia = lancamento.comprovante
        db.session.add(EnvioSede(data_pagamento=date(2026, 7, 12), valor=31,
                                competencia="07/2026", comprovante=referencia))
        db.session.commit()
    assert referencia.startswith("/financeiro/arquivos/comprovantes/")
    assert tesoureiro.get(referencia).data.endswith(b"novo principal")
    assert tesoureiro.post(f"/financeiro/excluir-comprovante/{identificador}",
                           data={"csrf_token": csrf}).status_code == 302
    assert tesoureiro.get(referencia).status_code == 200
    assert (pasta / "privado/comprovantes" / referencia.rsplit("/", 1)[-1]).is_file()


def test_link_legado_com_host_nao_redireciona_para_fora(dados):
    from app.extensoes import db
    from app.financeiro.financeiro_model import Lancamento

    app, _, identificador = dados
    with app.app_context():
        lancamento = db.session.get(Lancamento, identificador)
        lancamento.comprovante = "https://antigo.example.test/static/uploads/comprovantes/ficticio.pdf"
        db.session.commit()
    tesoureiro = entrar(app, "tesoureiro")
    pagina = tesoureiro.get(f"/financeiro/editar/{identificador}")
    assert b'href="/financeiro/arquivos/comprovantes/ficticio.pdf"' in pagina.data
    assert b"antigo.example.test" not in pagina.data
    assert tesoureiro.get("/static/uploads/comprovantes/ficticio.pdf").status_code == 200
    assert tesoureiro.post(f"/financeiro/excluir-comprovante/{identificador}",
                           data={"csrf_token": token(pagina)}).status_code == 302
    assert tesoureiro.get("/static/uploads/comprovantes/ficticio.pdf").status_code == 404
