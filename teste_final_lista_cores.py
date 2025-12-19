#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste final - verifica se a lista de certificados e cores estão funcionando
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🧪 TESTE FINAL - LISTA E CORES")
    print("=" * 50)
    
    try:
        from app import create_app, db
        from app.midia.midia_model import Certificado
        
        app = create_app()
        
        with app.app_context():
            print("📊 Verificando certificados no banco...")
            
            # Contar total
            total = Certificado.query.count()
            print(f"📈 Total de certificados: {total}")
            
            if total == 0:
                print("❌ Nenhum certificado encontrado!")
                return
            
            # Listar todos
            certificados = Certificado.query.order_by(Certificado.id).all()
            
            print("\n📋 LISTA COMPLETA:")
            for i, cert in enumerate(certificados, 1):
                # Determinar emoji de cor
                if cert.genero == 'Masculino':
                    cor = "🔵"
                elif cert.genero == 'Feminino':
                    cor = "🌸"
                else:
                    cor = "💜"
                
                print(f"{i:2d}. {cor} {cert.nome_pessoa}")
                print(f"     📝 {cert.tipo_certificado} | Gênero: {cert.genero or 'Neutro'}")
                print(f"     📅 {cert.data_evento.strftime('%d/%m/%Y') if cert.data_evento else 'N/A'}")
                
                if cert.filiacao:
                    print(f"     👨‍👩‍👧‍👦 {cert.filiacao}")
                if cert.padrinhos:
                    print(f"     🤝 {cert.padrinhos}")
                
                print(f"     🔗 Alegre: /midia/certificados/visualizar/{cert.id}/alegre")
                print(f"     🔗 Minimal: /midia/certificados/visualizar/{cert.id}/minimalista")
                print()
            
            # Resumo por gênero e tipo
            print("📊 RESUMO:")
            apresentacoes = Certificado.query.filter_by(tipo_certificado='Apresentação').count()
            batismos = Certificado.query.filter_by(tipo_certificado='Batismo').count()
            
            masculinos = Certificado.query.filter_by(genero='Masculino').count()
            femininos = Certificado.query.filter_by(genero='Feminino').count() 
            neutros = total - masculinos - femininos
            
            print(f"📄 Apresentações: {apresentacoes}")
            print(f"💒 Batismos: {batismos}")
            print()
            print(f"🔵 Masculinos: {masculinos} (tema azul)")
            print(f"🌸 Femininos: {femininos} (tema rosa)")
            print(f"💜 Neutros: {neutros} (tema roxo)")
            
            print("\n✅ SISTEMA FUNCIONANDO!")
            print("🌐 Lista: http://127.0.0.1:5000/midia/certificados")
            print("➕ Novo: http://127.0.0.1:5000/midia/certificados/novo")
            
            print("\n🎨 TESTE DAS CORES:")
            print("1. Acesse a lista de certificados")
            print("2. Clique no dropdown do botão 'olho' 👁️")
            print("3. Escolha 'Template Alegre e Colorido'")
            print("4. Veja as cores baseadas no gênero!")
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()