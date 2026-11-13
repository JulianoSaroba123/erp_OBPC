"""Armazenamento privado com leitura compatível para comprovantes legados."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
from uuid import uuid4

from flask import abort, current_app, send_file, url_for
from werkzeug.utils import secure_filename

from app.extensoes import db


PREFIXO_LEGADO = "/static/uploads/comprovantes/"
PREFIXO_PRIVADO = "/financeiro/arquivos/comprovantes/"
MIMES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
}
EXTENSOES_UPLOAD = {".pdf", ".jpg", ".jpeg", ".png"}


def pasta_financeira_privada():
    """FINANCEIRO_ARQUIVOS_DIR permite usar um volume já provisionado."""
    pasta = Path(
        current_app.config.get("FINANCEIRO_ARQUIVOS_DIR")
        or Path(current_app.instance_path) / "arquivos_financeiros"
    ).resolve()
    if current_app.static_folder:
        estatico = Path(current_app.static_folder).resolve()
        if pasta.is_relative_to(estatico) or estatico.is_relative_to(pasta):
            raise ValueError("FINANCEIRO_ARQUIVOS_DIR não pode se sobrepor à pasta estática")
    return pasta


def nome_comprovante_valido(nome):
    if not isinstance(nome, str) or not nome or len(nome.encode("utf-8")) > 255:
        return False
    return (
        not nome.startswith(".")
        and not any(char in nome for char in ("/", "\\", ":", "%", "?", "#"))
        and not any(ord(char) < 32 or ord(char) == 127 for char in nome)
        and Path(nome).suffix.lower() in MIMES
    )


def nome_da_referencia(referencia):
    if not isinstance(referencia, str) or not referencia.strip():
        return None
    try:
        partes = urlsplit(referencia.strip())
    except ValueError:
        return None
    if partes.scheme and partes.scheme not in {"http", "https"}:
        return None
    caminho = "/" + unquote(partes.path).lstrip("/")
    for prefixo in (PREFIXO_LEGADO, PREFIXO_PRIVADO):
        if caminho.startswith(prefixo):
            nome = caminho[len(prefixo):]
            return nome if nome_comprovante_valido(nome) else None
    return None


def url_comprovante(referencia, *, externa=False):
    nome = nome_da_referencia(referencia)
    if not nome:
        return None
    return url_for("financeiro.abrir_comprovante", nome=nome, _external=externa)


def _arquivo_existente(pasta, nome):
    # O nome é uma única parte e links simbólicos não são documentos do ERP.
    caminho = pasta / nome
    if not pasta.is_symlink() and not caminho.is_symlink() and caminho.is_file() and caminho.resolve().parent == pasta.resolve():
        return caminho
    return None


def _referencia_ativa(nome, prefixo):
    from sqlalchemy import inspect
    from app.financeiro.comprovante_model import Comprovante
    from app.financeiro.envios_sede_model import EnvioSede
    from app.financeiro.financeiro_model import Lancamento
    from app.financeiro.obrigacoes_model import PagamentoObrigacao

    referencia = prefixo + nome
    colunas = [Lancamento.comprovante, Comprovante.arquivo, EnvioSede.comprovante]
    insp = inspect(db.session.connection())

    def possui_vinculo(coluna):
        if not insp.has_table(coluna.class_.__tablename__):
            return False
        if db.session.query(coluna).filter(coluna.in_((referencia, referencia.lstrip("/")))).first():
            return True
        if prefixo != PREFIXO_LEGADO:
            return False
        # URLs antigas por vezes foram salvas com host. Só o caminho local é usado.
        candidatos = db.session.query(coluna).filter(coluna.contains(nome, autoescape=True))
        return any(nome_da_referencia(valor) == nome for (valor,) in candidatos)

    return any(possui_vinculo(coluna) for coluna in (*colunas, PagamentoObrigacao.comprovante))


def localizar_comprovante(nome, *, legado_apenas=False):
    if not nome_comprovante_valido(nome):
        return None
    legado = Path(current_app.static_folder) / "uploads" / "comprovantes"
    if not legado_apenas:
        privado = _arquivo_existente(pasta_financeira_privada() / "comprovantes", nome)
        if privado:
            return privado if _referencia_ativa(nome, PREFIXO_PRIVADO) else None
    arquivo = _arquivo_existente(legado, nome)
    return arquivo if arquivo and _referencia_ativa(nome, PREFIXO_LEGADO) else None


def servir_comprovante(nome, *, legado_apenas=False):
    caminho = localizar_comprovante(nome, legado_apenas=legado_apenas)
    if caminho is None:
        abort(404)
    resposta = send_file(caminho, mimetype=MIMES[caminho.suffix.lower()], max_age=0)
    resposta.headers["Cache-Control"] = "private, no-store"
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    return resposta


def gravar_comprovante(file):
    nome_original = secure_filename(file.filename or "")
    extensao = Path(nome_original).suffix.lower()
    if extensao not in EXTENSOES_UPLOAD:
        raise ValueError("Extensão de comprovante inválida")
    nome_original = Path(nome_original).stem[:180] + extensao
    nome = f"{uuid4().hex}_{nome_original}"
    pasta = pasta_financeira_privada() / "comprovantes"
    pasta.mkdir(mode=0o700, parents=True, exist_ok=True)
    if pasta.is_symlink():
        raise OSError("Pasta de comprovantes inválida")
    caminho = pasta / nome
    destino = caminho.open("xb")
    try:
        with destino:
            file.save(destino)
    except Exception:
        caminho.unlink(missing_ok=True)
        raise
    return PREFIXO_PRIVADO + nome, nome_original, caminho
