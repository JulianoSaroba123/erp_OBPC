# -*- coding: utf-8 -*-
"""Regressao HTTP isolada do financeiro, CSRF e login.

Executar via test_p0_http_integrado.py, sempre em subprocesso com
banco SQLite descartavel e bloqueio de conexoes externas.
A mini-rota /__p05h/token existe somente na instancia de teste.
"""
import gc
import os
import platform
import secrets
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DB_NAME = "isolado_p06d.sqlite"


def fail(message):
    raise AssertionError(message)


def test_case(label, response, expected, predicate=None):
    print(f"{label}: HTTP {response.status_code} (esperado {expected})", flush=True)
    if response.status_code != expected:
        fail(f"{label}: resposta inesperada: {response.status_code}; conteudo: {response.get_data(as_text=True)[:280]!r}")
    if predicate is not None and not predicate(response):
        fail(f"{label}: o conteudo nao corresponde ao esperado")


def main():
    # Executa apenas a partir da raiz deste checkout (sem caminhos externos).
    if Path.cwd().resolve() != REPO:
        fail("Execute a partir da raiz do repositorio.")

    # Evita que a identificacao local do Windows use subprocessos depois do bloqueio.
    platform.uname()
    platform.win32_ver()

    temp_dir = Path(tempfile.mkdtemp(prefix="OBPC_P06D_"))
    sqlite_file = (temp_dir / DB_NAME).resolve()
    os.environ["DATABASE_URL"] = "sqlite:///" + sqlite_file.as_posix()
    os.environ["SECRET_KEY"] = "p05h-ficticia-" + secrets.token_hex(32)
    os.environ["FLASK_ENV"] = "testing"
    os.environ["RENDER"] = "false"
    os.environ.pop("SQLALCHEMY_DATABASE_URI", None)

    blocked = []
    ipv6_probes = []
    app_instance = None
    database = None
    error = None
    cleanup_failure = None

    def safety_audit(event, args):
        if event == "sqlite3.connect":
            target = args[0]
            if target == ":memory:":
                return
            try:
                allowed = Path(os.fsdecode(target)).resolve() == sqlite_file
            except (OSError, TypeError, ValueError):
                allowed = False
            if not allowed:
                blocked.append("sqlite3.connect fora do banco temporario")
                raise RuntimeError("Conexao SQLite externa bloqueada")
        elif event == "socket.bind":
            address = args[1] if len(args) > 1 else None
            origin = any(
                frame.name == "_has_ipv6"
                and frame.filename.replace("\\", "/").endswith("/urllib3/util/connection.py")
                for frame in traceback.extract_stack(limit=14)
            )
            local_ipv6_probe = (
                isinstance(address, tuple) and len(address) >= 2
                and address[0] == "::1" and address[1] == 0 and origin
            )
            if local_ipv6_probe:
                ipv6_probes.append(True)
                return
            blocked.append("socket.bind")
            raise RuntimeError("Socket bind nao autorizado")
        elif event in {"socket.connect", "subprocess.Popen", "os.system"}:
            blocked.append(event)
            raise RuntimeError(f"Operacao externa bloqueada: {event}")

    # A descoberta de bibliotecas nativas pelo WeasyPrint pode executar
    # ldconfig/gcc na inicializacao. Carregar essa dependencia confiavel
    # ANTES do audit hook evita falsos positivos no harness e conserva
    # o bloqueio total de subprocessos durante a inicializacao do ERP.
    import weasyprint  # noqa: F401

    sys.addaudithook(safety_audit)

    try:
        import app as erp
        from flask import jsonify
        from flask_login import UserMixin
        from flask_wtf.csrf import generate_csrf
        from sqlalchemy import inspect, text
        from sqlalchemy.engine import make_url
        from app.config import Config
        from app.extensoes import db, login_manager
        from app.notificacoes import tarefas_agendadas

        url = make_url(Config.SQLALCHEMY_DATABASE_URI)
        assert url.get_backend_name() == "sqlite", "O URL nao e SQLite"
        assert Path(url.database).resolve() == sqlite_file, "Banco diferente do temporario"
        assert Config.SECRET_KEY == os.environ["SECRET_KEY"], "Chave nao e ficticia"

        scheduler_calls = []
        def disable_scheduler(flask_app):
            scheduler_calls.append(1)
            return None
        tarefas_agendadas.iniciar_scheduler = disable_scheduler

        app_instance = erp.create_app()
        database = db
        assert scheduler_calls == [1], "Scheduler nao foi interceptado uma vez"
        assert tarefas_agendadas.scheduler is None, "Scheduler real em execucao"
        assert app_instance.config["WTF_CSRF_CHECK_DEFAULT"] is False
        assert app_instance.config["SECRET_KEY"] == os.environ["SECRET_KEY"]
        assert not blocked, f"Operacoes bloqueadas durante a inicializacao: {blocked}"
        # Evita propagacao de excecoes nos testes HTTP: observar respostas reais.
        app_instance.config["TESTING"] = False
        app_instance.config["PROPAGATE_EXCEPTIONS"] = False

        # Usuario ficticio, sem salvar usuarios no banco ou utilizar login real.
        class FakeUser(UserMixin):
            def __init__(self, user_id, role):
                self.id = user_id
                self.nome = "Usuario ficticio P05H"
                self.nivel_acesso = role
            def tem_acesso_financeiro(self):
                return self.nivel_acesso in {"master", "administrador", "Admin", "tesoureiro"}
            def tem_acesso_configuracoes(self):
                return self.nivel_acesso in {"master", "administrador", "Admin"}
            def pode_gerenciar_eventos(self):
                return self.nivel_acesso in {"master", "administrador", "lider_departamento", "midia"}
            def get_menu_principal(self):
                return "usuario.painel"

        fake_users = {
            "p05h_allowed": FakeUser("p05h_allowed", "tesoureiro"),
            "p05h_denied": FakeUser("p05h_denied", "membro"),
        }
        login_manager.user_loader(lambda uid: fake_users.get(uid))

        # Rotas locais de observacao; nao sao adicionadas ao codigo-fonte do ERP.
        @app_instance.get("/__p05h/token")
        def csrf_test_token():
            return jsonify({"token": generate_csrf()})

        @app_instance.post("/__p05h/outro-modulo")
        def unrelated_post():
            return "fora-do-financeiro", 200

        allowed = app_instance.test_client()
        denied = app_instance.test_client()
        anonymous = app_instance.test_client()
        for client, user_id in [(allowed, "p05h_allowed"), (denied, "p05h_denied")]:
            with client.session_transaction() as session:
                session["_user_id"] = user_id
                session["_fresh"] = True

        token_response = allowed.get("/__p05h/token")
        assert token_response.status_code == 200, "Nao foi possivel gerar o CSRF local"
        valid_token = token_response.get_json()["token"]
        assert valid_token and isinstance(valid_token, str)

        # Flask-WTF verifica Referer em HTTPS. O navegador real o envia
        # em requisicoes POST normais de mesma origem. Nao desativar SSL_STRICT.
        HTTPS_ORIGIN = "https://localhost"
        SAME_ORIGIN = {"Referer": HTTPS_ORIGIN + "/financeiro/conciliacao"}

        def https_get(cliente, endereco, **kwargs):
            return cliente.get(endereco, base_url=HTTPS_ORIGIN, **kwargs)

        def https_post(cliente, endereco, **kwargs):
            kwargs.setdefault("headers", {"Referer": HTTPS_ORIGIN + "/login"})
            return cliente.post(endereco, base_url=HTTPS_ORIGIN, **kwargs)
        assert app_instance.config.get("WTF_CSRF_SSL_STRICT", True) is True

        conciliacao = "/financeiro/conciliacao/criar-par"  # Sem IDs -> sem gravacoes
        exportacao = "/financeiro/conciliacao/export_pairs"  # Sem pares -> sem gravacoes

        with app_instance.app_context():
            tabelas = set(inspect(db.engine).get_table_names())
            assert "lancamentos" in tabelas, "Tabela de lancamentos ausente"
            n_antes = db.session.execute(text("SELECT COUNT(*) FROM lancamentos")).scalar_one()

        print("\n=== P0.5H | TESTES HTTP AUTENTICADOS ===", flush=True)
        test_case("01 Financeiro autorizado, sem token", allowed.post(exportacao, data={}, base_url=HTTPS_ORIGIN, headers=SAME_ORIGIN), 400)
        test_case("02 Financeiro autorizado, token invalido", allowed.post(exportacao, data={"csrf_token": "invalido"}, base_url=HTTPS_ORIGIN, headers=SAME_ORIGIN), 400)
        missing_referer = allowed.post(exportacao, data={"csrf_token": valid_token}, base_url=HTTPS_ORIGIN)
        assert missing_referer.status_code == 400, "HTTPS sem Referer deveria ser bloqueado"
        assert b"referrer" in missing_referer.data.lower(), "Motivo de bloqueio inesperado"
        print("OK: HTTPS com token valido e sem Referer foi rejeitado.")
        test_case("03 Financeiro autorizado, token valido", allowed.post(exportacao, data={"csrf_token": valid_token}, base_url=HTTPS_ORIGIN, headers=SAME_ORIGIN), 302)

        test_case("04 Conciliacao autorizada, sem token", allowed.post(conciliacao, data={}, base_url=HTTPS_ORIGIN, headers=SAME_ORIGIN), 400)
        test_case("05 Conciliacao autorizada, token invalido", allowed.post(conciliacao, data={"csrf_token": "invalido"}, base_url=HTTPS_ORIGIN, headers=SAME_ORIGIN), 400)
        test_case(
            "06 Conciliacao autorizada, token valido e sem IDs",
            allowed.post(conciliacao, data={"csrf_token": valid_token}, base_url=HTTPS_ORIGIN, headers=SAME_ORIGIN), 200,
            lambda res: res.is_json and res.get_json().get("success") is False,
        )
        test_case("07 Acesso negado, sem token, financeiro", denied.post(exportacao, data={}), 403)
        test_case("08 Acesso negado, token valido, financeiro", denied.post(exportacao, data={"csrf_token": valid_token}), 403)
        test_case("09 Acesso negado, sem token, conciliacao", denied.post(conciliacao, data={}), 403)
        test_case("10 Acesso anonimo ao financeiro", anonymous.post(exportacao, data={}), 302)
        test_case("11 Acesso anonimo a conciliacao", anonymous.post(conciliacao, data={}), 302)
        test_case("12 Modulo de teste fora do financeiro, sem CSRF", anonymous.post("/__p05h/outro-modulo"), 200)
        test_case("13 Exclusao por GET continua proibida", anonymous.get("/financeiro/excluir/1"), 405)
        test_case("14 Conciliacao automatica por GET continua proibida", anonymous.get("/financeiro/conciliacao/executar-automatica"), 405)

        # A7H.28: perfil textual 'Pastor' nao pode autorizar limpeza destrutiva.
        fake_users["p05h_denied"].perfil = "Pastor"
        test_case(
            "15 Autocadastrado Pastor com nivel membro nao pode limpar dados",
            denied.get("/configuracoes/limpar-dados-sistema"), 403,
        )
        fake_users["p05h_master"] = FakeUser("p05h_master", "master")
        master_efemero = app_instance.test_client()
        with master_efemero.session_transaction() as sessao:
            sessao["_user_id"] = "p05h_master"
            sessao["_fresh"] = True
        test_case(
            "16 Master nao pode limpar dados sem token CSRF",
            master_efemero.post(
                "/configuracoes/limpar-dados-sistema",
                data={"senha_confirmacao": "invalida", "confirmacao_texto": "LIMPAR TUDO"},
            ), 400,
        )
        test_case(
            "16A Membro nao pode alterar configuracoes",
            denied.post("/configuracoes/salvar", data={"nome_igreja": "NUNCA"}), 403,
        )
        test_case(
            "16B Membro nao pode resetar configuracoes",
            denied.post("/configuracoes/resetar", data={"aba": "gerais"}), 403,
        )
        test_case(
            "16C Master sem CSRF nao pode resetar configuracoes",
            master_efemero.post("/configuracoes/resetar", data={"aba": "gerais"}), 400,
        )
        # A7H.29: exercita a autorizacao de rotas legadas SEM executar mutacoes.
        token_negado = https_get(denied, "/__p05h/token").get_json()["token"]
        test_case(
            "16D Membro nao consulta configuracoes de notificacoes",
            denied.get("/notificacoes/configuracoes"), 403,
        )
        test_case(
            "16E Membro nao testa envio de email",
            https_post(denied,
                "/notificacoes/testar-email",
                data={"csrf_token": token_negado, "email_teste": "fake@invalid.test"},
            ), 403,
        )
        test_case(
            "16F Master nao envia notificacao sem token",
            master_efemero.post("/notificacoes/testar-email",
                               data={"email_teste": "fake@invalid.test"}), 400,
        )
        test_case(
            "16G Exclusao de evento nao aceita GET",
            denied.get("/eventos/excluir/1"), 405,
        )
        test_case(
            "16H Membro nao cadastra evento com token valido",
            denied.post("/eventos/salvar", data={"csrf_token": token_negado}), 403,
        )
        test_case(
            "16I Master nao exclui evento sem CSRF",
            master_efemero.post("/eventos/excluir/1"), 400,
        )
        test_case(
            "16J Diagnostico de usuarios oculto em producao",
            master_efemero.get("/usuarios/debug-info"), 404,
        )
        test_case(
            "16K Atualizacao administrativa nao aceita GET",
            master_efemero.get("/admin/atualizar-atividades-painel"), 405,
        )
        test_case(
            "16L Atualizacao administrativa nao aceita POST sem CSRF",
            master_efemero.post("/admin/atualizar-atividades-painel"), 400,
        )

        with app_instance.app_context():
            n_depois = db.session.execute(text("SELECT COUNT(*) FROM lancamentos")).scalar_one()
            assert n_antes == n_depois, "Quantidade de lancamentos alterada nos testes"
        # P0.6D-B: testa o login REAL, com usuario/senha ficticios apenas
        # no banco descartavel. Nao reutiliza a autenticacao simulada P0.5H.
        from app.usuario.usuario_model import Usuario, load_user
        from flask import url_for
        from html.parser import HTMLParser
        from urllib.parse import quote, parse_qs, urlsplit

        class LoginForm(HTMLParser):
            def __init__(self):
                super().__init__()
                self.action = None
                self.csrf_token = None
            def handle_starttag(self, tag, attrs):
                d = dict(attrs)
                if tag.lower() == "form" and (d.get("method") or "").lower() == "post":
                    if self.action is None:
                        self.action = d.get("action")
                if tag.lower() == "input" and d.get("name") == "csrf_token":
                    self.csrf_token = d.get("value")

        with app_instance.app_context():
            assert "usuarios" in set(inspect(db.engine).get_table_names())
            conta = Usuario(
                nome="Teste P06D - descartavel",
                email="p06d-usuario@invalid.test",
                nivel_acesso="tesoureiro",
                ativo=True,
            )
            conta.set_senha("TesteP06D-SomenteLocal-2026!")
            db.session.add(conta)
            db.session.commit()
            conta_id = conta.id
            assert conta_id is not None

        # Login Manager volta a buscar os usuarios reais, mas APENAS do banco temporario.
        login_manager.user_loader(load_user)

        with app_instance.test_request_context():
            fallback = url_for("financeiro.lista_lancamentos")

        senha_ficticia = "TesteP06D-SomenteLocal-2026!"
        dados_login = {"email": "p06d-usuario@invalid.test", "senha": senha_ficticia}

        def fazer_login(next_destino):
            navegador = app_instance.test_client()
            if next_destino is None:
                pagina = "/login"
            else:
                pagina = "/login?next=" + quote(next_destino, safe="")
            get_response = https_get(navegador, pagina)
            assert get_response.status_code == 200, (
                "GET login falhou: " + str(get_response.status_code)
            )
            parser = LoginForm()
            parser.feed(get_response.get_data(as_text=True))
            assert parser.action is not None, "Form de login sem action"
            assert parser.csrf_token, "CSRF ausente do formulario de login"
            test_case(
                "Login sem CSRF bloqueado",
                https_post(navegador, parser.action, data=dados_login, follow_redirects=False),
                400,
            )
            # Verifica que o formulario realmente transmite o next no POST.
            if next_destino is not None:
                recebido = parse_qs(urlsplit(parser.action).query).get("next")
                assert recebido == [next_destino], (
                    "Formulario nao preservou next: " + repr(recebido)
                )
            res = https_post(
                navegador, parser.action,
                data={**dados_login, "csrf_token": parser.csrf_token},
                follow_redirects=False,
            )
            assert res.status_code == 302, (
                "POST login deveria redirecionar: HTTP " + str(res.status_code)
            )
            return res.headers.get("Location", "")

        destinos_validos = [
            "/financeiro/lista",
            "/financeiro/conciliacao?mes=11&ano=2026",
            "/usuario/painel",
        ]
        destinos_invalidos = [
            "https://externo.invalid/login",
            "http://externo.invalid",
            "//externo.invalid",
            "///externo.invalid",
            "/\\externo.invalid",
            "/%2fexterno.invalid",
            "/%5cexterno.invalid",
            "/%252fexterno.invalid",
            "/%255cexterno.invalid",
        ]

        for destino in destinos_validos:
            location = fazer_login(destino)
            assert location == destino, (
                "Destino interno foi alterado: " + repr(location)
            )
            print("OK: login redireciona para caminho interno:", destino)

        for destino in destinos_invalidos:
            location = fazer_login(destino)
            assert location == fallback, (
                f"Destino externo nao foi rejeitado ({destino!r}): {location!r}"
            )
            print("OK: login rejeitou destino inseguro:", destino)

        location = fazer_login(None)
        assert location == fallback, (
            "Login sem next deveria ir ao painel padrao: " + repr(location)
        )
        print("OK: login sem next mantem destino padrao.")

        # A7H.28: fluxo REAL de cadastro e gestao Master no mesmo SQLite efemero.
        publico = app_instance.test_client()
        token_publico = https_get(publico, "/__p05h/token").get_json()["token"]
        cadastro_publico = {
            "nome": "Membro P28 ficticio", "email": "p28-membro@invalid.test",
            "senha": "SenhaLongaPublica!2026", "perfil": "Pastor",
            "nivel_acesso": "master", "csrf_token": token_publico,
        }
        test_case("17 Cadastro publico sem CSRF", https_post(publico,
            "/cadastro", data={k: v for k, v in cadastro_publico.items() if k != "csrf_token"}
        ), 400)
        test_case("18 Cadastro publico com perfil Pastor forjado", https_post(publico,
            "/cadastro", data=cadastro_publico, follow_redirects=False,
        ), 302)
        with app_instance.app_context():
            membro = Usuario.query.filter_by(email="p28-membro@invalid.test").one()
            assert membro.nivel_acesso == "membro" and membro.perfil == "Membro"
            master = Usuario(
                nome="Master P28 ficticio", email="p28-master@invalid.test",
                nivel_acesso="master", perfil="Master", ativo=True,
            )
            master.set_senha("SenhaMasterFicticia2026!")
            db.session.add(master)
            db.session.commit()

        navegador_master = app_instance.test_client()
        tela_login = https_get(navegador_master, "/login")
        parser_master = LoginForm()
        parser_master.feed(tela_login.get_data(as_text=True))
        assert parser_master.csrf_token
        test_case("19 Login real do Master ficticio", https_post(navegador_master,
            parser_master.action,
            data={"email": "p28-master@invalid.test",
                  "senha": "SenhaMasterFicticia2026!",
                  "csrf_token": parser_master.csrf_token},
            follow_redirects=False,
        ), 302)
        test_case("20 Tela de criacao de usuarios para Master", https_get(navegador_master,
            "/usuarios/novo"
        ), 200)
        token_master = https_get(navegador_master, "/__p05h/token").get_json()["token"]
        criacao = {
            "nome": "Segundo Master P28", "email": "p28-master2@invalid.test",
            "senha": "SenhaMasterSegunda2026!", "confirmar_senha": "SenhaMasterSegunda2026!",
            "nivel_acesso": "master", "csrf_token": token_master,
        }
        test_case("21 Criar Master sem CSRF bloqueado", https_post(navegador_master,
            "/usuarios/novo", data={k: v for k, v in criacao.items() if k != "csrf_token"},
        ), 400)
        test_case("22 Criar Master sem reautenticacao bloqueado", https_post(navegador_master,
            "/usuarios/novo", data=criacao,
        ), 200)
        with app_instance.app_context():
            assert Usuario.query.filter_by(email="p28-master2@invalid.test").first() is None
        criacao["confirmar_senha_admin"] = "SenhaMasterFicticia2026!"
        test_case("23 Criar Master com senha do gestor", https_post(navegador_master,
            "/usuarios/novo", data=criacao, follow_redirects=False,
        ), 302)
        with app_instance.app_context():
            novo_master = Usuario.query.filter_by(email="p28-master2@invalid.test").one()
            novo_id = novo_master.id

        edicao = {
            "nome": "Master P28 auditado", "email": "p28-master2@invalid.test",
            "nivel_acesso": "master", "ativo": "on", "csrf_token": token_master,
        }
        test_case("24 Editar Master sem reautenticacao bloqueado", https_post(navegador_master,
            f"/usuarios/{novo_id}/editar", data=edicao,
        ), 200)
        with app_instance.app_context():
            assert db.session.get(Usuario, novo_id).nome == "Segundo Master P28"
        edicao["confirmar_senha_admin"] = "SenhaMasterFicticia2026!"
        test_case("25 Editar Master autenticado", https_post(navegador_master,
            f"/usuarios/{novo_id}/editar", data=edicao, follow_redirects=False,
        ), 302)
        with app_instance.app_context():
            assert db.session.get(Usuario, novo_id).nome == "Master P28 auditado"

        perfil_base = {
            "nome": "Master P28 ficticio", "email": "p28-master@invalid.test",
            "senha_atual": "SenhaMasterFicticia2026!",
            "nova_senha": "curta", "confirmar_senha": "curta",
            "csrf_token": token_master,
        }
        test_case("26 Perfil sem CSRF bloqueado", https_post(navegador_master,
            "/perfil", data={k: v for k, v in perfil_base.items() if k != "csrf_token"},
        ), 400)
        test_case("27 Troca de senha curta rejeitada", https_post(navegador_master,
            "/perfil", data=perfil_base,
        ), 200)
        perfil_base["nova_senha"] = "NovaSenhaSegura2026!"
        perfil_base["confirmar_senha"] = "NovaSenhaSegura2026!"
        test_case("28 Troca de senha valida exige novo login", https_post(navegador_master,
            "/perfil", data=perfil_base, follow_redirects=False,
        ), 302)
        test_case("29 Sessao anterior encerrada", https_get(navegador_master, "/usuarios"), 302)
        with app_instance.app_context():
            master_recarregado = Usuario.query.filter_by(email="p28-master@invalid.test").one()
            assert master_recarregado.check_senha("NovaSenhaSegura2026!")
            assert not master_recarregado.check_senha("SenhaMasterFicticia2026!")
        print("OK: A7H.28 - cadastro, CSRF, Master e politica de senha validados.", flush=True)

        # Garante novamente que nenhuma movimentacao foi realizada.
        with app_instance.app_context():
            n_login_depois = db.session.execute(text("SELECT COUNT(*) FROM lancamentos")).scalar_one()
        assert n_login_depois == n_antes, "Movimentacoes alteradas na homologacao de login"
        print("OK: login real validado com conta ficticia e banco descartavel.")

        assert not blocked, f"Operacoes externas bloqueadas: {blocked}"
        print("OK: 14 verificacoes HTTP anteriores + 13 cenarios de login.")
        print("OK: quantidade de lancamentos preservada.")
        print(f"OK: sondagens IPv6 locais permitidas: {len(ipv6_probes)}")

    except Exception as exc:
        error = exc
        traceback.print_exc()
    finally:
        print("\n=== ENCERRAMENTO ===", flush=True)
        if app_instance is not None and database is not None:
            try:
                with app_instance.app_context():
                    database.session.remove()
                    database.engine.dispose()
                print("OK: conexoes SQLAlchemy encerradas.")
            except Exception as exc:
                cleanup_failure = exc
                print("FALHA ao encerrar SQLAlchemy:", repr(exc))
        gc.collect()
        try:
            shutil.rmtree(temp_dir)
            print("OK: pasta temporaria excluida.")
        except OSError as exc:
            cleanup_failure = exc
            print("FALHA ao excluir pasta temporaria:", repr(exc))
            print("Diretorio temporario:", temp_dir)
        if blocked:
            print("AVISO: operacoes bloqueadas:", blocked)
            if error is None:
                error = RuntimeError("Houve tentativas de operacoes externas")

    if error is not None or cleanup_failure is not None:
        print("P0.6D-B: NAO APROVADA")
        return 1
    print("\nP0.6D-B: LOGIN REAL E HOMOLOGACAO HTTP APROVADOS.")
    print("Sem commit, deploy, servidor externo ou banco real.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
