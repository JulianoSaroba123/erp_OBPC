#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste rápido do modelo Certificado após correção do banco
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🧪 TESTE RÁPIDO DOS CERTIFICADOS")
    print("=" * 40)
    
    try:
        from app import create_app, db
        from app.midia.midia_model import Certificado
        
        app = create_app()
        
        with app.app_context():
            print("📊 Testando consulta de certificados...")
            
            # Teste simples
            total = Certificado.query.count()
            print(f"✅ Total de certificados: {total}")
            
            if total > 0:
                certificados = Certificado.query.limit(5).all()
                print(f"📋 Primeiros {len(certificados)} certificados:")
                
                for cert in certificados:
                    print(f"  - {cert.nome_pessoa} ({cert.tipo_certificado})")
                    if hasattr(cert, 'filiacao') and cert.filiacao:
                        print(f"    👨‍👩‍👧‍👦 Filiação: {cert.filiacao}")
                    if hasattr(cert, 'padrinhos') and cert.padrinhos:
                        print(f"    🤝 Padrinhos: {cert.padrinhos}")
                
                print("\n✅ CERTIFICADOS FUNCIONANDO PERFEITAMENTE!")
                print("🎯 Agora a lista deve aparecer no sistema!")
                
            else:
                print("ℹ️ Nenhum certificado encontrado")
                
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()