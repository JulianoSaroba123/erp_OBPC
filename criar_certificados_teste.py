#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar certificados de teste (batismo e apresentação)
Data: 07/10/2025
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.midia.midia_model import Certificado
from datetime import date, datetime

def criar_certificados_teste():
    """Cria certificados de teste para demonstração"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("📜 Criando certificados de teste...")
            print("=" * 50)
            
            # Limpar certificados de teste anteriores (opcional)
            certificados_teste = Certificado.query.filter(
                Certificado.nome_pessoa.in_([
                    'João Silva Santos', 
                    'Maria Fernanda Oliveira', 
                    'Pedro Henrique Costa'
                ])
            ).all()
            
            for cert in certificados_teste:
                db.session.delete(cert)
            
            # 1. CERTIFICADO DE BATISMO
            certificado_batismo = Certificado(
                nome_pessoa='João Silva Santos',
                tipo_certificado='Batismo',
                data_evento=date(2025, 9, 15),  # 15/09/2025
                pastor_responsavel='Pastor Paulo Ricardo',
                local_evento='Igreja OBPC - Tietê/SP',
                observacoes='Batismo realizado durante o culto dominical com a presença da família.',
                numero_certificado='BAT-2025-015'
            )
            
            # 2. CERTIFICADO DE APRESENTAÇÃO - FEMININO
            certificado_apresentacao_fem = Certificado(
                nome_pessoa='Maria Fernanda Oliveira',
                tipo_certificado='Apresentação',
                data_evento=date(2025, 8, 25),  # 25/08/2025
                pastor_responsavel='Pastor Paulo Ricardo',
                local_evento='Igreja OBPC - Tietê/SP',
                observacoes='Apresentação da criança pelos pais Carlos e Ana Oliveira.',
                numero_certificado='APR-2025-008'
            )
            
            # 3. CERTIFICADO DE APRESENTAÇÃO - MASCULINO
            certificado_apresentacao_masc = Certificado(
                nome_pessoa='Pedro Henrique Costa',
                tipo_certificado='Apresentação',
                data_evento=date(2025, 10, 6),  # 06/10/2025
                pastor_responsavel='Pastor Paulo Ricardo',
                local_evento='Igreja OBPC - Tietê/SP',
                observacoes='Apresentação da criança pelos pais Marcos e Juliana Costa.',
                numero_certificado='APR-2025-012'
            )
            
            # Adicionar ao banco
            db.session.add(certificado_batismo)
            db.session.add(certificado_apresentacao_fem)
            db.session.add(certificado_apresentacao_masc)
            
            # Salvar
            db.session.commit()
            
            print("✅ Certificados criados com sucesso!")
            print(f"📋 Total de certificados: {Certificado.query.count()}")
            
            print("\n📜 CERTIFICADOS CRIADOS:")
            print("=" * 50)
            
            certificados = Certificado.query.order_by(Certificado.data_evento.desc()).all()
            
            for cert in certificados:
                print(f"• {cert.tipo_certificado}: {cert.nome_pessoa}")
                print(f"  Data: {cert.data_evento.strftime('%d/%m/%Y')}")
                print(f"  Pastor: {cert.pastor_responsavel}")
                print(f"  Número: {cert.numero_certificado}")
                print(f"  ID: {cert.id}")
                print()
            
            print("🌐 COMO ACESSAR:")
            print("• Sistema > Mídia > Certificados")
            print("• Visualizar, editar ou gerar PDF dos certificados")
            
            print("\n🔗 URLS DIRETAS:")
            print("• Lista: http://127.0.0.1:5000/midia/certificados")
            for cert in certificados:
                print(f"• PDF {cert.nome_pessoa}: http://127.0.0.1:5000/midia/certificados/pdf/{cert.id}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao criar certificados: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    criar_certificados_teste()