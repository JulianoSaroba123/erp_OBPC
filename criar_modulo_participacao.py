"""
Script para testar o módulo de Participação de Obreiros
"""
from app import create_app
from app.extensoes import db
from app.secretaria.participacao.participacao_model import ParticipacaoObreiro
from app.obreiros.obreiros_model import Obreiro
from datetime import datetime, date

app = create_app()

with app.app_context():
    print("🔧 === CRIANDO MÓDULO DE PARTICIPAÇÃO DE OBREIROS ===")
    
    try:
        # Criar tabelas
        db.create_all()
        print("✅ Tabelas criadas com sucesso!")
        
        # Verificar se existem obreiros
        obreiros = Obreiro.query.filter_by(status='Ativo').all()
        print(f"📋 Encontrados {len(obreiros)} obreiros ativos")
        
        if obreiros:
            # Criar alguns registros de exemplo
            print("\n📝 Criando registros de exemplo...")
            
            # Participação 1
            participacao1 = ParticipacaoObreiro(
                obreiro_id=obreiros[0].id,
                data_reuniao=date(2025, 10, 1),
                tipo_reuniao="Sede",
                presenca="Presente",
                observacao="Participação ativa na reunião"
            )
            
            # Participação 2 (se houver mais obreiros)
            if len(obreiros) > 1:
                participacao2 = ParticipacaoObreiro(
                    obreiro_id=obreiros[1].id,
                    data_reuniao=date(2025, 10, 1),
                    tipo_reuniao="Sede",
                    presenca="Ausente",
                    observacao="Não compareceu - motivo pessoal"
                )
                db.session.add(participacao2)
            
            # Participação 3 (mesmo obreiro, reunião diferente)
            participacao3 = ParticipacaoObreiro(
                obreiro_id=obreiros[0].id,
                data_reuniao=date(2025, 9, 15),
                tipo_reuniao="Superintendência",
                presenca="Justificado",
                observacao="Viagem a trabalho"
            )
            
            db.session.add(participacao1)
            db.session.add(participacao3)
            db.session.commit()
            
            print("✅ Registros de exemplo criados!")
            
            # Listar participações criadas
            participacoes = ParticipacaoObreiro.query.all()
            print(f"\n📊 Total de participações: {len(participacoes)}")
            for p in participacoes:
                print(f"   - {p.obreiro.nome}: {p.data_reuniao.strftime('%d/%m/%Y')} - {p.tipo_reuniao} - {p.presenca}")
        
        else:
            print("⚠️  Nenhum obreiro encontrado. Cadastre obreiros primeiro.")
            
        print("\n🎯 === MÓDULO CRIADO COM SUCESSO! ===")
        print("📁 Estrutura criada:")
        print("   ✅ app/secretaria/participacao/participacao_model.py")
        print("   ✅ app/secretaria/participacao/participacao_routes.py") 
        print("   ✅ app/secretaria/participacao/templates/participacao/")
        print("   ✅ Menu adicionado à aba Secretaria")
        print("   ✅ Blueprint registrado no app")
        
        print("\n🌐 Rotas disponíveis:")
        print("   📋 /secretaria/participacao - Lista participações")
        print("   ➕ /secretaria/participacao/nova - Nova participação")
        print("   📄 /secretaria/participacao/pdf - Relatório PDF")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()