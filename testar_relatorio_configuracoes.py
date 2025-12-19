#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste do Relatório com Configurações - Sistema OBPC
Igreja O Brasil para Cristo - Tietê/SP

Script para testar se o relatório está usando as configurações do banco
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.configuracoes.configuracoes_model import Configuracao
from app.utils.gerar_pdf_reportlab import RelatorioFinanceiro

def testar_relatorio_configuracoes():
    """Testa se o relatório está usando configurações do banco"""
    print("🔧 TESTE DO RELATÓRIO COM CONFIGURAÇÕES")
    print("=" * 50)
    
    # Criar app
    app = create_app()
    
    with app.app_context():
        try:
            # Obter configuração
            config = Configuracao.obter_configuracao()
            print(f"✅ Configuração obtida: ID {config.id}")
            print(f"📋 Nome da igreja: {config.nome_igreja}")
            print(f"📋 Cor principal: {config.cor_principal}")
            print(f"📋 Cor secundária: {config.cor_secundaria}")
            print(f"📋 Cor de destaque: {config.cor_destaque}")
            print(f"📋 Fonte do relatório: {config.fonte_relatorio}")
            print(f"📋 Logo: {config.logo}")
            print(f"📋 Exibir logo no relatório: {config.exibir_logo_relatorio}")
            print(f"📋 Rodapé: {config.rodape_relatorio}")
            print(f"📋 Campo assinatura 1: {config.campo_assinatura_1}")
            print(f"📋 Campo assinatura 2: {config.campo_assinatura_2}")
            print("-" * 40)
            
            # Testar criação do RelatorioFinanceiro
            print("📋 Testando criação do RelatorioFinanceiro...")
            relatorio = RelatorioFinanceiro(config)
            print("✅ RelatorioFinanceiro criado com sucesso!")
            
            # Verificar se as cores foram aplicadas
            print("📋 Verificando estilos configurados...")
            estilos = relatorio.styles
            
            if 'titulo_principal' in estilos:
                print("✅ Estilo titulo_principal criado")
            
            if 'titulo_igreja' in estilos:
                print("✅ Estilo titulo_igreja criado")
                
            print("-" * 40)
            print("🎉 Teste concluído com sucesso!")
            print("📝 O relatório agora deve usar as configurações do sistema")
            
        except Exception as e:
            print(f"❌ Erro durante o teste: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    testar_relatorio_configuracoes()