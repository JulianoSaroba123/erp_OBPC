#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.abspath('.'))

def adicionar_coluna_padrinhos():
    """Adiciona coluna padrinhos usando o contexto Flask"""
    
    print("🔄 ADICIONANDO COLUNA PADRINHOS AOS CERTIFICADOS")
    print("=" * 60)
    
    try:
        from app import create_app, db
        from app.midia.midia_model import Certificado
        
        # Criar aplicação
        app = create_app()
        
        with app.app_context():
            # Verificar se a tabela existe
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            
            if 'certificados' in inspector.get_table_names():
                print("✅ Tabela 'certificados' encontrada")
                
                # Verificar colunas atuais
                colunas = inspector.get_columns('certificados')
                nomes_colunas = [col['name'] for col in colunas]
                
                print(f"📋 Colunas atuais: {', '.join(nomes_colunas)}")
                
                if 'padrinhos' in nomes_colunas:
                    print("✅ Coluna 'padrinhos' já existe!")
                else:
                    print("🔄 Adicionando coluna 'padrinhos'...")
                    
                    # Adicionar coluna usando SQLAlchemy
                    with db.engine.connect() as conn:
                        conn.execute(text('ALTER TABLE certificados ADD COLUMN padrinhos TEXT;'))
                        conn.commit()
                    
                    print("✅ Coluna 'padrinhos' adicionada com sucesso!")
                
                # Verificar certificados existentes
                total = Certificado.query.count()
                apresentacoes = Certificado.query.filter_by(tipo_certificado='Apresentação').count()
                
                print(f"\n📊 CERTIFICADOS EXISTENTES:")
                print(f"  Total: {total}")
                print(f"  Apresentações: {apresentacoes}")
                
                print(f"\n🎉 FUNCIONALIDADE PRONTA!")
                print(f"✅ Agora você pode usar o campo 'padrinhos' nos certificados de apresentação!")
                
            else:
                print("❌ Tabela 'certificados' não encontrada!")
                
                # Criar a tabela
                print("🔄 Criando tabela 'certificados'...")
                db.create_all()
                print("✅ Tabela criada com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    adicionar_coluna_padrinhos()