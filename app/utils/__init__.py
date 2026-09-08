"""
Utilitários do Sistema Administrativo OBPC.

D23D49 mantém o gerador ReportLab legado para Caixa/Recibos e substitui apenas
apresentação do PDF oficial da Sede por um adaptador read-only.
"""

from .gerar_pdf_reportlab import gerar_pdf_relatorio_caixa, gerar_pdf_relatorio_sede, gerar_nome_arquivo_relatorio
from .relatorio_sede_oficial import instalar_relatorio_sede_oficial

instalar_relatorio_sede_oficial()

__all__ = ['gerar_pdf_relatorio_caixa', 'gerar_pdf_relatorio_sede', 'gerar_nome_arquivo_relatorio']
