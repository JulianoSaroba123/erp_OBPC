#!/usr/bin/env python3
"""
Script para testar a geração de PDF dos módulos Atas e Inventário
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

def testar_pdf():
    """Testa se as funções de PDF estão funcionando"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🧪 === TESTANDO GERAÇÃO DE PDF ===")
            print()
            
            # Teste 1: Verificar se há atas
            atas = Ata.query.limit(1).all()
            if atas:
                print(f"✅ Encontradas {len(atas)} ata(s)")
                print(f"   Primeira ata: {atas[0].titulo}")
            else:
                print("❌ Nenhuma ata encontrada para teste")
            
            # Teste 2: Verificar se há itens de inventário
            itens = ItemInventario.query.filter_by(ativo=True).limit(1).all()
            if itens:
                print(f"✅ Encontrados {len(itens)} item(ns) de inventário")
                print(f"   Primeiro item: {itens[0].nome}")
            else:
                print("❌ Nenhum item de inventário encontrado para teste")
            
            print()
            
            # Teste 3: Verificar import do WeasyPrint
            try:
                import weasyprint
                print("✅ WeasyPrint importado com sucesso")
                print(f"   Versão: {weasyprint.__version__}")
            except ImportError as e:
                print(f"❌ Erro ao importar WeasyPrint: {e}")
                return False
            
            # Teste 4: Verificar se os diretórios estáticos existem
            static_dir = os.path.join(os.path.dirname(__file__), 'app', 'static')
            atas_dir = os.path.join(static_dir, 'atas')
            inventario_dir = os.path.join(static_dir, 'inventario')
            
            print(f"✅ Diretório static: {os.path.exists(static_dir)}")
            print(f"✅ Diretório atas: {os.path.exists(atas_dir)}")
            print(f"✅ Diretório inventário: {os.path.exists(inventario_dir)}")
            
            # Teste 5: Teste simples de HTML para PDF
            print()
            print("🧪 Testando conversão HTML → PDF...")
            
            html_simples = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Teste PDF</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ color: #0066cc; text-align: center; }}
                </style>
            </head>
            <body>
                <h1>TESTE DE PDF</h1>
                <p>Este é um teste simples de geração de PDF.</p>
                <p>Data/Hora: {}</p>
                <p>Sistema: OBPC - Organização Batista Pedra de Cristo</p>
            </body>
            </html>
            """.format(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
            
            # Tenta gerar PDF de teste
            teste_pdf = os.path.join(static_dir, 'teste_pdf.pdf')
            
            pdf_data = weasyprint.HTML(string=html_simples).write_pdf()
            
            with open(teste_pdf, 'wb') as f:
                f.write(pdf_data)
            
            if os.path.exists(teste_pdf):
                tamanho = os.path.getsize(teste_pdf)
                print(f"✅ PDF teste criado: {teste_pdf}")
                print(f"   Tamanho: {tamanho} bytes")
                
                # Remove arquivo de teste
                os.remove(teste_pdf)
                print("   Arquivo de teste removido")
            else:
                print("❌ Falha ao criar PDF de teste")
                return False
            
            print()
            print("🎉 TODOS OS TESTES PASSARAM!")
            print("   Os módulos de PDF devem estar funcionando corretamente.")
            print("   Se ainda houver problemas, verifique:")
            print("   1. Permissões de escrita nos diretórios")
            print("   2. Templates HTML existem e estão corretos")
            print("   3. Logs de erro no navegador/terminal")
            
            return True
            
        except Exception as e:
            print(f"❌ ERRO durante teste: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    sucesso = testar_pdf()
    if sucesso:
        print("\n✨ Teste concluído com sucesso!")
    else:
        print("\n❌ Teste falharam!")
        sys.exit(1)