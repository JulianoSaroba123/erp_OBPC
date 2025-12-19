#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests

def demonstrar_templates():
    """Demonstra as URLs dos templates disponíveis"""
    base_url = "http://127.0.0.1:5000"
    
    print("=" * 60)
    print("🎨 NOVO SISTEMA DE CERTIFICADOS IMPLEMENTADO")
    print("=" * 60)
    
    print("\n📋 FUNCIONALIDADES:")
    print("✅ Template MINIMALISTA para Apresentação (azul/rosa)")
    print("✅ Template AZUL TRADICIONAL para Batismo")
    print("✅ Logo MUITO MAIOR em ambos os templates")
    print("✅ Suporte a padrinhos no template de apresentação")
    print("✅ Design responsivo e profissional")
    
    print("\n🎯 CARACTERÍSTICAS DO TEMPLATE MINIMALISTA:")
    print("• Cores: Azul (#4A90E2) e Rosa (#E91E63)")
    print("• Logo: 120px de altura (bem maior)")
    print("• Nome da criança: Gradiente azul/rosa")
    print("• Padrinhos: Box destacado em rosa claro")
    print("• Versículo: Mateus 19:14 sobre crianças")
    print("• Layout: Minimalista e moderno")
    
    print("\n📱 COMO TESTAR:")
    print(f"1. Acesse: {base_url}/midia/certificados/novo")
    print("2. Crie um certificado de 'Apresentação'")
    print("3. Preencha o campo 'Padrinhos' (opcional)")
    print("4. Salve e volte à lista")
    print("5. Use o botão 'Visualizar' (👁️) para ver o template minimalista")
    print("6. Use o botão 'PDF' (📄) para gerar o arquivo")
    
    print("\n🔄 DIFERENÇAS POR TIPO:")
    print("• APRESENTAÇÃO → Template minimalista (azul/rosa)")
    print("• BATISMO → Template azul tradicional")
    print("• Ambos têm logo grande e layout profissional")
    
    print("\n🌐 URLS DIRETAS:")
    print(f"Lista: {base_url}/midia/certificados")
    print(f"Novo: {base_url}/midia/certificados/novo")
    
    print("\n💡 DICA:")
    print("Crie certificados dos dois tipos para ver a diferença!")
    print("O template minimalista foi baseado no modelo que você anexou.")
    
    print("\n" + "=" * 60)
    print("🎉 SISTEMA PRONTO PARA USO!")
    print("=" * 60)

if __name__ == "__main__":
    demonstrar_templates()