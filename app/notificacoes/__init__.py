"""Inicialização do módulo de notificações.

D23D50, D23D53 e D23D54 instalam adaptadores read-only somente quando o
módulo financeiro já foi carregado pela aplicação, evitando import circular.
"""

import logging
import sys


def _instalar_adaptadores_financeiros_se_disponiveis():
    if "app.financeiro.financeiro_routes" not in sys.modules:
        return

    try:
        from app.financeiro.dashboard_d23d50 import instalar_correcao_dashboard_d23d50

        instalar_correcao_dashboard_d23d50()
    except Exception:
        logging.getLogger(__name__).exception("D23D50: falha ao instalar correção do dashboard financeiro")

    try:
        from app.financeiro.relatorio_sede_d23d53 import instalar_correcao_relatorio_sede_d23d53

        instalar_correcao_relatorio_sede_d23d53()
    except Exception:
        logging.getLogger(__name__).exception("D23D53: falha ao instalar correção do relatório da Sede")

    try:
        from app.financeiro.relatorio_workspace_d23d54 import instalar_workspace_relatorios_d23d54

        instalar_workspace_relatorios_d23d54()
    except Exception:
        logging.getLogger(__name__).exception("D23D54: falha ao instalar workspace padrão de relatórios")


_instalar_adaptadores_financeiros_se_disponiveis()
