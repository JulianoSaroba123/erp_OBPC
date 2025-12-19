#!/usr/bin/env python3
"""
Script para testar login e verificar rotas disponíveis
"""

from app import create_app
from flask import url_for

def verificar_rotas_admin():
    """Verifica as rotas disponíveis para admin"""
    print("🔍 VERIFICANDO ROTAS DISPONÍVEIS")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        # Listar todas as rotas
        print("📋 TODAS AS ROTAS REGISTRADAS:")
        
        rotas_por_modulo = {}
        
        for rule in app.url_map.iter_rules():
            endpoint = rule.endpoint
            modulo = endpoint.split('.')[0] if '.' in endpoint else 'main'
            
            if modulo not in rotas_por_modulo:
                rotas_por_modulo[modulo] = []
            
            rotas_por_modulo[modulo].append({
                'rota': str(rule),
                'endpoint': endpoint,
                'metodos': list(rule.methods - {'HEAD', 'OPTIONS'})
            })
        
        # Mostrar por módulo
        for modulo, rotas in rotas_por_modulo.items():
            print(f"\n📁 {modulo.upper()}:")
            for rota in rotas:
                metodos = ', '.join(rota['metodos'])
                print(f"  - {rota['rota']} [{metodos}] -> {rota['endpoint']}")
        
        # Verificar rotas específicas importantes
        print("\n🎯 ROTAS IMPORTANTES:")
        
        rotas_importantes = [
            'main.dashboard',
            'main.painel', 
            'secretaria.index',
            'departamentos.index',
            'midia.index',
            'midia.listar_certificados',
            'eventos.index',
            'financeiro.index'
        ]
        
        for rota in rotas_importantes:
            try:
                url = url_for(rota)
                print(f"  ✅ {rota} -> {url}")
            except:
                print(f"  ❌ {rota} -> NÃO ENCONTRADA")

if __name__ == "__main__":
    verificar_rotas_admin()