#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para adicionar campos de indicadores de distribuição financeira
Sistema OBPC - Igreja O Brasil para Cristo

Adiciona campos para controlar a distribuição de Ofertas e Dízimos:
- Percentual Administrativo Sede (30%)
- Percentual Prebenda Pastoral (0-30% ajustável)
- Percentual Cuidados da Igreja (40%)
"""

import os
import sys

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.configuracoes.configuracoes_model import Configuracao
from sqlalchemy import inspect, text

def adicionar_campos_indicadores():
    """Adiciona os campos de indicadores de distribuição"""
    app = create_app()
    
    with app.app_context():
        try:
            print("="*70)
            print("ADICIONANDO CAMPOS DE INDICADORES DE DISTRIBUIÇÃO FINANCEIRA")
            print("="*70)
            
            # Verificar se a tabela existe
            inspector = inspect(db.engine)
            if not inspector.has_table('configuracoes'):
                print("❌ Tabela 'configuracoes' não encontrada!")
                return
            
            # Obter colunas existentes
            colunas_existentes = {col['name'] for col in inspector.get_columns('configuracoes')}
            print(f"\n📋 Colunas existentes na tabela: {len(colunas_existentes)}")
            
            # Definir novos campos
            is_postgres = db.engine.dialect.name == 'postgresql'
            float_type = 'DOUBLE PRECISION' if is_postgres else 'FLOAT'
            
            novos_campos = {
                'percentual_administrativo': {
                    'tipo': float_type,
                    'default': 30.0,
                    'descricao': 'Percentual para Administrativo Sede (fixo 30%)'
                },
                'percentual_prebenda': {
                    'tipo': float_type,
                    'default': 30.0,
                    'descricao': 'Percentual para Prebenda Pastoral (ajustável 0-30%)'
                },
                'percentual_cuidados_igreja': {
                    'tipo': float_type,
                    'default': 40.0,
                    'descricao': 'Percentual para Cuidados da Igreja (fixo 40%)'
                },
                'exibir_indicador_distribuicao': {
                    'tipo': 'BOOLEAN',
                    'default': True,
                    'descricao': 'Exibir indicador de distribuição no dashboard'
                }
            }
            
            # Adicionar campos faltantes
            campos_adicionados = 0
            campos_ja_existentes = 0
            
            for campo, config in novos_campos.items():
                if campo not in colunas_existentes:
                    try:
                        print(f"\n➕ Adicionando campo '{campo}'...")
                        print(f"   Descrição: {config['descricao']}")
                        
                        # Criar SQL de acordo com o tipo de banco
                        if is_postgres:
                            # PostgreSQL permite DEFAULT direto no ALTER TABLE
                            if config['tipo'] == 'BOOLEAN':
                                default_value = 'TRUE' if config['default'] else 'FALSE'
                            else:
                                default_value = str(config['default'])
                            
                            sql = f"ALTER TABLE configuracoes ADD COLUMN {campo} {config['tipo']} DEFAULT {default_value}"
                        else:
                            # SQLite: adicionar coluna sem DEFAULT, depois update
                            sql = f"ALTER TABLE configuracoes ADD COLUMN {campo} {config['tipo']}"
                        
                        with db.engine.begin() as conn:
                            conn.execute(text(sql))
                            
                            # Para SQLite, fazer UPDATE com valor padrão
                            if not is_postgres:
                                if config['tipo'] == 'BOOLEAN':
                                    default_value = 1 if config['default'] else 0
                                else:
                                    default_value = config['default']
                                
                                update_sql = f"UPDATE configuracoes SET {campo} = {default_value} WHERE {campo} IS NULL"
                                conn.execute(text(update_sql))
                        
                        print(f"   ✅ Campo '{campo}' adicionado com sucesso! (Valor padrão: {config['default']})")
                        campos_adicionados += 1
                        
                    except Exception as e:
                        print(f"   ❌ Erro ao adicionar campo '{campo}': {str(e)}")
                else:
                    print(f"\n✓ Campo '{campo}' já existe")
                    campos_ja_existentes += 1
            
            # Atualizar a configuração existente
            print("\n" + "="*70)
            print("ATUALIZANDO CONFIGURAÇÃO EXISTENTE")
            print("="*70)
            
            config = Configuracao.query.filter_by(id=1).first()
            if config:
                print("\n✓ Configuração encontrada (ID=1)")
                
                # Atualizar apenas se os valores ainda não foram definidos
                valores_atualizados = []
                
                if hasattr(config, 'percentual_administrativo') and (config.percentual_administrativo is None or config.percentual_administrativo == 0):
                    config.percentual_administrativo = 30.0
                    valores_atualizados.append('percentual_administrativo = 30%')
                
                if hasattr(config, 'percentual_prebenda') and (config.percentual_prebenda is None or config.percentual_prebenda == 0):
                    config.percentual_prebenda = 30.0
                    valores_atualizados.append('percentual_prebenda = 30%')
                
                if hasattr(config, 'percentual_cuidados_igreja') and (config.percentual_cuidados_igreja is None or config.percentual_cuidados_igreja == 0):
                    config.percentual_cuidados_igreja = 40.0
                    valores_atualizados.append('percentual_cuidados_igreja = 40%')
                
                if hasattr(config, 'exibir_indicador_distribuicao') and config.exibir_indicador_distribuicao is None:
                    config.exibir_indicador_distribuicao = True
                    valores_atualizados.append('exibir_indicador_distribuicao = True')
                
                if valores_atualizados:
                    db.session.commit()
                    print("\n✅ Valores atualizados:")
                    for valor in valores_atualizados:
                        print(f"   • {valor}")
                else:
                    print("\n✓ Configuração já possui valores definidos")
            else:
                print("\n⚠️  Nenhuma configuração encontrada (ID=1)")
                print("   Execute o sistema para criar a configuração padrão")
            
            # Resumo final
            print("\n" + "="*70)
            print("RESUMO DA ATUALIZAÇÃO")
            print("="*70)
            print(f"✅ Campos adicionados: {campos_adicionados}")
            print(f"✓  Campos já existentes: {campos_ja_existentes}")
            print(f"📊 Total de novos campos: {len(novos_campos)}")
            
            print("\n" + "="*70)
            print("INDICADORES DE DISTRIBUIÇÃO CONFIGURADOS COM SUCESSO!")
            print("="*70)
            print("\n📌 Próximos passos:")
            print("   1. O dashboard agora mostrará os indicadores de distribuição")
            print("   2. Acesse as configurações para ajustar o percentual de Prebenda")
            print("   3. O sistema alertará se a distribuição não estiver adequada")
            
            print("\n💡 Distribuição padrão configurada:")
            print("   • 30% - Administrativo Sede")
            print("   • 30% - Prebenda Pastoral (ajustável entre 0% e 30%)")
            print("   • 40% - Cuidados da Igreja")
            print("\n")
            
        except Exception as e:
            print(f"\n❌ ERRO GERAL: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    adicionar_campos_indicadores()
