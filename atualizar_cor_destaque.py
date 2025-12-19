#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para Atualizar Cor de Destaque do Sistema
Igreja O Brasil para Cristo - Tietê/SP

Este script atualiza a cor de destaque padrão de amarelo para laranja vibrante
"""

import os
import sys

# Adicionar o diretório pai ao path do Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensoes import db
from app.configuracoes.configuracoes_model import Configuracao

# Criar aplicação Flask
app = create_app()

def atualizar_cor_destaque():
    """Atualiza a cor de destaque no banco de dados"""
    print("🎨 Atualizando cor de destaque do sistema...")
    
    with app.app_context():
        try:
            # Obter configuração atual
            config = Configuracao.obter_configuracao()
            
            print(f"📊 Cor atual: {config.cor_destaque}")
            
            # Atualizar para a nova cor laranja vibrante
            if config.cor_destaque != '#FF6B35':
                config.cor_destaque = '#FF6B35'
                db.session.commit()
                print(f"✅ Cor atualizada para: {config.cor_destaque}")
                print("🎉 Cor de destaque atualizada com sucesso!")
            else:
                print("✅ Cor já está atualizada!")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao atualizar cor: {str(e)}")
            db.session.rollback()
            return False

def verificar_cor_atual():
    """Verifica a cor atual configurada"""
    with app.app_context():
        config = Configuracao.obter_configuracao()
        print(f"🎨 Cor de destaque atual: {config.cor_destaque}")
        print(f"🎯 Cor principal: {config.cor_principal}")
        print(f"🌿 Cor secundária: {config.cor_secundaria}")

def main():
    """Função principal"""
    print("="*60)
    print("🎨 ATUALIZAÇÃO DA COR DE DESTAQUE")
    print("⛪ Igreja O Brasil para Cristo - Tietê/SP")
    print("="*60)
    
    print("\n📊 Verificando configurações atuais...")
    verificar_cor_atual()
    
    print("\n🔄 Aplicando nova cor de destaque...")
    if atualizar_cor_destaque():
        print("\n" + "="*60)
        print("🎉 ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        print("✅ Nova cor aplicada: #FF6B35 (Laranja Vibrante)")
        print("📱 A nova cor será aplicada:")
        print("  • Nos destaques do menu lateral")
        print("  • Nos botões de ação")
        print("  • Nos elementos de destaque")
        print("  • Nos relatórios PDF")
        print("\n💡 Reinicie o sistema para ver todas as mudanças!")
    else:
        print("❌ Falha na atualização.")

if __name__ == '__main__':
    main()