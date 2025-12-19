#!/usr/bin/env python3
"""
Script para adicionar a categoria 'OUTRAS OFERTAS' no sistema financeiro
Igreja O Brasil para Cristo - Sistema Administrativo OBPC
"""

from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento

def atualizar_categoria_outras_ofertas():
    """Atualiza lançamentos existentes que podem ser categorizados como 'OUTRAS OFERTAS'"""
    
    app = create_app()
    
    with app.app_context():
        print("🔄 Iniciando verificação para categoria 'OUTRAS OFERTAS'...")
        
        # Buscar lançamentos de OFERTA que podem ser reclassificados
        # Baseado na descrição - se tiver palavras-chave específicas
        palavras_chave_outras_ofertas = [
            'doação',
            'doacão', 
            'projeto',
            'ajuda',
            'contribuição especial',
            'contribuicao especial',
            'evento especial',
            'venda',
            'bazar',
            'festa',
            'campanha',
            'externa'
        ]
        
        contador_atualizacoes = 0
        
        # Buscar lançamentos de entrada com categoria OFERTA
        ofertas = Lancamento.query.filter(
            Lancamento.tipo == 'Entrada',
            Lancamento.categoria.ilike('OFERTA'),
            ~Lancamento.categoria.ilike('%OMN%')  # Não pegar OFERTA OMN
        ).all()
        
        print(f"Encontrados {len(ofertas)} lançamentos de OFERTA para análise...")
        
        for oferta in ofertas:
            descricao_original = oferta.descricao or ''
            descricao_lower = descricao_original.lower()
            
            # Verificar se a descrição contém palavras-chave para "OUTRAS OFERTAS"
            eh_outras_ofertas = any(palavra in descricao_lower for palavra in palavras_chave_outras_ofertas)
            
            if eh_outras_ofertas:
                print(f"\n📝 Reclassificando: {oferta.data.strftime('%Y-%m-%d')}")
                print(f"   Descrição: '{descricao_original}'")
                print(f"   Valor: R$ {oferta.valor:.2f}")
                print(f"   Categoria: OFERTA → OUTRAS OFERTAS")
                
                oferta.categoria = 'OUTRAS OFERTAS'
                contador_atualizacoes += 1
        
        if contador_atualizacoes > 0:
            try:
                db.session.commit()
                print(f"\n✅ Atualizações realizadas com sucesso!")
                print(f"📊 Total de lançamentos reclassificados: {contador_atualizacoes}")
                print(f"\n💡 Informação importante:")
                print(f"   Os lançamentos categorizados como 'OUTRAS OFERTAS' NÃO entrarão")
                print(f"   no cálculo dos 30% do valor administrativo para a sede.")
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erro ao salvar no banco: {str(e)}")
        else:
            print(f"\n✅ Nenhum lançamento precisou ser reclassificado.")
            print(f"💡 A categoria 'OUTRAS OFERTAS' está disponível para novos lançamentos.")
            
        print(f"\n🎯 Como usar a nova categoria:")
        print(f"   • Para ofertas especiais (doações, projetos, vendas, eventos)")
        print(f"   • Para ofertas que NÃO devem entrar no cálculo administrativo")
        print(f"   • Descrições sugeridas: 'Doação especial', 'Projeto X', 'Venda de livros'")

if __name__ == "__main__":
    atualizar_categoria_outras_ofertas()