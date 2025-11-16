#!/usr/bin/env python3
"""
Criar dados de teste para ofícios
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db
from app.secretaria.oficios.oficios_model import Oficio
from datetime import datetime

def criar_oficios_teste():
    """Cria ofícios de teste"""
    print("🧪 CRIANDO OFÍCIOS DE TESTE")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar se já existem ofícios
            oficios_existentes = Oficio.query.count()
            print(f"📊 Ofícios existentes: {oficios_existentes}")
            
            if oficios_existentes == 0:
                print("\n📝 Criando ofícios de teste...")
                
                # Criar ofícios de exemplo
                oficios_teste = [
                    {
                        'numero': 'OF-2025-001',
                        'destinatario': 'Prefeito Municipal de Tietê',
                        'assunto': 'Solicitação de Uso do Espaço Público',
                        'conteudo': 'Vimos por meio deste solicitar a autorização para uso do espaço público localizado na Praça Central para realização de evento religioso no dia 15 de março de 2025.',
                        'status': 'enviado',
                        'data_envio': datetime(2025, 1, 15)
                    },
                    {
                        'numero': 'OF-2025-002', 
                        'destinatario': 'Secretaria de Educação',
                        'assunto': 'Parcerias Educacionais',
                        'conteudo': 'Gostaríamos de propor uma parceria para desenvolvimento de projetos educacionais voltados à comunidade local.',
                        'status': 'rascunho',
                        'data_envio': datetime(2025, 1, 20)
                    }
                ]
                
                for dados in oficios_teste:
                    oficio = Oficio(
                        numero=dados['numero'],
                        destinatario=dados['destinatario'],
                        assunto=dados['assunto'],
                        conteudo=dados['conteudo'],
                        status=dados['status'],
                        data_envio=dados['data_envio'],
                        criado_em=datetime.now()
                    )
                    db.session.add(oficio)
                
                db.session.commit()
                print("✅ Ofícios de teste criados com sucesso!")
                
            else:
                print("✅ Ofícios já existem no sistema")
            
            # Listar ofícios disponíveis
            print("\n📋 Ofícios disponíveis:")
            oficios = Oficio.query.all()
            for oficio in oficios:
                print(f"   ID {oficio.id}: {oficio.numero} - {oficio.assunto}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    sucesso = criar_oficios_teste()
    
    print("\n" + "=" * 40)
    if sucesso:
        print("🎉 DADOS DE TESTE CRIADOS!")
    else:
        print("❌ FALHA NA CRIAÇÃO DOS DADOS")
    print("=" * 40)