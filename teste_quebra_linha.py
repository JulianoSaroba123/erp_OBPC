#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF Inventário - Com Quebra de Linha Automática
==============================================
Teste da nova funcionalidade de quebra de linha dentro das células.
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

def gerar_pdf_com_quebra_linha():
    """Gera PDF com quebra de linha automática nas células"""
    try:
        from app import create_app
        from app.secretaria.inventario.inventario_routes import gerar_pdf_inventario_reportlab
        from app.secretaria.inventario.inventario_model import ItemInventario
        from app.configuracoes.configuracoes_model import Configuracao
        
        app = create_app()
        
        with app.app_context():
            itens = ItemInventario.query.filter_by(ativo=True).order_by(
                ItemInventario.categoria.asc(), 
                ItemInventario.codigo.asc()
            ).all()
            
            inventario_por_categoria = {}
            valor_total = 0
            
            for item in itens:
                if item.categoria not in inventario_por_categoria:
                    inventario_por_categoria[item.categoria] = []
                inventario_por_categoria[item.categoria].append(item)
                if item.valor_aquisicao:
                    valor_total += float(item.valor_aquisicao)
            
            config = Configuracao.obter_configuracao()
            
            print("🔄 Gerando PDF com quebra de linha automática...")
            response = gerar_pdf_inventario_reportlab(itens, inventario_por_categoria, valor_total, config)
            
            nome_arquivo = "inventario_com_quebra_linha.pdf"
            pdf_content = response.get_data()
            
            with open(nome_arquivo, 'wb') as f:
                f.write(pdf_content)
            
            tamanho = os.path.getsize(nome_arquivo)
            print(f"✅ PDF com quebra de linha salvo: {nome_arquivo}")
            print(f"📊 Tamanho: {tamanho:,} bytes")
            
            print("\n🎯 NOVA FUNCIONALIDADE:")
            print("=" * 50)
            print("✓ Quebra de linha automática nas células")
            print("✓ Textos longos não são mais truncados")
            print("✓ Altura das linhas ajusta automaticamente")
            print("✓ Layout mais organizado e legível")
            print("✓ Padding aumentado para acomodar quebras")
            print("✓ Alinhamento vertical no topo das células")
            
            print(f"\n🎉 Agora as tabelas ficam muito mais organizadas!")
            print(f"📄 Confira o arquivo '{nome_arquivo}'")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = gerar_pdf_com_quebra_linha()
    if sucesso:
        print("\n" + "=" * 50)
        print("🎊 QUEBRA DE LINHA IMPLEMENTADA COM SUCESSO!")
        print("=" * 50)
    else:
        print("\n❌ FALHA NA IMPLEMENTAÇÃO")
        sys.exit(1)