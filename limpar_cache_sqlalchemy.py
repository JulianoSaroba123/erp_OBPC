#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpar cache SQLAlchemy e testar o modelo atualizado
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🧹 LIMPANDO CACHE SQLALCHEMY")
    print("=" * 40)
    
    try:
        # Importar e criar app
        from app import create_app, db
        from app.midia.midia_model import Certificado
        
        app = create_app()
        
        with app.app_context():
            print("🔄 Forçando refresh do metadata...")
            
            # Limpar metadata cache
            db.metadata.clear()
            
            # Refletir estrutura atual do banco
            db.metadata.reflect(bind=db.engine)
            
            print("📊 Testando consulta de certificados...")
            
            # Testar consulta básica
            certificados = db.session.execute(
                db.text("SELECT id, nome_pessoa, tipo_certificado, filiacao FROM certificados LIMIT 3")
            ).fetchall()
            
            print(f"✅ Encontrados {len(certificados)} certificados:")
            for cert in certificados:
                print(f"  - {cert[1]} ({cert[2]})")
                if cert[3]:
                    print(f"    Filiação: {cert[3]}")
            
            print("\n🧪 Testando modelo SQLAlchemy...")
            
            # Testar o modelo diretamente
            try:
                certificados_orm = Certificado.query.limit(3).all()
                print(f"✅ ORM funcionando! {len(certificados_orm)} certificados encontrados")
                
                for cert in certificados_orm:
                    print(f"  - {cert.nome_pessoa} ({cert.tipo_certificado})")
                    if hasattr(cert, 'filiacao') and cert.filiacao:
                        print(f"    Filiação: {cert.filiacao}")
                        
            except Exception as e:
                print(f"❌ Erro no ORM: {str(e)}")
                
                # Se houver erro, vamos forçar recriação das tabelas
                print("🔄 Tentando recriar tabelas...")
                
                # Dropar e recriar apenas a tabela certificados
                db.session.execute(db.text("DROP TABLE IF EXISTS certificados_backup"))
                db.session.execute(db.text("""
                    CREATE TABLE certificados_backup AS 
                    SELECT * FROM certificados
                """))
                
                # Recriar com estrutura correta
                db.drop_all(tables=[Certificado.__table__])
                db.create_all(tables=[Certificado.__table__])
                
                # Restaurar dados
                db.session.execute(db.text("""
                    INSERT INTO certificados 
                    SELECT * FROM certificados_backup
                """))
                
                db.session.execute(db.text("DROP TABLE certificados_backup"))
                db.session.commit()
                
                print("✅ Tabelas recriadas com sucesso!")
                
                # Testar novamente
                certificados_orm = Certificado.query.limit(3).all()
                print(f"✅ Agora funcionando! {len(certificados_orm)} certificados")
                
    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()