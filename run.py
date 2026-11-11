"""Ponto de entrada WSGI do ERP OBPC.

Importar este modulo pelo Gunicorn nao inicia o servidor de desenvolvimento
nem executa criacao automatica de administrador pelo run.py.
A fabrica create_app() ainda possui inicializacoes legadas, tratadas a parte.
"""

import os

from app import create_app


app = create_app()


if __name__ == "__main__":
    # Uso local explicito; em producao, iniciar com gunicorn run:app.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
