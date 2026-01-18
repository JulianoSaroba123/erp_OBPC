"""
Script COMPLETO para configurar banco de dados no Render
- Cria tabelas se não existirem
- Adiciona colunas extras na tabela membros
- Cria usuário admin se não existir
"""

import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def configurar_banco_render():
    """Configura completamente o banco de dados no Render"""
    
    print("Importando aplicacao...")
    
    try:
        from app import create_app
        from app.extensoes import db
        from sqlalchemy import inspect, text
    except Exception as e:
        print(f"Erro ao importar: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("Criando aplicacao Flask...")
    app = create_app()
    
    with app.app_context():
        try:
            # PASSO 1: Criar tabelas
            print("\n[1/3] Verificando e criando tabelas...")
            db.create_all()
            
            inspector = inspect(db.engine)
            tabelas = inspector.get_table_names()
            print(f"Total de tabelas: {len(tabelas)}")
            
            # Verificar se tabela membros existe
            if 'membros' not in tabelas:
                print("ERRO: Tabela membros nao foi criada!")
                return
            
            print("Tabela membros encontrada")
            
            # PASSO 2: Adicionar colunas extras
            print("\n[2/3] Verificando colunas da tabela membros...")
            
            colunas_existentes = {col['name'] for col in inspector.get_columns('membros')}
            print(f"Colunas atuais: {len(colunas_existentes)}")
            
            # Colunas que devem existir
            colunas_necessarias = {
                'cpf': 'VARCHAR(14)',
                'numero': 'VARCHAR(10)', 
                'bairro': 'VARCHAR(100)',
                'estado_civil': 'VARCHAR(20)',
                'curso_teologia': 'BOOLEAN DEFAULT FALSE',
                'nivel_teologia': 'VARCHAR(20)',
                'instituto': 'VARCHAR(200)',
                'deseja_servir': 'BOOLEAN DEFAULT FALSE',
                'area_servir': 'VARCHAR(200)'
            }
            
            # Adiciona colunas faltantes
            colunas_adicionadas = 0
            for coluna, tipo in colunas_necessarias.items():
                if coluna not in colunas_existentes:
                    try:
                        sql = text(f"ALTER TABLE membros ADD COLUMN {coluna} {tipo}")
                        db.session.execute(sql)
                        db.session.commit()
                        print(f"   + Coluna '{coluna}' adicionada")
                        colunas_adicionadas += 1
                    except Exception as e:
                        print(f"   ! Erro ao adicionar '{coluna}': {e}")
                        db.session.rollback()
            
            if colunas_adicionadas == 0:
                print("   Todas as colunas ja existem")
            else:
                print(f"   Total de colunas adicionadas: {colunas_adicionadas}")
            
            # PASSO 3: Criar usuário admin
            print("\n[3/3] Verificando usuario admin...")
            
            from app.usuario.usuario_model import Usuario, NivelAcesso
            
            admin = Usuario.query.filter_by(email='admin@obpc.com').first()
            
            if not admin:
                print("Criando usuario admin...")
                admin = Usuario(
                    nome='Administrador',
                    email='admin@obpc.com',
                    perfil='Admin',
                    nivel_acesso=NivelAcesso.MASTER.value,
                    ativo=True
                )
                admin.set_senha('admin123')
                db.session.add(admin)
                db.session.commit()
                print("   Usuario admin criado!")
                print("   Email: admin@obpc.com")
                print("   Senha: admin123")
                print("   IMPORTANTE: Altere a senha apos o primeiro login!")
            else:
                print(f"   Usuario admin ja existe: {admin.email}")
            
            # RESUMO FINAL
            print("\n" + "=" * 60)
            print("CONFIGURACAO CONCLUIDA COM SUCESSO!")
            print("=" * 60)
            print(f"\nTabelas criadas: {len(tabelas)}")
            print(f"Colunas extras adicionadas: {colunas_adicionadas}")
            print("\nVoce pode agora:")
            print("1. Acessar o sistema no Render")
            print("2. Fazer login com admin@obpc.com / admin123")
            print("3. Cadastrar membros com todos os campos")
            print("=" * 60)
            
        except Exception as e:
            print(f"\nERRO ao configurar banco: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            raise

if __name__ == "__main__":
    print("=" * 60)
    print("CONFIGURACAO COMPLETA DO BANCO - RENDER")
    print("=" * 60)
    configurar_banco_render()
