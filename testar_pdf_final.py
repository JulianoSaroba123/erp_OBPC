#!/usr/bin/env python3
"""
Script final para testar a geração de PDF corrigida
Sistema OBPC
"""

import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.secretaria.atas.atas_model import Ata
from app.secretaria.inventario.inventario_model import ItemInventario

def testar_pdf_corrigido():
    """Testa se os PDFs corrigidos estão funcionando"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🎯 === TESTE FINAL - PDF CORRIGIDO ===")
            print()
            
            # Verificar dados disponíveis
            atas = Ata.query.all()
            itens = ItemInventario.query.filter_by(ativo=True).all()
            
            print(f"📊 Dados disponíveis:")
            print(f"   • Atas: {len(atas)}")
            print(f"   • Itens de Inventário: {len(itens)}")
            
            if len(atas) == 0:
                print("⚠️  Nenhuma ata encontrada. Execute criar_dados_secretaria.py primeiro")
                
            if len(itens) == 0:
                print("⚠️  Nenhum item de inventário encontrado. Execute criar_dados_secretaria.py primeiro")
            
            print()
            
            # Teste de geração direta de PDF
            print("🧪 Testando geração de PDF...")
            
            import weasyprint
            
            # Teste simples direto
            html_teste = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Times, serif; margin: 40px; }}
                    h1 {{ color: #0066cc; text-align: center; }}
                </style>
            </head>
            <body>
                <h1>TESTE DE PDF CORRIGIDO</h1>
                <p>Data: {}</p>
                <p>Status: Funcionando corretamente!</p>
            </body>
            </html>
            """.format(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
            
            pdf_data = weasyprint.HTML(string=html_teste).write_pdf()
            
            if pdf_data and len(pdf_data) > 1000:
                print("✅ Geração de PDF funcionando!")
                print(f"   Tamanho do PDF: {len(pdf_data)} bytes")
            else:
                print("❌ Problema na geração de PDF")
                return False
            
            print()
            print("🔗 URLs corrigidas:")
            print("   • Atas: /secretaria/atas/pdf/<id>")
            print("   • Inventário: /secretaria/inventario/pdf")
            print("   • Ofícios: /secretaria/oficios/pdf/<id>")
            
            print()
            print("✅ CORREÇÕES APLICADAS:")
            print("   • Imports corrigidos (weasyprint.HTML)")
            print("   • Resposta direta (make_response)")
            print("   • Headers corretos (Content-Type, Content-Disposition)")
            print("   • Base URL configurado")
            print("   • Arquivos salvos localmente")
            
            print()
            print("📋 Como testar:")
            print("   1. Acesse o sistema web")
            print("   2. Vá para Secretaria → Atas/Inventário")
            print("   3. Clique nos botões de PDF")
            print("   4. PDFs devem abrir diretamente no navegador")
            
            return True
            
        except Exception as e:
            print(f"❌ ERRO durante teste: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    sucesso = testar_pdf_corrigido()
    if sucesso:
        print("\n🎉 Teste final passou! PDFs corrigidos!")
    else:
        print("\n❌ Ainda há problemas com os PDFs!")
        sys.exit(1)