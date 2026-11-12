"""Identificadores Flask-Login vinculados a senha, sem migracao de banco.

O identificador assinado nao inclui o hash de senha em texto. Tokens legados
com somente ID inteiro sao intencionalmente rejeitados: deploy exige novo login.
"""
import hashlib
import hmac
import re


_ID_SESSAO = re.compile(r"v1:([1-9][0-9]{0,18}):([0-9a-f]{64})")


def extrair_usuario_id(identificador):
    """Retorna um inteiro positivo somente para identificadores no formato v1."""
    if not isinstance(identificador, str) or len(identificador) > 90:
        return None
    match = _ID_SESSAO.fullmatch(identificador)
    return int(match.group(1)) if match else None


def gerar_id_sessao(usuario_id, senha_hash, chave_secreta):
    """Assina o ID com HMAC do hash atual e da SECRET_KEY do ambiente."""
    if not isinstance(usuario_id, int) or usuario_id <= 0:
        raise ValueError("Identificador de usuario invalido")
    if not isinstance(senha_hash, str) or not senha_hash:
        raise ValueError("Hash de senha ausente")
    if isinstance(chave_secreta, str):
        chave_secreta = chave_secreta.encode("utf-8")
    if not isinstance(chave_secreta, bytes) or not chave_secreta:
        raise ValueError("SECRET_KEY ausente")
    mensagem = f"obpc-sessao-v1:{usuario_id}:{senha_hash}".encode("utf-8")
    assinatura = hmac.new(chave_secreta, mensagem, hashlib.sha256).hexdigest()
    return f"v1:{usuario_id}:{assinatura}"


def validar_id_sessao(identificador, senha_hash, chave_secreta):
    usuario_id = extrair_usuario_id(identificador)
    if usuario_id is None:
        return False
    try:
        esperado = gerar_id_sessao(usuario_id, senha_hash, chave_secreta)
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(identificador, esperado)
