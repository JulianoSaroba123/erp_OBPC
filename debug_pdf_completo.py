#!/usr/bin/env python3
"""
Script para debugar erros específicos na geração de PDF
Sistema OBPC - Captura erros detalhados
"""

import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.secretaria.atas.atas_model import Ata
from app.secretaria.inventario.inventario_model import ItemInventario
from app.secretaria.oficios.oficios_model import Oficio

def debug_pdf_atas():
    """Debug específico para PDFs de Atas"""
    print("🔍 === DEBUG PDF ATAS ===")
    try:
        from flask import render_template
        import weasyprint
        
        ata = Ata.query.first()
        if not ata:
            print("❌ Nenhuma ata encontrada")
            return False
            
        print(f"📄 Testando ata: {ata.titulo}")
        
        # Configurações
        config = {
            'nome_igreja': 'ORGANIZAÇÃO BATISTA PEDRA DE CRISTO',
            'endereco': 'Rua das Flores, 123',
            'cidade': 'Tietê - SP',
            'cnpj': '12.345.678/0001-99',
            'dirigente': 'Pastor João Silva',
            'tesoureiro': 'Maria Santos'
        }
        
        print("📋 Renderizando template atas...")
        html_content = render_template('atas/pdf_ata.html', ata=ata, config=config)
        print(f"   ✅ Template renderizado: {len(html_content)} chars")
        
        print("🔄 Gerando PDF...")
        pdf = weasyprint.HTML(string=html_content).write_pdf()
        print(f"   ✅ PDF gerado: {len(pdf)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO em Atas: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def debug_pdf_inventario():
    """Debug específico para PDFs de Inventário"""
    print("\n🔍 === DEBUG PDF INVENTÁRIO ===")
    try:
        from flask import render_template
        import weasyprint
        
        itens = ItemInventario.query.filter_by(ativo=True).all()
        if not itens:
            print("❌ Nenhum item de inventário encontrado")
            return False
            
        print(f"📦 Testando inventário: {len(itens)} itens")
        
        # Agrupar por categoria
        inventario_por_categoria = {}
        valor_total = 0
        
        for item in itens:
            if item.categoria not in inventario_por_categoria:
                inventario_por_categoria[item.categoria] = []
            inventario_por_categoria[item.categoria].append(item)
            if item.valor_aquisicao:
                valor_total += float(item.valor_aquisicao)
        
        config = {
            'nome_igreja': 'ORGANIZAÇÃO BATISTA PEDRA DE CRISTO',
            'endereco': 'Rua das Flores, 123',
            'cidade': 'Tietê - SP',
            'cnpj': '12.345.678/0001-99',
            'dirigente': 'Pastor João Silva',
            'tesoureiro': 'Maria Santos'
        }
        
        print("📋 Renderizando template inventário...")
        html_content = render_template('inventario/pdf_inventario.html', 
                                     inventario_por_categoria=inventario_por_categoria,
                                     valor_total=valor_total,
                                     total_itens=len(itens),
                                     config=config)
        print(f"   ✅ Template renderizado: {len(html_content)} chars")
        
        print("🔄 Gerando PDF...")
        pdf = weasyprint.HTML(string=html_content).write_pdf()
        print(f"   ✅ PDF gerado: {len(pdf)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO em Inventário: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def debug_pdf_oficios():
    """Debug específico para PDFs de Ofícios"""
    print("\n🔍 === DEBUG PDF OFÍCIOS ===")
    try:
        from flask import render_template
        import weasyprint
        
        oficio = Oficio.query.first()
        if not oficio:
            print("❌ Nenhum ofício encontrado")
            return False
            
        print(f"📄 Testando ofício: {oficio.numero}")
        
        dados_igreja = {
            'nome': 'ORGANIZAÇÃO BATISTA PEDRA DE CRISTO',
            'endereco': 'Rua das Flores, 123 - Tietê - SP',
            'cnpj': '12.345.678/0001-99',
            'telefone': '(15) 3285-1234',
            'email': 'contato@obpctcp.org.br'
        }
        
        print("📋 Renderizando template ofícios...")
        html_content = render_template('oficios/pdf_oficio.html', 
                                     oficio=oficio,
                                     dados_igreja=dados_igreja,
                                     data_geracao=datetime.now().strftime('%d/%m/%Y'))
        print(f"   ✅ Template renderizado: {len(html_content)} chars")
        
        print("🔄 Gerando PDF...")
        pdf = weasyprint.HTML(string=html_content).write_pdf()
        print(f"   ✅ PDF gerado: {len(pdf)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO em Ofícios: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verificar_permissoes():
    """Verifica permissões de escrita"""
    print("\n🔒 === VERIFICANDO PERMISSÕES ===")
    
    diretorios = [
        'app/static/atas',
        'app/static/inventario', 
        'app/static/oficios'
    ]
    
    for dir_path in diretorios:
        try:
            # Tenta criar um arquivo de teste
            test_file = os.path.join(dir_path, 'teste_permissao.txt')
            with open(test_file, 'w') as f:
                f.write('teste')
            
            # Remove o arquivo
            os.remove(test_file)
            print(f"   ✅ {dir_path}: Permissão OK")
            
        except Exception as e:
            print(f"   ❌ {dir_path}: Erro de permissão - {e}")
            return False
    
    return True

def verificar_templates():
    """Verifica se os templates existem e são válidos"""
    print("\n📋 === VERIFICANDO TEMPLATES ===")
    
    templates = [
        'app/secretaria/atas/templates/atas/pdf_ata.html',
        'app/secretaria/inventario/templates/inventario/pdf_inventario.html',
        'app/secretaria/oficios/templates/oficios/pdf_oficio.html'
    ]
    
    for template_path in templates:
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"   ✅ {os.path.basename(template_path)}: {len(content)} chars")
            
            # Verifica se tem sintaxe básica HTML
            if '<html' in content and '</html>' in content:
                print(f"      ✅ HTML válido")
            else:
                print(f"      ⚠️  HTML pode estar malformado")
        else:
            print(f"   ❌ {template_path}: Não encontrado")
            return False
    
    return True

def main():
    """Função principal de debug"""
    app = create_app()
    
    with app.app_context():
        print("🐛 === DEBUG COMPLETO - PDFs ===")
        print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print()
        
        # Verificações básicas
        templates_ok = verificar_templates()
        permissoes_ok = verificar_permissoes()
        
        if not templates_ok or not permissoes_ok:
            print("\n❌ Problemas básicos encontrados!")
            return False
        
        # Testes específicos
        atas_ok = debug_pdf_atas()
        inventario_ok = debug_pdf_inventario()
        oficios_ok = debug_pdf_oficios()
        
        print(f"\n📊 === RESULTADO FINAL ===")
        print(f"   📄 Atas: {'✅ OK' if atas_ok else '❌ ERRO'}")
        print(f"   📦 Inventário: {'✅ OK' if inventario_ok else '❌ ERRO'}")
        print(f"   📄 Ofícios: {'✅ OK' if oficios_ok else '❌ ERRO'}")
        
        if atas_ok and inventario_ok and oficios_ok:
            print("\n🎉 TODOS OS MÓDULOS ESTÃO FUNCIONANDO!")
            print("   O problema pode ser:")
            print("   1. Erro no navegador (console F12)")
            print("   2. Problema de sessão/login")
            print("   3. Configuração do servidor")
        else:
            print("\n❌ PROBLEMAS ENCONTRADOS!")
            print("   Verifique os erros acima para correção")
        
        return atas_ok and inventario_ok and oficios_ok

if __name__ == "__main__":
    sucesso = main()
    if not sucesso:
        sys.exit(1)