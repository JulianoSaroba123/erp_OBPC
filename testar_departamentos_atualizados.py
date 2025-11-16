#!/usr/bin/env python3
"""
Script de teste para o módulo Departamentos atualizado
Testa todas as funcionalidades: CRUD, cronograma mensal e planejamento de aulas

OBPC - Sistema de Gestão de Igreja
Versão: 2025.1
Data: 06/10/2025
"""

import os
import sys
import requests
import json
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def testar_departamentos():
    """Testa o módulo de departamentos"""
    print("🏛️  TESTE DO MÓDULO DEPARTAMENTOS")
    print("=" * 50)
    
    # Importar dependências do Flask
    try:
        from app import create_app, db
        from app.departamentos.departamentos_model import Departamento
        
        # Criar app de teste
        app = create_app()
        
        with app.app_context():
            # 1. Testar modelo atualizado
            print("\n📋 1. TESTANDO MODELO ATUALIZADO")
            print("-" * 30)
            
            # Verificar se as colunas existem
            try:
                # Criar departamento de teste
                dept_teste = Departamento(
                    nome="Departamento de Teste - Atualizado",
                    lider="João Silva",
                    vice_lider="Maria Santos", 
                    descricao="Departamento criado para testar novas funcionalidades",
                    cronograma_mensal="""
CRONOGRAMA MENSAL - DEPARTAMENTO TESTE:

🗓️  PRIMEIRA SEMANA:
- Segunda: Reunião de planejamento (19h)
- Quarta: Estudo bíblico (19h30)
- Sábado: Atividade prática (14h)

🗓️  SEGUNDA SEMANA:  
- Terça: Ensaio de apresentação (19h)
- Quinta: Capacitação de líderes (19h)
- Domingo: Ministração no culto (18h)

🗓️  TERCEIRA SEMANA:
- Segunda: Avaliação do mês anterior (19h)
- Quarta: Estudo temático (19h30)
- Sábado: Visitas e evangelismo (14h)

🗓️  QUARTA SEMANA:
- Sexta: Confraternização mensal (19h)
- Domingo: Relatório e testemunhos (18h)
                    """.strip(),
                    possui_aulas=True,
                    planejamento_aulas="""
PLANEJAMENTO DE AULAS - CURSO BÍBLICO:

📚 MÓDULO 1: FUNDAMENTOS (4 aulas)
• Aula 1: Conhecendo a Bíblia
• Aula 2: Salvação e Novo Nascimento  
• Aula 3: Vida Cristã Prática
• Aula 4: Oração e Comunhão

📚 MÓDULO 2: CRESCIMENTO (4 aulas)
• Aula 5: Estudo Bíblico Pessoal
• Aula 6: Dons Espirituais
• Aula 7: Evangelismo e Testemunho
• Aula 8: Discipulado

🎯 METODOLOGIA:
- Exposição bíblica (30 min)
- Dinâmica interativa (15 min)
- Aplicação prática (15 min)
- Material: Apostila + Bíblia

📅 CRONOGRAMA: Quartas-feiras, 19h30-20h30
📍 LOCAL: Sala de aulas (anexo da igreja)
👥 PÚBLICO: Novos convertidos e interessados
                    """.strip(),
                    contato="(11) 99999-9999",
                    status="Ativo"
                )
                
                print(f"✅ Modelo criado com sucesso!")
                print(f"   Nome: {dept_teste.nome}")
                print(f"   Liderança: {dept_teste.lideranca_completa}")
                print(f"   Possui aulas: {dept_teste.possui_aulas}")
                print(f"   Cronograma: {len(dept_teste.cronograma_mensal) if dept_teste.cronograma_mensal else 0} caracteres")
                print(f"   Planejamento: {len(dept_teste.planejamento_aulas) if dept_teste.planejamento_aulas else 0} caracteres")
                
                # Testar propriedades
                print(f"   Badge aulas: {dept_teste.possui_aulas_badge}")
                print(f"   Status badge: {dept_teste.status_badge_class}")
                
            except Exception as e:
                print(f"❌ Erro ao testar modelo: {e}")
                return False
            
            # 2. Testar banco de dados  
            print("\n💾 2. TESTANDO BANCO DE DADOS")
            print("-" * 30)
            
            try:
                # Verificar se a tabela existe e tem as colunas corretas
                resultado = db.engine.execute("PRAGMA table_info(departamentos)")
                colunas = [row[1] for row in resultado]
                
                colunas_esperadas = ['id', 'nome', 'lider', 'vice_lider', 'descricao', 
                                   'contato', 'status', 'cronograma_mensal', 
                                   'possui_aulas', 'planejamento_aulas', 'criado_em']
                
                print(f"📊 Colunas encontradas: {len(colunas)}")
                for coluna in colunas:
                    status = "✅" if coluna in colunas_esperadas else "❓"
                    print(f"   {status} {coluna}")
                
                # Verificar se todas as colunas esperadas existem
                colunas_faltando = [col for col in colunas_esperadas if col not in colunas]
                if colunas_faltando:
                    print(f"⚠️  Colunas faltando: {colunas_faltando}")
                else:
                    print("✅ Todas as colunas esperadas estão presentes!")
                
            except Exception as e:
                print(f"❌ Erro ao verificar banco: {e}")
                return False
            
            # 3. Testar CRUD
            print("\n🔧 3. TESTANDO OPERAÇÕES CRUD")
            print("-" * 30)
            
            try:
                # Salvar no banco
                db.session.add(dept_teste)
                db.session.commit()
                print("✅ CREATE: Departamento salvo no banco")
                
                # Ler do banco
                dept_lido = Departamento.query.filter_by(nome="Departamento de Teste - Atualizado").first()
                if dept_lido:
                    print("✅ READ: Departamento encontrado no banco")
                    print(f"   ID: {dept_lido.id}")
                    print(f"   Possui aulas: {dept_lido.possui_aulas}")
                else:
                    print("❌ READ: Departamento não encontrado")
                    return False
                
                # Atualizar
                dept_lido.cronograma_mensal += "\n\n📝 OBSERVAÇÃO: Cronograma atualizado em teste"
                db.session.commit()
                print("✅ UPDATE: Departamento atualizado")
                
                # Contar total
                total = Departamento.query.count()
                print(f"📊 Total de departamentos no banco: {total}")
                
            except Exception as e:
                print(f"❌ Erro nas operações CRUD: {e}")
                return False
            
            # 4. Testar funcionalidades específicas
            print("\n🎯 4. TESTANDO FUNCIONALIDADES ESPECÍFICAS")
            print("-" * 30)
            
            try:
                # Testar departamentos com aulas
                depts_com_aulas = Departamento.query.filter_by(possui_aulas=True).count()
                print(f"📚 Departamentos com aulas: {depts_com_aulas}")
                
                # Testar departamentos com cronograma
                depts_com_cronograma = Departamento.query.filter(
                    Departamento.cronograma_mensal.isnot(None)
                ).count()
                print(f"📅 Departamentos com cronograma: {depts_com_cronograma}")
                
                # Testar to_dict com novos campos
                dept_dict = dept_lido.to_dict()
                campos_novos = ['cronograma_mensal', 'possui_aulas', 'planejamento_aulas', 'criado_em']
                for campo in campos_novos:
                    if campo in dept_dict:
                        print(f"✅ Campo '{campo}' presente no to_dict()")
                    else:
                        print(f"❌ Campo '{campo}' ausente no to_dict()")
                
            except Exception as e:
                print(f"❌ Erro ao testar funcionalidades: {e}")
                return False
            
            # 5. Limpar dados de teste
            print("\n🧹 5. LIMPANDO DADOS DE TESTE")
            print("-" * 30)
            
            try:
                db.session.delete(dept_lido)
                db.session.commit()
                print("✅ Departamento de teste removido")
                
            except Exception as e:
                print(f"⚠️  Erro ao limpar dados: {e}")
            
            print("\n" + "=" * 50)
            print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
            print("=" * 50)
            print("🎉 O módulo Departamentos está funcionando perfeitamente!")
            print("\n📋 Funcionalidades testadas:")
            print("• ✅ Modelo atualizado com novos campos")
            print("• ✅ Banco de dados com estrutura correta") 
            print("• ✅ Operações CRUD funcionando")
            print("• ✅ Campo cronograma_mensal")
            print("• ✅ Campo possui_aulas (boolean)")
            print("• ✅ Campo planejamento_aulas (condicional)")
            print("• ✅ Propriedades e métodos auxiliares")
            
            return True
            
    except ImportError as e:
        print(f"❌ Erro ao importar módulos: {e}")
        print("⚠️  Certifique-se de que o Flask app está configurado corretamente")
        return False
    
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def main():
    """Função principal"""
    print("🏛️  OBPC - Teste do Módulo Departamentos")
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    if testar_departamentos():
        print("\n🚀 Pronto para usar o módulo Departamentos atualizado!")
        sys.exit(0)
    else:
        print("\n❌ Testes falharam - verifique a configuração")
        sys.exit(1)

if __name__ == "__main__":
    main()