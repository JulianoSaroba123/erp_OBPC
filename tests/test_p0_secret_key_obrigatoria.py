
"""P0.4C: usa apenas AST de create_app + Config via runpy; sem ERP ou DB."""
import ast
import copy
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / 'app/config.py'
APP_PATH = ROOT / 'app/__init__.py'


def _configuracao(monkeypatch, chave):
    # Executa somente app/config.py (stdlib), sem importar pacote app ou DB.
    monkeypatch.delenv('DATABASE_URL', raising=False)
    if chave is None:
        monkeypatch.delenv('SECRET_KEY', raising=False)
    else:
        monkeypatch.setenv('SECRET_KEY', chave)
    return runpy.run_path(str(CONFIG_PATH), run_name='__teste_config_p04c__')['Config']


class _ConfigFicticia(dict):
    def from_object(self, obj):
        self['SECRET_KEY'] = obj.SECRET_KEY


class _FlaskFicticio:
    def __init__(self, *_args, **_kwargs):
        self.config = _ConfigFicticia()


def _primeiro_bloco_create_app(config_cls):
    # Compila so as 4 primeiras instrucoes: Flask(), Config, chave e guard.
    # NENHUM import de app nem inicializacao de SQLAlchemy pode ser realizado.
    source = APP_PATH.read_text(encoding='utf-8-sig')
    tree = ast.parse(source)
    factory = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'create_app')
    assert isinstance(factory.body[3], ast.If), 'Guard deve vir logo apos ler a chave'
    m = ast.Module(body=[ast.FunctionDef(
        name='create_app_config_apenas',
        args=copy.deepcopy(factory.args),
        body=[copy.deepcopy(n) for n in factory.body[:4]] + [
            ast.Return(value=ast.Name(id='app', ctx=ast.Load()))],
        decorator_list=[],
        returns=None,
        type_comment=None,
    )], type_ignores=[])
    ast.fix_missing_locations(m)
    namespace = {'__name__': '__teste_p04c__', 'Flask': _FlaskFicticio, 'Config': config_cls}
    exec(compile(m, str(APP_PATH), 'exec'), namespace)
    return namespace['create_app_config_apenas']()


def test_variavel_definida_usa_valor_exato_sem_rotacao(monkeypatch):
    # Sem logs ou tela exibindo a chave.
    chave = 'valor-exclusivo-somente-para-testes-p04c-2026'
    cfg = _configuracao(monkeypatch, chave)
    assert cfg.SECRET_KEY == chave


def test_valor_diferente_na_variavel_nao_e_substituido(monkeypatch):
    outro = 'outro-valor-aleatorio-apenas-para-testes-p04c-2026'
    assert _configuracao(monkeypatch, outro).SECRET_KEY == outro


def test_ausencia_da_variavel_nao_recebe_fallback(monkeypatch):
    cfg = _configuracao(monkeypatch, None)
    assert cfg.SECRET_KEY is None
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        _primeiro_bloco_create_app(cfg)


def test_variavel_vazia_bloqueia_inicializacao(monkeypatch):
    cfg = _configuracao(monkeypatch, '')
    assert not cfg.SECRET_KEY
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        _primeiro_bloco_create_app(cfg)


def test_chave_apenas_espacos_bloqueia_inicializacao(monkeypatch):
    cfg = _configuracao(monkeypatch, '   ')
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        _primeiro_bloco_create_app(cfg)


def test_chave_valida_aceita_antes_do_banco(monkeypatch):
    chave = 'somente-testes-p04c-chave-estavel-2026'
    cfg = _configuracao(monkeypatch, chave)
    app = _primeiro_bloco_create_app(cfg)
    assert app.config['SECRET_KEY'] == chave
    tree = ast.parse(APP_PATH.read_text(encoding='utf-8-sig'))
    factory = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'create_app')
    assert 'app.config.from_object(Config)' in ast.unparse(factory.body[1])
    assert isinstance(factory.body[3], ast.If)
    linhas = APP_PATH.read_text(encoding='utf-8-sig').splitlines()
    pos_guard = next(i for i, s in enumerate(linhas) if "chave = app.config.get('SECRET_KEY')" in s)
    pos_db = next(i for i, s in enumerate(linhas) if 'db.init_app(app)' in s)
    assert pos_guard < pos_db


def test_codigo_nao_contem_chave_publica_nem_fallback(monkeypatch):
    codigo = CONFIG_PATH.read_text(encoding='utf-8-sig')
    assert 'chave-secreta-obpc-2025-igreja-brasil-para-cristo' not in codigo
    assert "SECRET_KEY = os.environ.get('SECRET_KEY') or None" in codigo
    assert _configuracao(monkeypatch, None).SECRET_KEY is None
