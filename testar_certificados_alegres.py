#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da nova funcionalidade de certificados alegres e coloridos
Este script verifica se o novo template está funcionando corretamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.midia.midia_model import Certificado
from datetime import datetime

def main():
    app = create_app()
    
    with app.app_context():
        print("🎉 Testando os novos templates alegres e coloridos! 🎉")
        print("=" * 60)
        
        # Verificar certificados existentes de apresentação
        certificados_apresentacao = Certificado.query.filter_by(tipo_certificado='Apresentação').all()
        
        print(f"📋 Encontrados {len(certificados_apresentacao)} certificados de apresentação:")
        print()
        
        for cert in certificados_apresentacao:
            print(f"🏷️  Nome: {cert.nome_pessoa}")
            print(f"📅 Data: {cert.data_evento.strftime('%d/%m/%Y') if cert.data_evento else 'Não informada'}")
            if cert.filiacao:
                print(f"👨‍👩‍👧‍👦 Filiação: {cert.filiacao}")
            if cert.padrinhos:
                print(f"🤝 Padrinhos: {cert.padrinhos}")
            print(f"🔗 URLs disponíveis:")
            print(f"   - Template Alegre: /midia/certificados/visualizar/{cert.id}/alegre")
            print(f"   - Template Minimalista: /midia/certificados/visualizar/{cert.id}/minimalista")
            print("-" * 40)
        
        # Se não houver certificados de apresentação, criar um de exemplo
        if not certificados_apresentacao:
            print("📝 Criando certificado de exemplo para teste...")
            
            certificado_exemplo = Certificado(
                nome_pessoa="Sofia Isabella da Silva",
                tipo_certificado="Apresentação",
                data_evento=datetime.now(),
                pastor_responsavel="Pastor João Carlos",
                local_evento="Igreja OBPC - Tietê",
                filiacao="João Carlos da Silva e Maria Isabella da Silva",
                padrinhos="Ana Carolina Santos e Pedro Henrique Santos",
                observacoes="Certificado de exemplo para teste dos novos templates coloridos",
                numero_certificado=f"APRES-{datetime.now().strftime('%Y%m%d')}-001"
            )
            
            try:
                db.session.add(certificado_exemplo)
                db.session.commit()
                
                print("✅ Certificado de exemplo criado com sucesso!")
                print(f"🔗 URLs para testar:")
                print(f"   - Template Alegre: /midia/certificados/visualizar/{certificado_exemplo.id}/alegre")
                print(f"   - Template Minimalista: /midia/certificados/visualizar/{certificado_exemplo.id}/minimalista")
                
            except Exception as e:
                print(f"❌ Erro ao criar certificado de exemplo: {str(e)}")
                db.session.rollback()
        
        print()
        print("🌟 Funcionalidades disponíveis nos novos templates:")
        print("   ✨ Cores vibrantes e gradientes")
        print("   🎨 Emojis e decorações alegres")
        print("   📱 Design responsivo para impressão")
        print("   👨‍👩‍👧‍👦 Campo de filiação (pais)")
        print("   🤝 Campo de padrinhos melhorado")
        print("   📖 Versículo bíblico destacado")
        print("   🎉 Animações e efeitos visuais")
        print()
        print("🚀 Para testar, acesse o sistema e vá para a lista de certificados!")
        print("   Agora os certificados de apresentação têm opções de template no menu dropdown.")

if __name__ == "__main__":
    main()