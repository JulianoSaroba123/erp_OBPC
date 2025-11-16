#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste Final do PDF do Inventário com Tabelas Corrigidas
======================================================
Este script gera um PDF final do inventário com as tabelas corrigidas.
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

def gerar_pdf_final():
    """Gera PDF final do inventário com tabelas corrigidas"""
    print("🎯 GERAÇÃO FINAL: PDF do Inventário com Tabelas Corrigidas")
    print("=" * 65)
    
    try:
        # Importar módulos
        print("📋 Preparando módulos...")
        from app import create_app
        from app.secretaria.inventario.inventario_routes import gerar_pdf_inventario_reportlab
        from app.secretaria.inventario.inventario_model import ItemInventario
        from app.configuracoes.configuracoes_model import Configuracao
        
        # Criar aplicação
        app = create_app()
        
        with app.app_context():
            # Buscar dados
            print("📊 Coletando dados do inventário...")
            itens = ItemInventario.query.filter_by(ativo=True).order_by(
                ItemInventario.categoria.asc(), 
                ItemInventario.codigo.asc()
            ).all()
            
            # Agrupar por categoria
            inventario_por_categoria = {}
            valor_total = 0
            
            for item in itens:
                if item.categoria not in inventario_por_categoria:
                    inventario_por_categoria[item.categoria] = []
                inventario_por_categoria[item.categoria].append(item)
                if item.valor_aquisicao:
                    valor_total += float(item.valor_aquisicao)
            
            # Obter configurações
            config = Configuracao.obter_configuracao()
            
            print(f"✅ {len(itens)} itens encontrados em {len(inventario_por_categoria)} categorias")
            print(f"💰 Valor total: R$ {valor_total:,.2f}")
            
            # Gerar PDF
            print("\n🔧 Gerando PDF com tabelas corrigidas...")
            response = gerar_pdf_inventario_reportlab(itens, inventario_por_categoria, valor_total, config)
            
            # Salvar arquivo
            nome_arquivo = "inventario_tabelas_corrigidas.pdf"
            pdf_content = response.get_data()
            
            with open(nome_arquivo, 'wb') as f:
                f.write(pdf_content)
            
            tamanho = os.path.getsize(nome_arquivo)
            print(f"✅ PDF salvo: {nome_arquivo}")
            print(f"📊 Tamanho: {tamanho:,} bytes")
            
            # Resumo das melhorias
            print("\n🎨 MELHORIAS IMPLEMENTADAS:")
            print("=" * 40)
            print("✓ Larguras de colunas otimizadas para A4")
            print("✓ Cabeçalho com fundo azul e texto escuro")
            print("✓ Alinhamento inteligente (código centralizado, valor à direita)")
            print("✓ Truncamento de textos longos para evitar quebras")
            print("✓ Linhas alternadas (branco/cinza) para melhor leitura")
            print("✓ Bordas e padding melhorados")
            print("✓ Fontes e tamanhos otimizados")
            
            print(f"\n🎉 PDF do inventário gerado com sucesso!")
            print(f"📄 Abra o arquivo '{nome_arquivo}' para ver as tabelas corrigidas")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = gerar_pdf_final()
    if sucesso:
        print("\n" + "=" * 65)
        print("🎊 CONCLUÍDO COM SUCESSO!")
        print("=" * 65)
    else:
        print("\n❌ FALHA NA GERAÇÃO")
        sys.exit(1)