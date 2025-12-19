#!/usr/bin/env python3
"""
Teste direto da função de PDF das atas com logo
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def testar_logo_atas():
    """Testa função diretamente"""
    print("🧪 TESTE DIRETO: Logo nas Atas")
    print("=" * 40)
    
    try:
        # Verificar se os logos existem
        print("1. Verificando logos disponíveis...")
        
        logo_paths = [
            'static/Logo_OBPC.jpg',
            'static/logo_obpc_novo.jpg', 
            'static/logo_igreja_20251014_210556.jpg',
            'app/static/Logo_OBPC.jpg',
            'app/static/logo_obpc_novo.jpg'
        ]
        
        logos_encontrados = []
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                size = os.path.getsize(logo_path)
                print(f"✅ {logo_path} ({size} bytes)")
                logos_encontrados.append(logo_path)
            else:
                print(f"❌ {logo_path} não encontrado")
        
        if logos_encontrados:
            print(f"\n✅ {len(logos_encontrados)} logo(s) disponível(eis)!")
        else:
            print("\n❌ Nenhum logo encontrado!")
            return False
        
        # Testar importação ReportLab Image
        print("\n2. Verificando importação ReportLab...")
        try:
            from reportlab.platypus import Image
            print("✅ reportlab.platypus.Image importado com sucesso")
        except ImportError as e:
            print(f"❌ Erro na importação: {e}")
            return False
        
        # Testar criação de Image
        print("\n3. Testando criação de objeto Image...")
        try:
            primeiro_logo = logos_encontrados[0]
            image_obj = Image(primeiro_logo, width=80, height=80)
            print(f"✅ Objeto Image criado para {primeiro_logo}")
            print(f"   Dimensões especificadas: 80x80")
            return True
        except Exception as e:
            print(f"❌ Erro ao criar Image: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False

if __name__ == "__main__":
    sucesso = testar_logo_atas()
    
    print("\n" + "=" * 40)
    if sucesso:
        print("🎉 TESTE BÁSICO PASSOU!")
        print("💡 Logo pode ser inserido no PDF")
    else:
        print("❌ PROBLEMAS DETECTADOS")
    print("=" * 40)