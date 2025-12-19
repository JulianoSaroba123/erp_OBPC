#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF Inventário - Versão Otimizada Final
======================================
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

def gerar_pdf_otimizado():
    """Gera PDF otimizado final"""
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
            
            print("🔧 Gerando PDF otimizado...")
            response = gerar_pdf_inventario_reportlab(itens, inventario_por_categoria, valor_total, config)
            
            nome_arquivo = "inventario_layout_otimizado_v2.pdf"
            pdf_content = response.get_data()
            
            with open(nome_arquivo, 'wb') as f:
                f.write(pdf_content)
            
            tamanho = os.path.getsize(nome_arquivo)
            print(f"✅ PDF otimizado salvo: {nome_arquivo}")
            print(f"📊 Tamanho: {tamanho:,} bytes")
            
            print("\n🎯 OTIMIZAÇÕES APLICADAS:")
            print("• Larguras: Código(1.5cm), Nome(4cm), Descrição(5cm)")
            print("• Valores(2.5cm), Estado(2cm), Responsável(2cm)")
            print("• Altura mínima das linhas: 20pt")
            print("• Alinhamento vertical: TOP (melhor para textos)")
            print("• Padding aumentado para melhor espaçamento")
            print("• Truncamento inteligente com mais caracteres")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

if __name__ == "__main__":
    gerar_pdf_otimizado()