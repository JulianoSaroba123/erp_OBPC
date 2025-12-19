#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para padronizar as ofertas existentes no banco de dados
conforme a nova lógica definida
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

from app import create_app, db
from app.financeiro.financeiro_model import Lancamento
from app.config import Config

app = create_app()

with app.app_context():
    print("=== PADRONIZAÇÃO DAS OFERTAS EXISTENTES ===")
    
    # Buscar todos os lançamentos de entrada com categoria de oferta
    ofertas = Lancamento.query.filter(
        Lancamento.tipo == 'Entrada',
        Lancamento.categoria.ilike('%oferta%')
    ).all()
    
    print(f"Total de ofertas encontradas: {len(ofertas)}")
    
    contador_atualizacoes = 0
    
    for oferta in ofertas:
        categoria_original = oferta.categoria
        descricao_original = oferta.descricao or ''
        
        print(f"\nProcessando: {oferta.data.strftime('%Y-%m-%d')}")
        print(f"Categoria atual: '{categoria_original}'")
        print(f"Descrição atual: '{descricao_original}'")
        print(f"Valor: R$ {oferta.valor:.2f}")
        
        # Aplicar nova padronização
        categoria_lower = categoria_original.lower() if categoria_original else ''
        
        if 'omn' in categoria_lower:
            # OFERTA OMN - já está correto, manter como está
            print("→ OFERTA OMN - mantendo categoria e descrição")
            
        elif categoria_lower == 'oferta':
            # OFERTA regular - padronizar descrição baseado na lógica
            descricao_lower = descricao_original.lower()
            
            if not descricao_original or descricao_original.strip() == '':
                # Descrição vazia - assumir como oferta de culto
                oferta.descricao = 'Oferta'
                print("→ Atualizando descrição para: 'Oferta' (ofertório)")
                contador_atualizacoes += 1
                
            elif 'outras' in descricao_lower:
                # Já tem "outras" na descrição - padronizar
                oferta.descricao = 'Outras Ofertas'
                print("→ Atualizando descrição para: 'Outras Ofertas'")
                contador_atualizacoes += 1
                
            elif 'oferta' in descricao_lower and 'outras' not in descricao_lower:
                # Tem "oferta" mas não "outras" - padronizar como ofertório
                oferta.descricao = 'Oferta'
                print("→ Atualizando descrição para: 'Oferta' (ofertório)")
                contador_atualizacoes += 1
                
            else:
                # Descrição não padrão - perguntar ao usuário
                print(f"⚠️  Descrição não padrão: '{descricao_original}'")
                print("1 - Oferta de culto (ofertório)")
                print("2 - Outras ofertas (externas/projetos)")
                
                # Para automação, vamos assumir que descrições específicas são "outras ofertas"
                # e descrições genéricas são "ofertas de culto"
                palavras_especificas = ['doação', 'projeto', 'campanha', 'evento', 'externa', 'especial']
                
                if any(palavra in descricao_lower for palavra in palavras_especificas):
                    oferta.descricao = 'Outras Ofertas'
                    print("→ Auto-classificando como: 'Outras Ofertas' (externa)")
                    contador_atualizacoes += 1
                else:
                    oferta.descricao = 'Oferta'
                    print("→ Auto-classificando como: 'Oferta' (ofertório)")
                    contador_atualizacoes += 1
        
        print("-" * 60)
    
    # Salvar alterações
    if contador_atualizacoes > 0:
        try:
            db.session.commit()
            print(f"\n✅ Padronização concluída! {contador_atualizacoes} ofertas atualizadas.")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro ao salvar: {str(e)}")
    else:
        print(f"\n✅ Nenhuma atualização necessária. Todas as ofertas já estão padronizadas.")
    
    print(f"\n=== RESUMO DA NOVA LÓGICA ===")
    print(f"📊 Ofertas Alçadas: Categoria 'OFERTA' + Descrição 'Oferta' OU Categoria 'OFERTA OMN'")
    print(f"📊 Outras Ofertas: Categoria 'OFERTA' + Descrição 'Outras Ofertas' OU outras categorias")
    print(f"📊 Ofertas OMN: Categoria 'OFERTA OMN' (para convenção)")