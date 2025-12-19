#!/usr/bin/env python3
"""
Script para corrigir observações com valor "None" no banco de dados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento

def corrigir_observacoes_none():
    """Corrige observações que estão como string 'None' no banco"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Iniciando correção de observações com 'None'...")
        
        # Buscar lançamentos com observações problemáticas
        lancamentos_problematicos = Lancamento.query.filter(
            db.or_(
                Lancamento.observacoes == 'None',
                Lancamento.observacoes == 'none',
                Lancamento.observacoes == '',
                Lancamento.observacoes == ' '
            )
        ).all()
        
        if not lancamentos_problematicos:
            print("✅ Nenhum lançamento com observações problemáticas encontrado!")
            return
        
        print(f"📋 Encontrados {len(lancamentos_problematicos)} lançamentos para corrigir:")
        
        corrigidos = 0
        for lancamento in lancamentos_problematicos:
            print(f"   • ID {lancamento.id}: '{lancamento.observacoes}' → NULL")
            lancamento.observacoes = None
            corrigidos += 1
        
        try:
            db.session.commit()
            print(f"✅ {corrigidos} lançamentos corrigidos com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao salvar correções: {e}")

if __name__ == "__main__":
    corrigir_observacoes_none()