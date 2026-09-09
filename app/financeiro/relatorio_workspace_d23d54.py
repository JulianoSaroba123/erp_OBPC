from __future__ import annotations


WORKSPACE_TEMPLATE = "financeiro/relatorio_workspace.html"
REPORT_TEMPLATES = {
    "financeiro/relatorio_gerencial.html",
    "financeiro/relatorio_sede.html",
    "financeiro/relatorio_auditoria.html",
}


def instalar_workspace_relatorios_d23d54() -> bool:
    """Aplica o shell padrão do ERP apenas às telas web dos relatórios.

    PDF continua sendo renderizado pelos templates oficiais existentes com
    ``modo_pdf=True``. Não altera contexto financeiro, persistência ou regras.
    """
    import app.financeiro.financeiro_routes as routes

    atual = routes.render_template
    if getattr(atual, "_d23d54_relatorios_workspace", False):
        return False

    render_template_original = atual

    def render_template_d23d54(template_name, *args, **contexto):
        if template_name in REPORT_TEMPLATES and not contexto.get("modo_pdf", False):
            contexto = dict(contexto)
            contexto["report_template_original"] = template_name
            return render_template_original(WORKSPACE_TEMPLATE, *args, **contexto)
        return render_template_original(template_name, *args, **contexto)

    render_template_d23d54._d23d54_relatorios_workspace = True
    render_template_d23d54._d23d54_original = render_template_original
    routes.render_template = render_template_d23d54
    return True
