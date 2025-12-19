#!/usr/bin/env python3
"""
Script para criar dados de exemplo do módulo Ofícios de Solicitação de Doação
Sistema OBPC - Organização Batista Pedra de Cristo
"""

import sys
import os
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.secretaria.oficios.oficios_model import Oficio

def criar_dados_oficios():
    """Cria dados de exemplo para o módulo de ofícios"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🏛️ === CRIANDO DADOS DE EXEMPLO - OFÍCIOS DE SOLICITAÇÃO ===")
            print()
            
            # Cria as tabelas se não existirem
            db.create_all()
            
            # Lista de ofícios de exemplo
            oficios_exemplo = [
                {
                    'destinatario': 'Prefeitura Municipal de Tietê',
                    'assunto': 'Solicitação de Apoio para Festa Junina Beneficente',
                    'descricao': '''Prezados Senhores,\n\nA Organização Batista Pedra de Cristo vem, por meio deste, solicitar o apoio da Prefeitura Municipal de Tietê para a realização de nossa tradicional Festa Junina Beneficente, que acontecerá no dia 25 de junho de 2025.\n\nO evento tem como objetivo arrecadar fundos para a reforma do salão comunitário da igreja, que atende mais de 200 famílias da comunidade local. Solicitamos apoio nas seguintes modalidades:\n\n- Cessão de palco e sistema de som\n- Disponibilização de cadeiras e mesas\n- Apoio na divulgação do evento\n- Autorização para venda de alimentos no evento\n\nO evento é totalmente beneficente e os recursos arrecadados serão aplicados exclusivamente na reforma das instalações que beneficiam toda a comunidade.''',
                    'status': 'Emitido'
                },
                {
                    'destinatario': 'Supermercado São João Ltda.',
                    'assunto': 'Solicitação de Doação de Alimentos para Campanha de Natal',
                    'descricao': '''Estimados Senhores,\n\nCom o espírito natalino se aproximando, nossa igreja está organizando a tradicional Campanha de Natal Solidário, que tem como objetivo distribuir cestas básicas para famílias carentes da nossa região.\n\nVenho, respeitosamente, solicitar a doação de alimentos não perecíveis para compor as cestas que serão distribuídas às famílias cadastradas em nosso projeto social.\n\nSugestões de produtos para doação:\n- Arroz, feijão, açúcar, óleo\n- Macarrão, farinha de trigo\n- Leite em pó, café\n- Enlatados diversos\n\nA campanha beneficiará aproximadamente 150 famílias e acontecerá na véspera do Natal. Todos os produtos doados receberão destinação apropriada e transparente.\n\nColocamo-nos à disposição para fornecer relatório detalhado da distribuição realizada.''',
                    'status': 'Enviado'
                },
                {
                    'destinatario': 'Rotary Club de Tietê',
                    'assunto': 'Parceria para Projeto de Inclusão Digital',
                    'descricao': '''Caros Companheiros,\n\nA OBPC desenvolve há dois anos um projeto de inclusão digital para jovens e idosos da comunidade, oferecendo cursos básicos de informática e internet.\n\nGostaríamos de solicitar parceria do Rotary Club de Tietê para ampliar nosso projeto, especificamente:\n\n1. Doação de computadores usados em bom estado\n2. Apoio na aquisição de mobiliário (mesas e cadeiras)\n3. Patrocínio de material didático\n4. Divulgação do projeto na comunidade\n\nAtualmente atendemos 50 pessoas por mês, e com o apoio de vocês, poderíamos dobrar essa capacidade. O projeto é totalmente gratuito e tem transformado vidas em nossa comunidade.\n\nTemos disponível um projeto detalhado com cronograma e orçamento que pode ser apresentado em reunião específica.''',
                    'status': 'Respondido'
                },
                {
                    'destinatario': 'Empresa Construtora Bandeirantes S.A.',
                    'assunto': 'Doação de Materiais de Construção para Reforma',
                    'descricao': '''Prezados Senhores,\n\nNossa igreja está passando por um momento de crescimento e necessita urgentemente de reformas em suas instalações para melhor atender a comunidade.\n\nSolicitamos a generosa doação de materiais de construção para a reforma do telhado e pintura externa do templo:\n\n- Telhas de fibrocimento ou similares\n- Tinta para pintura externa (aproximadamente 200 litros)\n- Cimento e materiais básicos de construção\n- Mão de obra especializada (se possível)\n\nA reforma beneficiará diretamente mais de 300 pessoas que frequentam nossa igreja semanalmente, além de eventos comunitários que realizamos.\n\nEstamos abertos a contrapartidas como divulgação da empresa em nossos eventos e redes sociais, bem como fornecimento de certificado de responsabilidade social.''',
                    'status': 'Atendido'
                },
                {
                    'destinatario': 'Hospital Santa Casa de Tietê',
                    'assunto': 'Proposta de Parceria para Assistência Hospitalar',
                    'descricao': '''Direção do Hospital Santa Casa,\n\nA OBPC possui um grupo de voluntários especializados em assistência hospitalar e espiritual, e gostaríamos de propor uma parceria com o hospital.\n\nNossa proposta inclui:\n\n1. Disponibilização de voluntários para apoio aos pacientes e familiares\n2. Organização de atividades recreativas para pacientes internados\n3. Assistência espiritual não denominacional (respeitando todas as crenças)\n4. Apoio na organização de campanhas de doação de sangue\n\nTodos os nossos voluntários possuem treinamento adequado e experiência na área. A parceria seria totalmente gratuita, como forma de retribuir à comunidade o trabalho social desenvolvido pelo hospital.\n\nGostaríamos de agendar uma reunião para apresentar nossa proposta em detalhes e adequá-la às necessidades do hospital.''',
                    'status': 'Emitido'
                }
            ]
            
            # Gera números sequenciais e datas
            contador = 1
            data_base = datetime.now().date() - timedelta(days=30)
            
            oficios_criados = []
            
            for dados in oficios_exemplo:
                # Gera número sequencial
                numero = f"OF-2025-{contador:03d}"
                
                # Calcula data (espalhadas nos últimos 30 dias)
                data_oficio = data_base + timedelta(days=contador * 6)
                
                # Cria o ofício
                oficio = Oficio(
                    numero=numero,
                    data=data_oficio,
                    destinatario=dados['destinatario'],
                    assunto=dados['assunto'],
                    descricao=dados['descricao'],
                    status=dados['status'],
                    criado_em=datetime.combine(data_oficio, datetime.min.time())
                )
                
                db.session.add(oficio)
                oficios_criados.append(oficio)
                contador += 1
            
            # Salva no banco
            db.session.commit()
            
            # Exibe resultado
            print("✅ OFÍCIOS CRIADOS COM SUCESSO!")
            print("=" * 50)
            
            for oficio in oficios_criados:
                print(f"📄 {oficio.numero} - {oficio.data.strftime('%d/%m/%Y')}")
                print(f"   Para: {oficio.destinatario}")
                print(f"   Assunto: {oficio.assunto[:50]}...")
                print(f"   Status: {oficio.status}")
                print()
            
            print("📊 RESUMO:")
            print(f"   • Total de ofícios: {len(oficios_criados)}")
            print(f"   • Emitidos: {len([o for o in oficios_criados if o.status == 'Emitido'])}")
            print(f"   • Enviados: {len([o for o in oficios_criados if o.status == 'Enviado'])}")
            print(f"   • Respondidos: {len([o for o in oficios_criados if o.status == 'Respondido'])}")
            print(f"   • Atendidos: {len([o for o in oficios_criados if o.status == 'Atendido'])}")
            print()
            print("🎯 MÓDULO PRONTO PARA USO!")
            print("   Acesse: Sistema → Secretaria → Ofícios de Solicitação")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERRO ao criar dados: {str(e)}")
            return False
        
        return True

if __name__ == "__main__":
    sucesso = criar_dados_oficios()
    if sucesso:
        print("\n✨ Dados criados com sucesso!")
    else:
        print("\n❌ Erro na criação dos dados!")
        sys.exit(1)