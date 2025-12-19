#!/usr/bin/env python3
"""
Script para testar a geração de PDF das atas
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.secretaria.atas.atas_model import Ata
from datetime import date

def criar_ata_teste():
    """Cria uma ata de teste para testar o PDF"""
    app = create_app()
    
    with app.app_context():
        # Verificar se já existe uma ata de teste
        ata_existente = Ata.query.filter_by(titulo='Ata de Teste - PDF').first()
        
        if ata_existente:
            print(f"✅ Ata de teste já existe (ID: {ata_existente.id})")
            return ata_existente.id
        
        # Criar nova ata de teste
        ata_teste = Ata(
            titulo='Ata de Teste - PDF',
            data=date.today(),
            local='Sede da Igreja OBPC',
            responsavel='Pastor João Silva',
            descricao='''
1. ABERTURA
A reunião foi aberta às 19h30 com oração do Pastor João Silva.

2. PRESENTES
Estiveram presentes:
- Pastor João Silva (Dirigente)
- Maria Santos (Tesoureira)
- José da Silva (Diácono)
- Ana Costa (Secretária)

3. PAUTA
3.1. Análise do relatório financeiro do mês
3.2. Planejamento dos eventos de fim de ano
3.3. Aprovação de reformas no templo

4. DECISÕES TOMADAS
- Aprovado o relatório financeiro apresentado pela tesoureira
- Definido o cronograma dos eventos natalinos
- Autorizada a reforma do sistema elétrico

5. ENCERRAMENTO
A reunião foi encerrada às 21h00 com oração de agradecimento.
            '''
        )
        
        db.session.add(ata_teste)
        db.session.commit()
        
        print(f"✅ Ata de teste criada com sucesso! (ID: {ata_teste.id})")
        print(f"📄 Título: {ata_teste.titulo}")
        print(f"📅 Data: {ata_teste.data}")
        
        return ata_teste.id

if __name__ == "__main__":
    print("🧪 TESTE: Criação de Ata para Testar PDF")
    print("=" * 50)
    
    ata_id = criar_ata_teste()
    
    print("\n" + "=" * 50)
    print("🎯 COMO TESTAR:")
    print(f"1. Acesse: http://127.0.0.1:5000")
    print(f"2. Faça login: admin@obpc.com / 123456")
    print(f"3. Vá em: Secretaria > Atas de Reunião")
    print(f"4. Encontre a ata 'Ata de Teste - PDF'")
    print(f"5. Clique no botão PDF (ícone vermelho)")
    print(f"6. O PDF deve ser gerado com ReportLab!")
    print("=" * 50)