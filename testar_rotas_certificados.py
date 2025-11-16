#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.abspath('.'))

def testar_rotas_certificados():
    """Testa as rotas dos certificados"""
    
    print("🧪 TESTE: Rotas dos Certificados")
    print("=" * 50)
    
    try:
        from app import create_app, db
        from app.midia.midia_model import Certificado
        from datetime import date
        
        # Criar aplicação
        app = create_app()
        
        with app.app_context():
            # Buscar um certificado existente
            certificado = Certificado.query.first()
            
            if certificado:
                print(f"✅ Certificado encontrado: ID {certificado.id}")
                print(f"   Nome: {certificado.nome_pessoa}")
                print(f"   Tipo: {certificado.tipo_certificado}")
                
                print(f"\n🔗 URLs disponíveis:")
                print(f"   📝 Editar: /midia/certificados/editar/{certificado.id}")
                print(f"   👁️  Visualizar: /midia/certificados/visualizar/{certificado.id}")
                print(f"   📄 PDF: /midia/certificados/pdf/{certificado.id}")
                
                # Testar se tem padrinhos
                if certificado.tipo_certificado == 'Apresentação' and certificado.padrinhos:
                    print(f"   👥 Padrinhos: {certificado.padrinhos}")
                
            else:
                print("❌ Nenhum certificado encontrado no banco")
                
                # Criar um certificado de teste
                print("🔄 Criando certificado de teste...")
                certificado_teste = Certificado(
                    nome_pessoa="Teste da Silva",
                    tipo_certificado="Apresentação", 
                    data_evento=date.today(),
                    pastor_responsavel="Pastor Teste",
                    local_evento="Igreja Teste",
                    padrinhos="João Silva\nMaria Silva"
                )
                
                db.session.add(certificado_teste)
                db.session.commit()
                
                print(f"✅ Certificado criado: ID {certificado_teste.id}")
                print(f"   👁️  Teste visualizar: /midia/certificados/visualizar/{certificado_teste.id}")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_rotas_certificados()