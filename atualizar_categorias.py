#!/usr/bin/env python3
"""
Script para atualizar categorias de lançamentos financeiros
Igreja O Brasil para Cristo - Sistema Administrativo OBPC
"""

from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento

def atualizar_categorias():
    """Atualiza as categorias dos lançamentos existentes para o novo padrão"""
    
    app = create_app()
    
    with app.app_context():
        print("🔄 Iniciando atualização de categorias...")
        
        # Mapeamento de categorias antigas para novas
        mapeamento_categorias = {
            # Entradas
            'dizimo': 'DÍZIMO',
            'dízimo': 'DÍZIMO',
            'dízimos': 'DÍZIMO',
            'oferta': 'OFERTA',
            'ofertas': 'OFERTA',
            'oferta alçada': 'OFERTA OMN',
            'oferta alcada': 'OFERTA OMN',
            'oferta omn': 'OFERTA OMN',
            'rendimento': 'RENDIMENTOS',
            'rendimento conta': 'RENDIMENTOS',
            'rendimentos': 'RENDIMENTOS',
            'rendimento banco': 'RENDIMENTOS',
            'rendimentos banco': 'RENDIMENTOS',
            'rendimento da conta': 'RENDIMENTOS',
            'renda conta': 'REND.CONTA',
            
            # Saídas
            'combustivel': 'COMBUSTÍVEL',
            'combustível': 'COMBUSTÍVEL',
            'gasolina': 'COMBUSTÍVEL',
            'prebenda': 'PREBENDA',
            'ajuda custo': 'AJUDA CUSTO',
            'ajuda de custo': 'AJUDA CUSTO',
            'transporte': 'TRANSP VIEX',
            'transporte viex': 'TRANSP VIEX',
            'contas': 'CONTAS',
            'conta': 'CONTAS',
            'despesa fixa': 'DESP. FIXAS',
            'despesas fixas': 'DESP. FIXAS',
            'despesa variavel': 'DESP. VARIAVEIS',
            'despesas variaveis': 'DESP. VARIAVEIS',
            'despesa variável': 'DESP. VARIAVEIS',
            'despesas variáveis': 'DESP. VARIAVEIS',
            'cartao': 'CRÉDITO CARTÃO',
            'cartão': 'CRÉDITO CARTÃO',
            'credito cartao': 'CRÉDITO CARTÃO',
            'crédito cartão': 'CRÉDITO CARTÃO',
            'desconto': 'DESC.CONTA',
            'desconto conta': 'DESC.CONTA',
            'desc conta': 'DESC.CONTA',
            'tarifa': 'DESC.CONTA',
        }
        
        # Buscar todos os lançamentos
        lancamentos = Lancamento.query.all()
        
        contador_atualizados = 0
        
        for lancamento in lancamentos:
            if lancamento.categoria:
                categoria_original = lancamento.categoria.lower().strip()
                
                # Procurar no mapeamento
                nova_categoria = mapeamento_categorias.get(categoria_original)
                
                if nova_categoria and nova_categoria != lancamento.categoria:
                    print(f"📝 Atualizando: '{lancamento.categoria}' → '{nova_categoria}'")
                    lancamento.categoria = nova_categoria
                    contador_atualizados += 1
        
        # Salvar alterações
        if contador_atualizados > 0:
            try:
                db.session.commit()
                print(f"✅ {contador_atualizados} categorias atualizadas com sucesso!")
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erro ao salvar: {e}")
        else:
            print("ℹ️  Nenhuma categoria precisou ser atualizada.")
        
        # Mostrar resumo das categorias atuais
        print("\n📊 Resumo das categorias atuais:")
        categorias_unicas = db.session.query(Lancamento.categoria, db.func.count(Lancamento.id))\
                                     .filter(Lancamento.categoria.isnot(None))\
                                     .group_by(Lancamento.categoria)\
                                     .order_by(Lancamento.categoria).all()
        
        for categoria, quantidade in categorias_unicas:
            print(f"   • {categoria}: {quantidade} lançamento(s)")
        
        print("\n🎉 Atualização concluída!")


if __name__ == "__main__":
    atualizar_categorias()