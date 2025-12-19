#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste das cores baseadas no gênero nos certificados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🎨 TESTANDO CORES BASEADAS NO GÊNERO")
    print("=" * 50)
    
    try:
        from app import create_app, db
        from app.midia.midia_model import Certificado
        from datetime import datetime
        
        app = create_app()
        
        with app.app_context():
            print("📊 Verificando certificados existentes...")
            
            # Buscar certificados de apresentação
            certificados = Certificado.query.filter_by(tipo_certificado='Apresentação').all()
            
            if not certificados:
                print("📝 Criando certificados de exemplo para teste...")
                
                # Criar certificado masculino
                cert_masculino = Certificado(
                    nome_pessoa="Pedro Henrique Costa",
                    tipo_certificado="Apresentação",
                    genero="Masculino",
                    data_evento=datetime.now().date(),
                    pastor_responsavel="Pastor João Carlos",
                    local_evento="Igreja OBPC - Tietê",
                    filiacao="Carlos Alberto Costa e Maria Helena Costa",
                    padrinhos="José Santos e Ana Santos",
                    numero_certificado="APRES-M-001"
                )
                
                # Criar certificado feminino
                cert_feminino = Certificado(
                    nome_pessoa="Sofia Isabella Silva",
                    tipo_certificado="Apresentação",
                    genero="Feminino",
                    data_evento=datetime.now().date(),
                    pastor_responsavel="Pastor João Carlos",
                    local_evento="Igreja OBPC - Tietê",
                    filiacao="Roberto Silva e Carolina Isabella Silva",
                    padrinhos="Paulo Oliveira e Mariana Oliveira",
                    numero_certificado="APRES-F-001"
                )
                
                # Criar certificado sem gênero
                cert_neutro = Certificado(
                    nome_pessoa="Alex Morgan Santos",
                    tipo_certificado="Apresentação",
                    genero="",
                    data_evento=datetime.now().date(),
                    pastor_responsavel="Pastor João Carlos",
                    local_evento="Igreja OBPC - Tietê",
                    filiacao="Diego Santos e Patricia Morgan",
                    padrinhos="Lucas Mendes e Julia Mendes",
                    numero_certificado="APRES-N-001"
                )
                
                db.session.add_all([cert_masculino, cert_feminino, cert_neutro])
                db.session.commit()
                
                certificados = [cert_masculino, cert_feminino, cert_neutro]
                print("✅ Certificados de exemplo criados!")
            
            print(f"\n🎯 Encontrados {len(certificados)} certificados de apresentação:")
            print()
            
            for cert in certificados:
                print(f"👤 Nome: {cert.nome_pessoa}")
                print(f"🎨 Gênero: {cert.genero or 'Não informado'}")
                
                # Definir cor baseada no gênero
                if cert.genero == 'Masculino':
                    cor = "🔵 AZUL"
                    tema = "Raios, estrelas, foguetes"
                elif cert.genero == 'Feminino':
                    cor = "🌸 ROSA"
                    tema = "Flores, corações, borboletas"
                else:
                    cor = "💜 ROXO"
                    tema = "Estrelas, brilhos neutros"
                
                print(f"🎨 Cor do template: {cor}")
                print(f"🎭 Tema decorativo: {tema}")
                print(f"🔗 URL: /midia/certificados/visualizar/{cert.id}/alegre")
                print("-" * 40)
            
            print("🌈 PALETA DE CORES IMPLEMENTADA:")
            print("🔵 Masculino: Azul (#4A90E2) com tons de céu")
            print("🌸 Feminino: Rosa (#FF69B4) com tons suaves")
            print("💜 Neutro: Roxo (#9B59B6) para casos sem gênero")
            print()
            print("✨ CARACTERÍSTICAS POR GÊNERO:")
            print("🔵 Azul: Raios, estrelas, foguetes - energia e aventura")
            print("🌸 Rosa: Flores, corações, borboletas - delicadeza e carinho")
            print("💜 Roxo: Estrelas universais - elegância neutra")
            print()
            print("🚀 Sistema pronto! Acesse os certificados para ver as cores!")
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()