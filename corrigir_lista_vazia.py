#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar e corrigir o banco usado pelo Flask
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🔍 VERIFICANDO BANCO DO FLASK")
    print("=" * 40)
    
    try:
        from app import create_app, db
        from app.midia.midia_model import Certificado
        from datetime import datetime, date
        
        app = create_app()
        
        with app.app_context():
            print("📊 Verificando banco atual do Flask...")
            
            # Verificar quantos certificados existem
            try:
                total = Certificado.query.count()
                print(f"📈 Total de certificados no Flask: {total}")
                
                if total == 0:
                    print("❌ Lista vazia! Criando certificados diretamente no Flask...")
                    
                    # Criar certificados diretamente através do Flask/SQLAlchemy
                    certificados = [
                        Certificado(
                            nome_pessoa="Ana Sofia Mendes",
                            tipo_certificado="Apresentação",
                            genero="Feminino",
                            data_evento=date(2025, 10, 15),
                            pastor_responsavel="Pastor João Carlos",
                            local_evento="Igreja OBPC - Tietê/SP",
                            filiacao="Roberto Mendes e Sofia Cristina Mendes",
                            padrinhos="Paulo Santos e Maria Santos",
                            numero_certificado="APRES-F-001"
                        ),
                        Certificado(
                            nome_pessoa="Pedro Henrique Costa",
                            tipo_certificado="Apresentação", 
                            genero="Masculino",
                            data_evento=date(2025, 10, 20),
                            pastor_responsavel="Pastor João Carlos",
                            local_evento="Igreja OBPC - Tietê/SP",
                            filiacao="Carlos Costa e Helena Silva Costa",
                            padrinhos="José Roberto e Ana Carolina",
                            numero_certificado="APRES-M-001"
                        ),
                        Certificado(
                            nome_pessoa="Isabella Santos",
                            tipo_certificado="Apresentação",
                            genero="Feminino", 
                            data_evento=date(2025, 11, 1),
                            pastor_responsavel="Pastor João Carlos",
                            local_evento="Igreja OBPC - Tietê/SP",
                            filiacao="Fernando Santos e Isabela Oliveira",
                            padrinhos="Marcos Silva e Fernanda Silva",
                            numero_certificado="APRES-F-002"
                        ),
                        Certificado(
                            nome_pessoa="Carlos Roberto Silva",
                            tipo_certificado="Batismo",
                            genero="Masculino",
                            data_evento=date(2025, 9, 15),
                            pastor_responsavel="Pastor João Carlos", 
                            local_evento="Igreja OBPC - Tietê/SP",
                            filiacao="Roberto Carlos Silva e Maria Silva",
                            numero_certificado="BAT-M-001"
                        ),
                        Certificado(
                            nome_pessoa="Mariana Oliveira",
                            tipo_certificado="Batismo",
                            genero="Feminino",
                            data_evento=date(2025, 9, 20),
                            pastor_responsavel="Pastor João Carlos",
                            local_evento="Igreja OBPC - Tietê/SP", 
                            filiacao="João Oliveira e Mariana Costa",
                            numero_certificado="BAT-F-001"
                        ),
                        Certificado(
                            nome_pessoa="João Paulo Santos",
                            tipo_certificado="Batismo",
                            genero="Masculino",
                            data_evento=date(2025, 10, 5),
                            pastor_responsavel="Pastor João Carlos",
                            local_evento="Igreja OBPC - Tietê/SP",
                            filiacao="Paulo Roberto Santos e Joana Santos",
                            numero_certificado="BAT-M-002"
                        )
                    ]
                    
                    # Adicionar todos ao banco
                    for cert in certificados:
                        db.session.add(cert)
                    
                    db.session.commit()
                    
                    total_final = Certificado.query.count()
                    print(f"✅ {len(certificados)} certificados criados!")
                    print(f"📊 Total final: {total_final}")
                    
                else:
                    print("✅ Certificados já existem!")
                
                # Listar certificados
                certificados = Certificado.query.all()
                
                print("\n📋 CERTIFICADOS NO FLASK:")
                for i, cert in enumerate(certificados, 1):
                    cor = "🔵" if cert.genero == "Masculino" else ("🌸" if cert.genero == "Feminino" else "💜")
                    print(f"{i}. {cor} {cert.nome_pessoa} ({cert.tipo_certificado})")
                    print(f"   Gênero: {cert.genero} | Data: {cert.data_evento}")
                    if cert.filiacao:
                        print(f"   👨‍👩‍👧‍👦 {cert.filiacao}")
                    if cert.padrinhos:
                        print(f"   🤝 {cert.padrinhos}")
                    print()
                
                print("🎯 AGORA A LISTA DEVE APARECER NO NAVEGADOR!")
                print("🔄 Atualize a página: http://127.0.0.1:5000/midia/certificados")
                    
            except Exception as e:
                print(f"❌ Erro ao acessar banco: {str(e)}")
                raise
                
    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()