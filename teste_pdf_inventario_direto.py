#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste Direto do PDF do Inventário
===============================
Este script testa a geração de PDF do inventário diretamente,
sem precisar do servidor Flask rodando.
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

def teste_pdf_direto():
    """Testa a geração de PDF do inventário diretamente"""
    print("🧪 TESTE DIRETO: PDF do Inventário")
    print("=" * 50)
    
    try:
        # 1. Importar módulos necessários
        print("1. Importando módulos...")
        from app import create_app
        from app.secretaria.inventario.inventario_routes import gerar_pdf_inventario_reportlab
        from app.secretaria.inventario.inventario_model import ItemInventario
        print("✅ Módulos importados com sucesso")
        
        # 2. Criar aplicação Flask
        print("\n2. Criando aplicação Flask...")
        app = create_app()
        print("✅ Aplicação criada com sucesso")
        
        # 3. Testar função de PDF diretamente
        print("\n3. Testando função de PDF...")
        with app.app_context():
            # Buscar itens do inventário
            itens = ItemInventario.query.filter_by(ativo=True).order_by(
                ItemInventario.categoria.asc(), 
                ItemInventario.codigo.asc()
            ).all()
            print(f"📦 Encontrados {len(itens)} itens no inventário")
            
            if len(itens) == 0:
                print("⚠️  Nenhum item encontrado. Criando item de teste...")
                from app.extensoes import db
                
                # Criar item de teste
                item_teste = ItemInventario(
                    nome="Item de Teste",
                    categoria="Teste",
                    quantidade=1,
                    valor_aquisicao=100.0,
                    localizacao="Sala de Teste",
                    observacoes="Criado para teste de PDF",
                    ativo=True
                )
                db.session.add(item_teste)
                db.session.commit()
                print("✅ Item de teste criado")
                
                # Buscar novamente
                itens = ItemInventario.query.filter_by(ativo=True).all()
                print(f"📦 Agora temos {len(itens)} itens")
            
            # Agrupar por categoria
            inventario_por_categoria = {}
            valor_total = 0
            
            for item in itens:
                if item.categoria not in inventario_por_categoria:
                    inventario_por_categoria[item.categoria] = []
                inventario_por_categoria[item.categoria].append(item)
                if item.valor_aquisicao:
                    valor_total += float(item.valor_aquisicao)
            
            print(f"📊 Categorias encontradas: {list(inventario_por_categoria.keys())}")
            print(f"💰 Valor total: R$ {valor_total:,.2f}")
            
            # Obter configurações da igreja
            from app.configuracoes.configuracoes_model import Configuracao
            config = Configuracao.obter_configuracao()
            print("⚙️  Configurações obtidas")
            
            # Gerar PDF
            print("\n4. Gerando PDF...")
            response = gerar_pdf_inventario_reportlab(itens, inventario_por_categoria, valor_total, config)
            
            if response:
                # Extrair dados do PDF da response
                pdf_content = response.get_data()
                
                # Salvar PDF para teste
                nome_arquivo = "teste_inventario_direto.pdf"
                with open(nome_arquivo, 'wb') as f:
                    f.write(pdf_content)
                
                # Verificar tamanho do arquivo
                tamanho = os.path.getsize(nome_arquivo)
                print(f"✅ PDF gerado com sucesso!")
                print(f"📄 Arquivo: {nome_arquivo}")
                print(f"📊 Tamanho: {tamanho:,} bytes")
                
                # Verificar se tem conteúdo válido
                if tamanho > 1000:  # PDFs válidos geralmente têm mais de 1KB
                    print("✅ PDF parece ter conteúdo válido")
                    print("\n" + "=" * 50)
                    print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
                    print("=" * 50)
                    return True
                else:
                    print("⚠️  PDF muito pequeno, pode estar vazio")
                    return False
            else:
                print("❌ Falha na geração do PDF")
                return False
                
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = teste_pdf_direto()
    if not sucesso:
        print("\n" + "=" * 50)
        print("❌ TESTE FALHOU")
        print("=" * 50)
        sys.exit(1)