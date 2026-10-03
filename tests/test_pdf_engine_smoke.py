"""Smoke test do motor PDF usado pelos relatórios financeiros.

D26F-PDF: diagnostica incompatibilidades WeasyPrint/pydyf antes de
investigar templates e regras financeiras.
"""

import pydyf
import weasyprint
from weasyprint import HTML


def test_weasyprint_write_pdf_smoke():
    print(f"WeasyPrint={weasyprint.__version__}")
    print(f"pydyf={pydyf.__version__}")

    pdf = HTML(string="<h1>Teste PDF</h1>").write_pdf()

    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


if __name__ == "__main__":
    test_weasyprint_write_pdf_smoke()
    print("PDF_SMOKE_OK")
