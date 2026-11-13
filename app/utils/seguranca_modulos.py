"""A7H.30 | ACL explicita e CSRF escopado para modulos legados.

Nao modifica a configuracao global de CSRF nem o banco de dados.
O bloqueio de acesso acontece no servidor, antes de qualquer consulta.
"""
from flask import abort, request
from flask_login import current_user
from app.extensoes import csrf

_METODOS_MUTACAO = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def proteger_modulo_legado(permissao):
    """Exige metodo de permissao no usuario e CSRF nas mutacoes.

    A requisicao anonima prossegue para @login_required da propria rota,
    preservando o fluxo atual de login.
    """
    if not current_user.is_authenticated:
        return None

    verificador = getattr(current_user, permissao, None)
    if not callable(verificador) or not verificador():
        abort(403)

    if request.method in _METODOS_MUTACAO:
        csrf.protect()
    return None
