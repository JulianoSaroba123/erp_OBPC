#!/usr/bin/env python3
"""
Teste final: Gerar PDF com logo diretamente
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER
from io import BytesIO

def gerar_pdf_teste_logo():
    """Gera um PDF de teste com logo"""
    print("🧪 TESTE FINAL: Gerar PDF com Logo")
    print("=" * 40)
    
    try:
        # Criar PDF
        print("1. Criando documento PDF...")
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=TA_CENTER
        )
        
        # Conteúdo
        story = []
        
        # Adicionar logo
        print("2. Adicionando logo...")
        logo_path = 'static/Logo_OBPC.jpg'
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=80, height=80)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 20))
            print(f"✅ Logo adicionado: {logo_path}")
        else:
            print("❌ Logo não encontrado")
            return False
        
        # Adicionar texto
        story.append(Paragraph("TESTE DE LOGO NO PDF", title_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph("Se você está vendo este PDF, o logo foi inserido com sucesso!", styles['Normal']))
        
        # Gerar PDF
        print("3. Gerando PDF...")
        doc.build(story)
        
        # Salvar arquivo
        pdf_data = buffer.getvalue()
        buffer.close()
        
        with open('teste_logo_pdf.pdf', 'wb') as f:
            f.write(pdf_data)
        
        print(f"✅ PDF gerado com sucesso!")
        print(f"📄 Tamanho: {len(pdf_data)} bytes")
        print("💾 Arquivo: teste_logo_pdf.pdf")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = gerar_pdf_teste_logo()
    
    print("\n" + "=" * 40)
    if sucesso:
        print("🎉 PDF COM LOGO GERADO COM SUCESSO!")
        print("📋 Abra 'teste_logo_pdf.pdf' para verificar")
    else:
        print("❌ FALHA NA GERAÇÃO DO PDF")
    print("=" * 40)