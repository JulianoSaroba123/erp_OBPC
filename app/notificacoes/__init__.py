"""Inicialização do módulo de notificações.

D23D50 instala o corretor read-only do dashboard somente quando o módulo
financeiro já foi carregado pela aplicação, evitando import circular.
"""

import logging
import sys


def _instalar_d23d50_se_disponivel():
    if "app.financeiro.financeiro_routes" not in sys.modules:
        return

    try:
        from app.financeiro.dashboard_d23d50 import instalar_correcao_dashboard_d23d50

        instalar_correcao_dashboard_d23d50()
    except Exception:
        logging.getLogger(__name__).exception("D23D50: falha ao instalar correção do dashboard financeiro")


_instalar_d23d50_se_disponivel()
