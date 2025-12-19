#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar certificados de exemplo com gêneros e testar a lista
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🎨 CRIANDO CERTIFICADOS DE EXEMPLO COM GÊNEROS")
    print("=" * 60)
    
    try:
        from app import create_app, db
        from app.midia.midia_model import Certificado
        from datetime import datetime, date
        
        app = create_app()
        
        with app.app_context():
            print("📊 Verificando certificados existentes...")
            
            # Contar certificados atuais
            total_atual = Certificado.query.count()
            print(f"📈 Certificados atuais: {total_atual}")
            
            # Verificar se já tem exemplos de gênero
            com_genero = Certificado.query.filter(Certificado.genero.isnot(None)).filter(Certificado.genero != '').count()
            print(f"👥 Com gênero definido: {com_genero}")
            
            if com_genero < 3:
                print("\n📝 Criando certificados de exemplo...")
                
                # Certificado masculino
                cert_masculino = Certificado(
                    nome_pessoa="Pedro Henrique Costa Silva",
                    tipo_certificado="Apresentação",
                    genero="Masculino",
                    data_evento=date(2025, 10, 15),
                    pastor_responsavel="Pastor João Carlos",
                    local_evento="Igreja OBPC - Tietê/SP",
                    filiacao="Carlos Alberto Costa e Maria Helena Silva Costa",
                    padrinhos="José Roberto Santos e Ana Carolina Santos",
                    numero_certificado="APRES-M-2025-001",
                    observacoes="Apresentação especial - Tema azul masculino"
                )
                
                # Certificado feminino
                cert_feminino = Certificado(
                    nome_pessoa="Sofia Isabella Mendes Oliveira",
                    tipo_certificado="Apresentação", 
                    genero="Feminino",
                    data_evento=date(2025, 11, 2),
                    pastor_responsavel="Pastor João Carlos",
                    local_evento="Igreja OBPC - Tietê/SP",
                    filiacao="Roberto Mendes e Carolina Isabella Oliveira",
                    padrinhos="Paulo Eduardo Lima e Mariana Cristina Lima",
                    numero_certificado="APRES-F-2025-001",
                    observacoes="Apresentação especial - Tema rosa feminino"
                )
                
                # Certificado neutro
                cert_neutro = Certificado(
                    nome_pessoa="Alex Jordan Santos Pereira",
                    tipo_certificado="Apresentação",
                    genero="",
                    data_evento=date(2025, 10, 28),
                    pastor_responsavel="Pastor João Carlos", 
                    local_evento="Igreja OBPC - Tietê/SP",
                    filiacao="Diego Santos e Patricia Morgan Pereira",
                    padrinhos="Lucas Henrique Mendes e Julia Cristina Mendes",
                    numero_certificado="APRES-N-2025-001",
                    observacoes="Apresentação especial - Tema neutro"
                )
                
                # Certificado de batismo exemplo
                cert_batismo = Certificado(
                    nome_pessoa="Ana Beatriz Rodrigues Santos",
                    tipo_certificado="Batismo",
                    genero="Feminino",
                    data_evento=date(2025, 9, 20),
                    pastor_responsavel="Pastor João Carlos",
                    local_evento="Igreja OBPC - Tietê/SP",
                    filiacao="Fernando Rodrigues e Beatriz Santos",
                    padrinhos="Marcos Antônio Silva e Fernanda Silva",
                    numero_certificado="BAT-F-2025-001",
                    observacoes="Batismo por imersão"
                )
                
                # Adicionar ao banco
                certificados_novos = [cert_masculino, cert_feminino, cert_neutro, cert_batismo]
                db.session.add_all(certificados_novos)
                db.session.commit()
                
                print("✅ Certificados de exemplo criados!")
                
                for cert in certificados_novos:
                    print(f"  - {cert.nome_pessoa} ({cert.tipo_certificado}, {cert.genero or 'Neutro'})")
            
            # Verificar total final
            total_final = Certificado.query.count()
            print(f"\n📊 Total final de certificados: {total_final}")
            
            # Listar todos os certificados
            print("\n📋 LISTA COMPLETA DE CERTIFICADOS:")
            certificados = Certificado.query.order_by(Certificado.data_evento.desc()).all()
            
            for i, cert in enumerate(certificados, 1):
                cor_emoji = ""
                if cert.genero == "Masculino":
                    cor_emoji = "🔵"
                elif cert.genero == "Feminino":
                    cor_emoji = "🌸"
                else:
                    cor_emoji = "💜"
                
                print(f"{i:2d}. {cor_emoji} {cert.nome_pessoa}")
                print(f"     Tipo: {cert.tipo_certificado} | Gênero: {cert.genero or 'Não informado'}")
                print(f"     Data: {cert.data_evento.strftime('%d/%m/%Y') if cert.data_evento else 'N/A'}")
                if cert.filiacao:
                    print(f"     👨‍👩‍👧‍👦 Filiação: {cert.filiacao}")
                if cert.padrinhos:
                    print(f"     🤝 Padrinhos: {cert.padrinhos}")
                print(f"     🔗 URL: /midia/certificados/visualizar/{cert.id}/alegre")
                print()
            
            print("🎯 RESUMO POR GÊNERO:")
            masculinos = Certificado.query.filter_by(genero="Masculino").count()
            femininos = Certificado.query.filter_by(genero="Feminino").count()
            neutros = Certificado.query.filter(
                (Certificado.genero == "") | (Certificado.genero.is_(None))
            ).count()
            
            print(f"🔵 Masculinos: {masculinos} (Tema azul)")
            print(f"🌸 Femininos: {femininos} (Tema rosa)")
            print(f"💜 Neutros: {neutros} (Tema roxo)")
            
            print("\n✅ CERTIFICADOS PRONTOS PARA TESTE!")
            print("🚀 Acesse: http://127.0.0.1:5000/midia/certificados")
            print("📝 Use o dropdown para ver os templates coloridos!")
                
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()