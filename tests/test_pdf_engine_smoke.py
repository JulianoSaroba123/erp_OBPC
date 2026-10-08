"""Regressão da geração de PDF dos relatórios financeiros."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pydyf
import weasyprint
from flask import Flask
from sqlalchemy import create_engine
from weasyprint import HTML

from app.financeiro import financeiro_routes


def test_postgresql_default_driver_continua_psycopg2():
    engine = create_engine("postgresql://user:pass@localhost/db")
    assert engine.dialect.driver == "psycopg2"


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


def test_relatorio_pdf_preserva_competencia_e_retorna_pdf_para_quatro_tipos():
    app = _app_teste()

    for tipo_relatorio in ("gerencial", "livro_caixa", "sede", "auditoria"):
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


def _config_reportlab_teste():
    return SimpleNamespace(
        cor_principal="#4A7C59",
        cor_secundaria="#2E86AB",
        cor_destaque="#D4A017",
        fonte_relatorio="Helvetica",
        logo=None,
        exibir_logo_relatorio=False,
        cidade="Tietê",
        bairro="Centro",
        presidente="Pastor Responsável",
        primeiro_tesoureiro="Tesoureiro(a)",
        campo_assinatura_1=None,
        campo_assinatura_2=None,
        rodape_relatorio=None,
        endereco_completo=lambda: "",
        percentual_conselho=30,
    )


def test_relatorio_caixa_rota_propria_08_2026_retorna_pdf():
    app = _app_teste()
    query = MagicMock()
    query.filter.return_value.order_by.return_value.all.return_value = []

    with app.test_request_context("/financeiro/relatorio-caixa/pdf?mes=8&ano=2026"):
        with patch.object(financeiro_routes.Lancamento, "query", query), \
             patch.object(
                 financeiro_routes.Lancamento,
                 "calcular_saldo_ate_mes_anterior",
                 return_value=832.24,
             ), \
             patch.object(
                 financeiro_routes.Configuracao,
                 "obter_configuracao",
                 return_value=_config_reportlab_teste(),
             ), \
             patch.object(
                 financeiro_routes,
                 "_montar_controle_repasse_sede",
                 return_value={},
             ), \
             patch.object(
                 financeiro_routes,
                 "_obter_observacao_repasse_sede",
                 return_value=("", "", False),
             ), \
             patch.object(
                 financeiro_routes,
                 "gerar_nome_arquivo_relatorio",
                 return_value="relatorio_caixa_08_2026.pdf",
             ):
            response = financeiro_routes.relatorio_caixa_pdf.__wrapped__()

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    response.direct_passthrough = False
    pdf = response.get_data()
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


if __name__ == "__main__":
    test_postgresql_default_driver_continua_psycopg2()
    test_weasyprint_write_pdf_smoke()
    test_relatorio_pdf_preserva_competencia_e_retorna_pdf_para_quatro_tipos()
    test_relatorio_caixa_rota_propria_08_2026_retorna_pdf()
    print("PDF_SMOKE_OK")
