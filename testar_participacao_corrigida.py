#!/usr/bin/env python3
"""
Teste do módulo Participação de Obreiros após correções
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from flask import url_for

def testar_participacao():
    """Testa se o módulo de participação está funcionando"""
    
    print("=== TESTE MÓDULO PARTICIPAÇÃO CORRIGIDO ===")
    print()
    
    # Criar app
    app = create_app()
    
    with app.app_context():
        try:
            print("✅ BLUEPRINT REGISTRADO")
            print(f"   Blueprints: {list(app.blueprints.keys())}")
            
            # Verificar se participacao está registrado
            if 'participacao' in app.blueprints:
                print("✅ Blueprint 'participacao' encontrado!")
                bp = app.blueprints['participacao']
                print(f"   URL Prefix: {bp.url_prefix}")
                print(f"   Template Folder: {bp.template_folder}")
            else:
                print("❌ Blueprint 'participacao' NÃO encontrado!")
                return
            
            print()
            print("✅ ROTAS DISPONÍVEIS:")
            for rule in app.url_map.iter_rules():
                if 'participacao' in rule.endpoint:
                    print(f"   {rule.methods} {rule.rule} -> {rule.endpoint}")
            
            print()
            print("✅ URLS GERADAS:")
            try:
                print(f"   Lista: {url_for('participacao.listar_participacoes')}")
                print(f"   Nova: {url_for('participacao.nova_participacao')}")
                print(f"   PDF: {url_for('participacao.gerar_relatorio')}")
            except Exception as e:
                print(f"❌ Erro ao gerar URLs: {e}")
            
            print()
            print("✅ TEMPLATES:")
            # Verificar se templates existem
            templates = [
                'participacao/lista_participacao.html',
                'participacao/cadastro_participacao.html', 
                'participacao/relatorio_participacao.html'
            ]
            
            for template in templates:
                template_path = os.path.join('app/secretaria/participacao/templates', template)
                if os.path.exists(template_path):
                    print(f"   ✅ {template}")
                else:
                    print(f"   ❌ {template} - NÃO ENCONTRADO")
            
            print()
            print("🎉 TESTE CONCLUÍDO!")
            print("   Acesse: http://127.0.0.1:5000/secretaria/participacao")
            
        except Exception as e:
            print(f"❌ ERRO NO TESTE: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    testar_participacao()