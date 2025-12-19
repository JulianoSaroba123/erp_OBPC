#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Conversor de Logo OBPC para Ícone
Converte a logo da igreja para formato .ico para usar no executável
"""

import os
from PIL import Image

def criar_icone_obpc():
    """Converte a logo existente para formato .ico"""
    
    # Procurar pela logo existente
    logo_paths = [
        'static/Logo_IBPC.jpg',
        'static/logo_obpc_novo.jpg', 
        'static/images.jpg'
    ]
    
    logo_encontrada = None
    for path in logo_paths:
        if os.path.exists(path):
            logo_encontrada = path
            break
    
    if not logo_encontrada:
        print("❌ Logo não encontrada!")
        print("Procurei em:")
        for path in logo_paths:
            print(f"   - {path}")
        return False
    
    try:
        print(f"📸 Carregando logo de: {logo_encontrada}")
        
        # Carregar imagem original
        with Image.open(logo_encontrada) as img:
            # Converter para RGBA se necessário
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Redimensionar para múltiplos tamanhos (formato ICO padrão)
            tamanhos = [16, 32, 48, 64, 128, 256]
            icones = []
            
            for tamanho in tamanhos:
                # Redimensionar mantendo proporção
                img_resized = img.resize((tamanho, tamanho), Image.Resampling.LANCZOS)
                icones.append(img_resized)
            
            # Salvar como .ico
            output_path = 'static/logo_obpc.ico'
            icones[0].save(
                output_path,
                format='ICO',
                sizes=[(t, t) for t in tamanhos]
            )
            
            print(f"✅ Ícone criado com sucesso: {output_path}")
            print(f"📏 Tamanhos incluídos: {', '.join(f'{t}x{t}' for t in tamanhos)}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao converter logo: {str(e)}")
        return False

def main():
    """Função principal"""
    print("==========================================")
    print("  CONVERSOR DE LOGO OBPC PARA ÍCONE")
    print("  Igreja O Brasil para Cristo - Tietê/SP")
    print("==========================================")
    print()
    
    # Verificar se pasta static existe
    if not os.path.exists('static'):
        os.makedirs('static')
        print("📁 Pasta 'static' criada")
    
    # Converter logo
    if criar_icone_obpc():
        print()
        print("🎉 Conversão concluída com sucesso!")
        print()
        print("💡 O ícone será usado em:")
        print("   ✓ Executável Sistema_OBPC.exe")
        print("   ✓ Atalho na área de trabalho")
        print("   ✓ Favicon do sistema web")
        print()
    else:
        print()
        print("❌ Falha na conversão do ícone")
        print()
        print("📋 Para resolver:")
        print("   1. Certifique-se que existe uma logo em /static/")
        print("   2. Formatos aceitos: .jpg, .png, .gif")
        print("   3. Execute: pip install Pillow")

if __name__ == "__main__":
    main()