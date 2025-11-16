#!/usr/bin/env python3
"""
Script para testar os novos módulos de Secretaria
Cria dados de exemplo para Atas e Inventário
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensoes import db
from app.secretaria.atas.atas_model import Ata
from app.secretaria.inventario.inventario_model import ItemInventario
from datetime import datetime, date
from decimal import Decimal

def criar_dados_exemplo():
    """Cria dados de exemplo para teste"""
    
    app = create_app()
    
    with app.app_context():
        # Criar tabelas
        db.create_all()
        
        # Limpar dados existentes (cuidado em produção!)
        Ata.query.delete()
        ItemInventario.query.delete()
        
        print("🗃️ Criando dados de exemplo...")
        
        # ATAS DE REUNIÃO
        print("\n📋 Criando Atas de Reunião...")
        
        atas_exemplo = [
            {
                'titulo': 'Reunião Ordinária de Diretoria - Janeiro 2025',
                'data': date(2025, 1, 15),
                'local': 'Sala de Reuniões do Templo',
                'responsavel': 'Pastor João Silva',
                'descricao': '''Aos quinze dias do mês de janeiro de dois mil e vinte e cinco, às 19h30min, reuniu-se a Diretoria da Igreja OBPC para tratar dos seguintes assuntos:

1. ABERTURA E ORAÇÃO
O Pastor João Silva abriu a reunião com oração, agradecendo a Deus pela oportunidade de servir.

2. RELATÓRIO FINANCEIRO
O tesoureiro Maria Santos apresentou o relatório financeiro do mês anterior, demonstrando:
- Receitas: R$ 15.350,00
- Despesas: R$ 12.890,00
- Saldo: R$ 2.460,00

3. PROJETOS EM ANDAMENTO
Foi discutido o andamento da reforma do salão principal:
- Orçamento aprovado: R$ 25.000,00
- Valor já gasto: R$ 8.500,00
- Previsão de conclusão: março/2025

4. PRÓXIMOS EVENTOS
Foram definidas as datas dos próximos eventos:
- Retiro da juventude: 20-22/02/2025
- Festa da família: 15/03/2025
- Campanha de páscoa: 30/03 a 20/04/2025

5. DECISÕES TOMADAS
Por unanimidade foi decidido:
- Aprovar a compra de novo equipamento de som
- Autorizar a reforma do banheiro feminino
- Criar comissão para organizar a festa da família

Nada mais havendo a tratar, a reunião foi encerrada às 21h15min com oração do Pastor João Silva.'''
            },
            {
                'titulo': 'Assembleia Geral Extraordinária',
                'data': date(2025, 2, 10),
                'local': 'Salão Principal',
                'responsavel': 'Pastor João Silva',
                'descricao': '''Assembleia realizada para tratar de assuntos específicos relacionados à aquisição de novo terreno para construção de anexo.

PAUTA:
1. Apresentação da proposta de terreno
2. Análise financeira do investimento  
3. Votação da proposta
4. Definição de forma de pagamento

DECISÕES:
- Aprovada por maioria (85%) a aquisição do terreno
- Valor: R$ 120.000,00
- Forma de pagamento: entrada + 24 parcelas
- Criação de comissão de obras

A assembleia contou com 127 membros presentes.'''
            },
            {
                'titulo': 'Reunião do Conselho de Obreiros',
                'data': date(2025, 3, 5),
                'local': 'Templo Central',
                'responsavel': 'Obreiro Paulo Mendes',
                'descricao': '''Reunião mensal do conselho de obreiros para alinhamento das atividades ministeriais e discussão de questões pastorais.

Participantes: 12 obreiros
Duração: 2h30min

Principais pontos discutidos:
- Escalas de pregação
- Visitação aos enfermos
- Aconselhamento matrimonial
- Programa de discipulado
- Organização dos cultos especiais'''
            }
        ]
        
        for ata_data in atas_exemplo:
            ata = Ata(**ata_data)
            db.session.add(ata)
            print(f"   ✅ Ata criada: {ata.titulo}")
        
        # INVENTÁRIO PATRIMONIAL
        print("\n📦 Criando Inventário Patrimonial...")
        
        itens_exemplo = [
            # Móveis e Utensílios
            {
                'codigo': 'MOV001',
                'nome': 'Mesa de Escritório em Madeira',
                'categoria': 'Móveis e Utensílios',
                'descricao': 'Mesa de escritório em madeira maciça, 1,20m x 0,80m, cor mogno, com 3 gavetas.',
                'valor_aquisicao': Decimal('850.00'),
                'data_aquisicao': date(2023, 5, 15),
                'estado_conservacao': 'Bom',
                'localizacao': 'Secretaria',
                'responsavel': 'Maria Santos',
                'observacoes': 'Comprada na Móveis São João. Nota fiscal arquivada.'
            },
            {
                'codigo': 'MOV002',
                'nome': 'Cadeiras Plásticas Brancas (lote 50 unidades)',
                'categoria': 'Móveis e Utensílios',
                'descricao': 'Conjunto de 50 cadeiras plásticas modelo bistro, cor branca, marca Tramontina.',
                'valor_aquisicao': Decimal('1250.00'),
                'data_aquisicao': date(2024, 1, 20),
                'estado_conservacao': 'Excelente',
                'localizacao': 'Salão Principal',
                'responsavel': 'José Costa',
                'observacoes': 'Utilizadas em eventos especiais. Empilháveis.'
            },
            
            # Equipamentos de Som e Imagem
            {
                'codigo': 'SOM001',
                'nome': 'Mesa de Som Digital Yamaha MG16XU',
                'categoria': 'Equipamentos de Som e Imagem',
                'descricao': 'Mesa de som digital 16 canais com efeitos built-in, USB e compressor.',
                'valor_aquisicao': Decimal('2850.00'),
                'data_aquisicao': date(2024, 8, 10),
                'estado_conservacao': 'Excelente',
                'localizacao': 'Cabine de Som',
                'responsavel': 'Carlos Música',
                'observacoes': 'Equipamento principal do sistema de som. Manual e garantia disponíveis.'
            },
            {
                'codigo': 'SOM002',
                'nome': 'Microfone Shure SM58 (par)',
                'categoria': 'Equipamentos de Som e Imagem',
                'descricao': 'Par de microfones dinâmicos cardióides profissionais, modelo SM58.',
                'valor_aquisicao': Decimal('980.00'),
                'data_aquisicao': date(2024, 6, 5),
                'estado_conservacao': 'Bom',
                'localizacao': 'Cabine de Som',
                'responsavel': 'Carlos Música',
                'observacoes': 'Utilizados nos cultos e eventos. Necessário cabo XLR.'
            },
            
            # Instrumentos Musicais
            {
                'codigo': 'INS001',
                'nome': 'Piano Digital Yamaha P-125',
                'categoria': 'Instrumentos Musicais',
                'descricao': 'Piano digital 88 teclas com peso, som GHS, 24 voices, metrônomo.',
                'valor_aquisicao': Decimal('3200.00'),
                'data_aquisicao': date(2023, 12, 15),
                'estado_conservacao': 'Excelente',
                'localizacao': 'Altar Principal',
                'responsavel': 'Ana Pianista',
                'observacoes': 'Instrumento principal dos cultos. Possui pedal sustain e estante.'
            },
            {
                'codigo': 'INS002',
                'nome': 'Violão Folk Takamine GD11M',
                'categoria': 'Instrumentos Musicais',
                'descricao': 'Violão folk acústico, tampo maciço, cordas de aço, cor natural.',
                'valor_aquisicao': Decimal('650.00'),
                'data_aquisicao': date(2024, 3, 22),
                'estado_conservacao': 'Bom',
                'localizacao': 'Altar Principal',
                'responsavel': 'Pedro Violão',
                'observacoes': 'Utilizado nos louvores. Possui capa e palhetas.'
            },
            
            # Equipamentos de Informática
            {
                'codigo': 'INF001',
                'nome': 'Notebook Dell Inspiron 15 3000',
                'categoria': 'Equipamentos de Informática',
                'descricao': 'Notebook Intel Core i5, 8GB RAM, 256GB SSD, Windows 11, tela 15.6".',
                'valor_aquisicao': Decimal('2400.00'),
                'data_aquisicao': date(2024, 2, 8),
                'estado_conservacao': 'Bom',
                'localizacao': 'Secretaria',
                'responsavel': 'Maria Santos',
                'observacoes': 'Utilizado para atividades administrativas e apresentações.'
            },
            {
                'codigo': 'INF002',
                'nome': 'Projetor Epson PowerLite S41+',
                'categoria': 'Equipamentos de Informática',
                'descricao': 'Projetor SVGA 3300 lumens, entrada HDMI/VGA, controle remoto.',
                'valor_aquisicao': Decimal('1850.00'),
                'data_aquisicao': date(2023, 9, 30),
                'estado_conservacao': 'Regular',
                'localizacao': 'Salão Principal',
                'responsavel': 'José Costa',
                'observacoes': 'Lâmpada substituída em jan/2025. Possui cabo HDMI 10m.'
            },
            
            # Eletrodomésticos
            {
                'codigo': 'ELE001',
                'nome': 'Geladeira Consul Frost Free 405L',
                'categoria': 'Eletrodomésticos',
                'descricao': 'Refrigerador duplex frost free, cor branca, 405 litros, classe A.',
                'valor_aquisicao': Decimal('1680.00'),
                'data_aquisicao': date(2024, 4, 12),
                'estado_conservacao': 'Excelente',
                'localizacao': 'Cozinha',
                'responsavel': 'Lucia Cozinha',
                'observacoes': 'Utilizada para eventos e refeições. Garantia até abr/2026.'
            },
            {
                'codigo': 'ELE002',
                'nome': 'Fogão Industrial 6 Bocas Dako',
                'categoria': 'Eletrodomésticos',
                'descricao': 'Fogão industrial 6 bocas, forno grande, queimadores duplos, inox.',
                'valor_aquisicao': Decimal('1250.00'),
                'data_aquisicao': date(2023, 11, 8),
                'estado_conservacao': 'Bom',
                'localizacao': 'Cozinha',
                'responsavel': 'Lucia Cozinha',
                'observacoes': 'Manutenção realizada em dez/2024. Gás por botijão P45.'
            }
        ]
        
        for item_data in itens_exemplo:
            item = ItemInventario(**item_data)
            db.session.add(item)
            print(f"   ✅ Item criado: {item.codigo} - {item.nome}")
        
        # Commit das alterações
        db.session.commit()
        
        # Exibir estatísticas
        total_atas = Ata.query.count()
        total_itens = ItemInventario.query.count()
        valor_total = db.session.query(db.func.sum(ItemInventario.valor_aquisicao)).scalar() or 0
        
        print(f"\n✨ Dados de exemplo criados com sucesso!")
        print(f"   📋 Atas de Reunião: {total_atas}")
        print(f"   📦 Itens do Inventário: {total_itens}")
        print(f"   💰 Valor Total do Patrimônio: R$ {valor_total:.2f}")
        print(f"\n🚀 Sistema pronto para uso!")
        print(f"   🌐 Acesse: http://127.0.0.1:5000")
        print(f"   🔗 Atas: http://127.0.0.1:5000/secretaria/atas")
        print(f"   🔗 Inventário: http://127.0.0.1:5000/secretaria/inventario")

if __name__ == '__main__':
    criar_dados_exemplo()