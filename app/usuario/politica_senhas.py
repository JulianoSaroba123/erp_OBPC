"""Politica central de novas senhas. Nao invalida senhas existentes no login."""

MINIMO_SENHA = 12
MAXIMO_SENHA = 128


def validar_nova_senha(senha):
    """Retorna mensagem de erro ou None; nunca registra/exibe a senha."""
    if not isinstance(senha, str):
        return "Informe uma senha valida."
    if len(senha) < MINIMO_SENHA:
        return f"A senha deve ter pelo menos {MINIMO_SENHA} caracteres."
    if len(senha) > MAXIMO_SENHA:
        return f"A senha deve ter no maximo {MAXIMO_SENHA} caracteres."
    if senha.isspace() or "\x00" in senha:
        return "Escolha uma senha valida, sem caracteres nulos."
    return None
