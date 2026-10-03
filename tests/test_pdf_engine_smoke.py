"""Regressão da geração de PDF dos relatórios financeiros."""

from unittest.mock import patch

import pydyf
import weasyprint
from flask import Flask
from weasyprint import HTML

from app.financeiro import financeiro_routes


def test_weasyprint_write_pdf_smoke():
    print(f"WeasyPrint={weasyprint.__version__}")
    print(f"pydyf={pydyf.__version__}")

    pdf = HTML(string="<h1>Teste PDF</h1>").write_pdf()

    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


def _app_teste():
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="pdf-test")
    app.register_blueprint(financeiro_routes.financeiro_bp)
    return app


def test_relatorio_pdf_preserva_competencia_e_retorna_pdf_para_tres_tipos():
    app = _app_teste()

    for tipo_relatorio in ("gerencial", "sede", "auditoria"):
        contexto = {
            "tipo_relatorio": tipo_relatorio,
            "mes": 8,
            "ano": 2026,
            "template_relatorio": f"financeiro/relatorio_{tipo_relatorio}.html",
            "dados_igreja": {"logo": ""},
        }

        with app.test_request_context(
            f"/financeiro/relatorio/pdf?tipo_relatorio={tipo_relatorio}&mes=8&ano=2026"
        ):
            with patch.object(
                financeiro_routes,
                "gerar_dados_relatorio",
                return_value=contexto,
            ) as gerar_dados, patch.object(
                financeiro_routes,
                "render_template",
                return_value="<h1>Relatório 08/2026</h1>",
            ), patch.object(
                financeiro_routes,
                "gerar_nome_arquivo_relatorio",
                return_value=f"relatorio_{tipo_relatorio}_08_2026.pdf",
            ):
                response = financeiro_routes.relatorio_pdf.__wrapped__()

        assert response.status_code == 200
        assert response.mimetype == "application/pdf"
        response.direct_passthrough = False
        pdf = response.get_data()
        assert pdf.startswith(b"%PDF")
        assert len(pdf) > 1000
        gerar_dados.assert_called_once_with(
            tipo_relatorio=tipo_relatorio,
            mes=8,
            ano=2026,
        )


if __name__ == "__main__":
    test_weasyprint_write_pdf_smoke()
    test_relatorio_pdf_preserva_competencia_e_retorna_pdf_para_tres_tipos()
    print("PDF_SMOKE_OK")
