#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar exatamente qual banco o Flask está usando
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🔍 VERIFICANDO BANCO REAL DO FLASK")
    print("=" * 45)
    
    try:
        from app import create_app, db
        from app.midia.midia_model import Certificado
        
        app = create_app()
        
        with app.app_context():
            # Verificar a URL do banco que o Flask está usando
            database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
            print(f"📊 URL do banco Flask: {database_url}")
            
            # Extrair o caminho do arquivo
            if database_url.startswith('sqlite:///'):
                banco_path = database_url.replace('sqlite:///', '')
                print(f"📁 Caminho do banco: {banco_path}")
                
                # Verificar se o arquivo existe
                if os.path.exists(banco_path):
                    print(f"✅ Arquivo existe: {banco_path}")
                    
                    # Verificar tamanho do arquivo
                    tamanho = os.path.getsize(banco_path)
                    print(f"📏 Tamanho: {tamanho} bytes")
                else:
                    print(f"❌ Arquivo NÃO existe: {banco_path}")
                    print("🔧 O Flask vai criar o banco na primeira consulta")
            
            # Tentar consultar certificados
            try:
                total = Certificado.query.count()
                print(f"📈 Certificados encontrados pelo Flask: {total}")
                
                if total == 0:
                    print("\n🚨 PROBLEMA: Flask não vê os certificados!")
                    print("💡 Vou criar certificados diretamente através do Flask...")
                    
                    # Força criação das tabelas
                    db.create_all()
                    
                    # Criar certificados através do SQLAlchemy
                    from datetime import date
                    
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
                        )
                    ]
                    
                    # Adicionar ao banco
                    for cert in certificados:
                        db.session.add(cert)
                    
                    db.session.commit()
                    
                    # Verificar novamente
                    total_final = Certificado.query.count()
                    print(f"✅ Certificados criados pelo Flask: {total_final}")
                    
                    # Listar certificados
                    certs = Certificado.query.all()
                    print("\n📋 CERTIFICADOS NO FLASK:")
                    for i, cert in enumerate(certs, 1):
                        cor = "🔵" if cert.genero == "Masculino" else "🌸"
                        print(f"{i}. {cor} {cert.nome_pessoa} ({cert.tipo_certificado})")
                        print(f"   ID: {cert.id} | Gênero: {cert.genero}")
                        if cert.filiacao:
                            print(f"   👨‍👩‍👧‍👦 {cert.filiacao}")
                        if cert.padrinhos:
                            print(f"   🤝 {cert.padrinhos}")
                        print()
                    
                    print("🎉 AGORA A LISTA DEVE APARECER!")
                    
                else:
                    print(f"✅ Flask encontrou {total} certificados!")
                    
            except Exception as e:
                print(f"❌ Erro ao consultar certificados: {str(e)}")
                
                # Tentar criar as tabelas
                print("🔧 Tentando criar tabelas...")
                db.create_all()
                print("✅ Tabelas criadas!")
                
    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()