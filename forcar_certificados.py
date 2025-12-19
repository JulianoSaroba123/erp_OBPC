#!/usr/bin/env python3
"""
Script para forçar a criação de certificados via Flask context
"""

from app import create_app, db
from app.midia.midia_model import Certificado
from datetime import date

def criar_certificados_forcado():
    """Força a criação de certificados via Flask context"""
    app = create_app()
    
    with app.app_context():
        # Verificar quantos certificados existem
        total_atual = Certificado.query.count()
        print(f"📊 Total atual de certificados: {total_atual}")
        
        if total_atual > 0:
            print(f"✅ Já existem {total_atual} certificados!")
            # Listar alguns
            certs = Certificado.query.limit(5).all()
            for cert in certs:
                print(f"  - {cert.nome_pessoa} ({cert.tipo_certificado})")
            return
        
        print("🚀 Criando certificados de exemplo...")
        
        # Criar certificados de exemplo
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
                numero_certificado="APRES-F-001",
                observacoes="Apresentação especial"
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
                numero_certificado="APRES-M-001",
                observacoes="Apresentação especial"
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
                numero_certificado="APRES-F-002",
                observacoes="Apresentação especial"
            ),
            Certificado(
                nome_pessoa="Carlos Roberto Silva",
                tipo_certificado="Batismo",
                genero="Masculino",
                data_evento=date(2025, 9, 15),
                pastor_responsavel="Pastor João Carlos",
                local_evento="Igreja OBPC - Tietê/SP",
                filiacao="Roberto Carlos Silva e Maria Silva",
                numero_certificado="BAT-M-001",
                observacoes="Batismo por imersão"
            ),
            Certificado(
                nome_pessoa="Mariana Oliveira",
                tipo_certificado="Batismo",
                genero="Feminino",
                data_evento=date(2025, 9, 20),
                pastor_responsavel="Pastor João Carlos",
                local_evento="Igreja OBPC - Tietê/SP",
                filiacao="João Oliveira e Mariana Costa",
                numero_certificado="BAT-F-001",
                observacoes="Batismo por imersão"
            ),
            Certificado(
                nome_pessoa="João Paulo Santos",
                tipo_certificado="Batismo",
                genero="Masculino",
                data_evento=date(2025, 10, 5),
                pastor_responsavel="Pastor João Carlos",
                local_evento="Igreja OBPC - Tietê/SP",
                filiacao="Paulo Roberto Santos e Joana Santos",
                numero_certificado="BAT-M-002",
                observacoes="Batismo por imersão"
            )
        ]
        
        try:
            # Adicionar todos ao banco
            for i, cert in enumerate(certificados, 1):
                db.session.add(cert)
                print(f"  ✅ {i}. {cert.nome_pessoa} ({cert.tipo_certificado} - {cert.genero})")
            
            # Confirmar no banco
            db.session.commit()
            
            # Verificar se foram salvos
            total_final = Certificado.query.count()
            print(f"\n🎉 Sucesso! Total de certificados: {total_final}")
            
            # Listar alguns para confirmar
            print("\n📋 Certificados criados:")
            todos = Certificado.query.all()
            for cert in todos:
                print(f"  - ID: {cert.id} | {cert.nome_pessoa} | {cert.tipo_certificado} | {cert.genero}")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro: {e}")
            raise

if __name__ == "__main__":
    criar_certificados_forcado()