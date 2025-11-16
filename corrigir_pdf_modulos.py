#!/usr/bin/env python3
"""
Script para corrigir problemas de PDF nos módulos Atas e Inventário
Sistema OBPC
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def corrigir_pdf_atas():
    """Corrige problemas no módulo de atas"""
    print("🔧 Corrigindo módulo de Atas...")
    
    # Leia o arquivo atual
    atas_file = 'app/secretaria/atas/atas_routes.py'
    
    with open(atas_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substitui a implementação por uma mais robusta
    new_pdf_function = '''@atas_bp.route('/secretaria/atas/pdf/<int:id>')
@login_required
def gerar_pdf_ata(id):
    """Gera PDF da ata"""
    try:
        ata = Ata.query.get_or_404(id)
        
        # Lê as configurações da igreja (se disponível)
        try:
            from app.configuracoes.configuracoes_model import Configuracao
            config_obj = Configuracao.query.first()
        except:
            config_obj = None
        
        # Configurações da igreja (com fallback se não houver configuração)
        config = {
            'nome_igreja': config_obj.nome if config_obj else 'ORGANIZAÇÃO BATISTA PEDRA DE CRISTO',
            'endereco': config_obj.endereco if config_obj else 'Rua das Flores, 123',
            'cidade': 'Tietê - SP',
            'cnpj': config_obj.cnpj if config_obj else '12.345.678/0001-99',
            'dirigente': 'Pastor João Silva',
            'tesoureiro': 'Maria Santos'
        }
        
        # Renderizar template HTML
        html_content = render_template('atas/pdf_ata.html', ata=ata, config=config)
        
        # Configura o WeasyPrint
        base_url = request.url_root
        
        # Gerar PDF
        pdf = weasyprint.HTML(string=html_content, base_url=base_url).write_pdf()
        
        # Define nome do arquivo
        filename = f"ata_{ata.id}_{ata.data.strftime('%Y%m%d')}.pdf"
        filepath = os.path.join('app', 'static', 'atas', filename)
        
        # Salva o arquivo
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(pdf)
        
        # Atualizar caminho do arquivo na ata
        ata.arquivo = f'static/atas/{filename}'
        db.session.commit()
        
        # Retorna o PDF para download
        from flask import make_response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        
        return response
        
    except Exception as e:
        flash(f'Erro ao gerar PDF: {str(e)}', 'danger')
        return redirect(url_for('atas.lista_atas'))'''
    
    # Substituir a função existente
    import re
    pattern = r'@atas_bp\.route\(\'/secretaria/atas/pdf/<int:id>\'\).*?return redirect\(url_for\(\'atas\.lista_atas\'\)\)'
    content = re.sub(pattern, new_pdf_function, content, flags=re.DOTALL)
    
    # Adicionar import necessário se não estiver
    if 'from flask import make_response' not in content:
        content = content.replace(
            'from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app',
            'from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, make_response'
        )
    
    # Salvar arquivo corrigido
    with open(atas_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("   ✅ Módulo de Atas corrigido!")

def corrigir_pdf_inventario():
    """Corrige problemas no módulo de inventário"""
    print("🔧 Corrigindo módulo de Inventário...")
    
    # Leia o arquivo atual
    inventario_file = 'app/secretaria/inventario/inventario_routes.py'
    
    with open(inventario_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substitui a implementação por uma mais robusta
    new_pdf_function = '''@inventario_bp.route('/secretaria/inventario/pdf')
@login_required
def gerar_pdf_inventario():
    """Gera PDF do inventário completo"""
    try:
        # Buscar apenas itens ativos
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
        
        # Lê as configurações da igreja (se disponível)
        try:
            from app.configuracoes.configuracoes_model import Configuracao
            config_obj = Configuracao.query.first()
        except:
            config_obj = None
        
        # Configurações da igreja (com fallback)
        config = {
            'nome_igreja': config_obj.nome if config_obj else 'ORGANIZAÇÃO BATISTA PEDRA DE CRISTO',
            'endereco': config_obj.endereco if config_obj else 'Rua das Flores, 123',
            'cidade': 'Tietê - SP',
            'cnpj': config_obj.cnpj if config_obj else '12.345.678/0001-99',
            'dirigente': 'Pastor João Silva',
            'tesoureiro': 'Maria Santos'
        }
        
        # Renderizar template HTML
        html_content = render_template('inventario/pdf_inventario.html', 
                                     inventario_por_categoria=inventario_por_categoria,
                                     valor_total=valor_total,
                                     total_itens=len(itens),
                                     config=config)
        
        # Configura o WeasyPrint
        base_url = request.url_root
        
        # Gerar PDF
        pdf = weasyprint.HTML(string=html_content, base_url=base_url).write_pdf()
        
        # Define nome do arquivo
        filename = f"inventario_patrimonial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join('app', 'static', 'inventario', filename)
        
        # Salva o arquivo
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(pdf)
        
        # Retorna o PDF para download
        from flask import make_response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        
        return response
        
    except Exception as e:
        flash(f'Erro ao gerar PDF: {str(e)}', 'danger')
        return redirect(url_for('inventario.lista_itens'))'''
    
    # Substituir a função existente
    import re
    pattern = r'@inventario_bp\.route\(\'/secretaria/inventario/pdf\'\).*?return redirect\(url_for\(\'inventario\.lista_itens\'\)\)'
    content = re.sub(pattern, new_pdf_function, content, flags=re.DOTALL)
    
    # Adicionar import necessário se não estiver
    if 'from flask import make_response' not in content:
        content = content.replace(
            'from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app',
            'from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, make_response'
        )
    
    # Salvar arquivo corrigido
    with open(inventario_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("   ✅ Módulo de Inventário corrigido!")

def main():
    print("🔧 === CORRIGINDO PROBLEMAS DE PDF ===")
    print()
    
    try:
        corrigir_pdf_atas()
        corrigir_pdf_inventario()
        
        print()
        print("🎉 CORREÇÕES APLICADAS COM SUCESSO!")
        print("   • Ambos os módulos agora usam o mesmo padrão do módulo Ofícios")
        print("   • PDFs são retornados diretamente no navegador")
        print("   • Arquivos salvos localmente para backup")
        print("   • Configurações da igreja integradas")
        print()
        print("📝 Para testar:")
        print("   1. Reinicie o servidor Flask")
        print("   2. Acesse Secretaria → Atas/Inventário")
        print("   3. Clique nos botões de PDF")
        
    except Exception as e:
        print(f"❌ ERRO durante correção: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    sucesso = main()
    if sucesso:
        print("\n✨ Correção concluída com sucesso!")
    else:
        print("\n❌ Correção falhou!")
        sys.exit(1)