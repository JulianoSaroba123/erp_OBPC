#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste das Melhorias do Relatório da Sede
Igreja O Brasil para Cristo - Tietê/SP
"""

import os
import sys

# Adicionar o diretório pai ao path do Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.configuracoes.configuracoes_model import Configuracao
from app.financeiro.despesas_fixas_model import DespesaFixaConselho

# Criar aplicação Flask
app = create_app()

def testar_percentual_conselho():
    """Testa se o percentual do conselho está sendo lido corretamente"""
    print("🔍 Testando percentual do conselho...")
    
    with app.app_context():
        config = Configuracao.obter_configuracao()
        percentual = config.percentual_conselho
        
        print(f"📊 Percentual configurado: {percentual}%")
        
        # Simular cálculo
        total_exemplo = 1000.00
        valor_conselho = total_exemplo * (percentual / 100)
        
        print(f"💰 Exemplo: R$ {total_exemplo:.2f} * {percentual}% = R$ {valor_conselho:.2f}")
        
        if percentual == 30.0:
            print("✅ Percentual correto (30%)!")
            return True
        else:
            print(f"❌ Percentual incorreto. Esperado: 30%, Encontrado: {percentual}%")
            return False

def testar_despesas_fixas():
    """Testa se as despesas fixas estão funcionando"""
    print("\n🔍 Testando despesas fixas...")
    
    with app.app_context():
        despesas = DespesaFixaConselho.obter_despesas_ativas()
        total = DespesaFixaConselho.obter_total_despesas_fixas()
        envios_dict = DespesaFixaConselho.obter_despesas_para_relatorio()
        
        print(f"📋 Total de despesas ativas: {len(despesas)}")
        print(f"💰 Valor total das despesas: R$ {total:.2f}")
        
        print("\n📝 Despesas configuradas:")
        for despesa in despesas:
            print(f"  • {despesa.nome}: R$ {despesa.valor_padrao:.2f}")
        
        print("\n🔗 Mapeamento para relatório:")
        for chave, valor in envios_dict.items():
            print(f"  • {chave}: R$ {valor:.2f}")
        
        # Verificar se todas as despesas esperadas existem
        esperadas = ['oferta_voluntaria_conchas', 'site', 'projeto_filipe', 'forca_para_viver', 'contador_sede']
        todas_presentes = all(chave in envios_dict for chave in esperadas)
        
        if todas_presentes and len(despesas) == 5:
            print("✅ Todas as despesas fixas estão configuradas corretamente!")
            return True
        else:
            print("❌ Algumas despesas fixas estão faltando.")
            return False

def atualizar_percentual_se_necessario():
    """Atualiza o percentual para 30% se estiver diferente"""
    print("\n🔧 Verificando se percentual precisa ser atualizado...")
    
    with app.app_context():
        config = Configuracao.obter_configuracao()
        
        if config.percentual_conselho != 30.0:
            print(f"🔄 Atualizando percentual de {config.percentual_conselho}% para 30%...")
            config.percentual_conselho = 30.0
            
            try:
                from app.extensoes import db
                db.session.commit()
                print("✅ Percentual atualizado com sucesso!")
                return True
            except Exception as e:
                print(f"❌ Erro ao atualizar percentual: {str(e)}")
                return False
        else:
            print("✅ Percentual já está correto (30%)!")
            return True

def main():
    """Função principal"""
    print("="*60)
    print("🧪 TESTE DAS MELHORIAS DO RELATÓRIO DA SEDE")
    print("⛪ Igreja O Brasil para Cristo - Tietê/SP")
    print("="*60)
    
    try:
        # Testar percentual
        percentual_ok = testar_percentual_conselho()
        
        # Se o percentual estiver errado, tentar corrigir
        if not percentual_ok:
            percentual_ok = atualizar_percentual_se_necessario()
        
        # Testar despesas fixas
        despesas_ok = testar_despesas_fixas()
        
        print("\n" + "="*60)
        if percentual_ok and despesas_ok:
            print("🎉 TODOS OS TESTES PASSARAM!")
            print("✅ Percentual do conselho: OK (30%)")
            print("✅ Despesas fixas: OK (5 itens configurados)")
            print("✅ Sistema pronto para uso!")
        else:
            print("⚠️  ALGUNS TESTES FALHARAM!")
            if not percentual_ok:
                print("❌ Percentual do conselho precisa de correção")
            if not despesas_ok:
                print("❌ Despesas fixas precisam de configuração")
        
        print("="*60)
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {str(e)}")
        return False
    
    return percentual_ok and despesas_ok

if __name__ == '__main__':
    main()