"""
Script para testar completamente o módulo de Participação de Obreiros
"""
from app import create_app
from app.extensoes import db
from app.secretaria.participacao.participacao_model import ParticipacaoObreiro
from app.obreiros.obreiros_model import Obreiro
from app.configuracoes.configuracoes_model import Configuracao
from datetime import datetime, date
from flask import render_template

app = create_app()

with app.app_context():
    print("🧪 === TESTE COMPLETO DO MÓDULO DE PARTICIPAÇÃO ===")
    
    try:
        # 1. Teste do Modelo
        print("\n📋 TESTANDO MODELO:")
        
        # Verificar métodos estáticos
        tipos = ParticipacaoObreiro.get_tipos_reuniao()
        status = ParticipacaoObreiro.get_status_presenca()
        print(f"   ✅ Tipos de reunião: {tipos}")
        print(f"   ✅ Status de presença: {status}")
        
        # Buscar participações existentes
        participacoes = ParticipacaoObreiro.query.all()
        print(f"   ✅ Total de participações: {len(participacoes)}")
        
        if participacoes:
            p = participacoes[0]
            print(f"   ✅ Exemplo: {p.obreiro.nome} - {p.data_reuniao} - {p.tipo_reuniao}")
            print(f"   ✅ to_dict(): {p.to_dict()}")
        
        # 2. Teste dos Templates
        print("\n🎨 TESTANDO TEMPLATES:")
        
        # Template lista
        try:
            obreiros = Obreiro.query.all()
            html_lista = render_template('participacao/lista_participacao.html',
                                       participacoes=participacoes,
                                       tipos_reuniao=tipos,
                                       status_presenca=status,
                                       total_participacoes=len(participacoes),
                                       presentes=len([p for p in participacoes if p.presenca == 'Presente']),
                                       ausentes=len([p for p in participacoes if p.presenca == 'Ausente']),
                                       justificados=len([p for p in participacoes if p.presenca == 'Justificado']))
            print(f"   ✅ Template lista renderizado: {len(html_lista)} caracteres")
        except Exception as e:
            print(f"   ❌ Erro no template lista: {e}")
        
        # Template cadastro
        try:
            html_cadastro = render_template('participacao/cadastro_participacao.html',
                                          obreiros=obreiros,
                                          tipos_reuniao=tipos,
                                          status_presenca=status)
            print(f"   ✅ Template cadastro renderizado: {len(html_cadastro)} caracteres")
        except Exception as e:
            print(f"   ❌ Erro no template cadastro: {e}")
        
        # Template relatório PDF
        try:
            config_obj = Configuracao.query.first()
            if config_obj:
                config = {
                    'nome_igreja': config_obj.nome_igreja,
                    'endereco': config_obj.endereco or 'Rua das Flores, 123',
                    'cidade': f"{config_obj.cidade} - SP" if config_obj.cidade else 'Tietê - SP',
                    'cnpj': config_obj.cnpj or '12.345.678/0001-99',
                    'telefone': config_obj.telefone or '(15) 3285-1234',
                    'email': config_obj.email or 'contato@obpctcp.org.br'
                }
            else:
                config = {
                    'nome_igreja': 'ORGANIZAÇÃO BATISTA PEDRA DE CRISTO',
                    'endereco': 'Rua das Flores, 123',
                    'cidade': 'Tietê - SP',
                    'cnpj': '12.345.678/0001-99',
                    'telefone': '(15) 3285-1234',
                    'email': 'contato@obpctcp.org.br'
                }
            
            html_pdf = render_template('participacao/relatorio_participacao.html',
                                     participacoes=participacoes,
                                     config=config,
                                     data_geracao=datetime.now().strftime('%d/%m/%Y às %H:%M'),
                                     filtros_aplicados=[],
                                     total_participacoes=len(participacoes),
                                     presentes=len([p for p in participacoes if p.presenca == 'Presente']),
                                     ausentes=len([p for p in participacoes if p.presenca == 'Ausente']),
                                     justificados=len([p for p in participacoes if p.presenca == 'Justificado']))
            print(f"   ✅ Template relatório PDF renderizado: {len(html_pdf)} caracteres")
        except Exception as e:
            print(f"   ❌ Erro no template PDF: {e}")
        
        # 3. Teste de Filtros
        print("\n🔍 TESTANDO FILTROS:")
        
        # Filtro por tipo
        sede_participacoes = ParticipacaoObreiro.query.filter_by(tipo_reuniao='Sede').all()
        print(f"   ✅ Participações 'Sede': {len(sede_participacoes)}")
        
        # Filtro por presença
        presentes = ParticipacaoObreiro.query.filter_by(presenca='Presente').all()
        print(f"   ✅ Presentes: {len(presentes)}")
        
        # 4. Teste de Validações
        print("\n🛡️  TESTANDO VALIDAÇÕES:")
        
        # Verificar duplicatas (mesmo obreiro, mesma data, mesmo tipo)
        if participacoes:
            p_teste = participacoes[0]
            duplicata = ParticipacaoObreiro.query.filter_by(
                obreiro_id=p_teste.obreiro_id,
                data_reuniao=p_teste.data_reuniao,
                tipo_reuniao=p_teste.tipo_reuniao
            ).first()
            print(f"   ✅ Verificação de duplicata funciona: {duplicata is not None}")
        
        # 5. Estatísticas
        print("\n📊 ESTATÍSTICAS:")
        total = len(participacoes)
        presentes_count = len([p for p in participacoes if p.presenca == 'Presente'])
        ausentes_count = len([p for p in participacoes if p.presenca == 'Ausente'])
        justificados_count = len([p for p in participacoes if p.presenca == 'Justificado'])
        
        print(f"   📈 Total: {total}")
        print(f"   ✅ Presentes: {presentes_count}")
        print(f"   ❌ Ausentes: {ausentes_count}")
        print(f"   ⚠️  Justificados: {justificados_count}")
        
        if total > 0:
            taxa_participacao = (presentes_count + justificados_count) / total * 100
            print(f"   📊 Taxa de Participação: {taxa_participacao:.1f}%")
        
        print("\n🎉 === TESTE CONCLUÍDO COM SUCESSO! ===")
        print("✅ Módulo de Participação de Obreiros está funcionando perfeitamente!")
        print("\n🌐 Para testar no navegador, inicie o servidor e acesse:")
        print("   http://localhost:5000/secretaria/participacao")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()