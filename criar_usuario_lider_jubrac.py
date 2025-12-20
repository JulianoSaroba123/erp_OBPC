"""
Script de exemplo para criar um usuário Líder de Departamento
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensoes import db
from app.usuario.usuario_model import Usuario
from app.departamentos.departamentos_model import Departamento

def criar_lider_jubrac():
    """Cria um usuário líder do departamento Jubrac"""
    app = create_app()
    
    with app.app_context():
        try:
            # Buscar ou criar o departamento Jubrac
            jubrac = Departamento.query.filter_by(nome='Jubrac').first()
            
            if not jubrac:
                print("⚠️ Departamento 'Jubrac' não encontrado!")
                print("Criando departamento Jubrac...")
                jubrac = Departamento(
                    nome='Jubrac',
                    lider='Nome do Líder',
                    descricao='Juventude Batista Renovada e Atuante em Cristo',
                    status='Ativo'
                )
                db.session.add(jubrac)
                db.session.commit()
                print(f"✅ Departamento Jubrac criado com ID {jubrac.id}")
            else:
                print(f"✅ Departamento Jubrac encontrado - ID: {jubrac.id}")
            
            # Verificar se já existe usuário para este departamento
            usuario_existente = Usuario.query.filter_by(
                nivel_acesso='lider_departamento',
                departamento_id=jubrac.id
            ).first()
            
            if usuario_existente:
                print(f"⚠️ Já existe um líder para o departamento Jubrac: {usuario_existente.nome}")
                return
            
            # Criar o usuário líder
            print("\n📝 Criando usuário líder do Jubrac...")
            
            # Exemplo de dados - ALTERE CONFORME NECESSÁRIO
            lider = Usuario(
                nome='Líder Jubrac',
                email='lider.jubrac@obpc.com',
                nivel_acesso='lider_departamento',
                departamento_id=jubrac.id,
                ativo=True
            )
            lider.set_senha('senha123')  # ALTERE A SENHA!
            
            db.session.add(lider)
            db.session.commit()
            
            print(f"\n🎯 USUÁRIO LÍDER CRIADO COM SUCESSO!")
            print(f"Nome: {lider.nome}")
            print(f"Email: {lider.email}")
            print(f"Nível: {lider.get_nome_nivel()}")
            print(f"Departamento: {jubrac.nome} (ID: {jubrac.id})")
            print(f"\n⚠️ IMPORTANTE: Altere a senha após o primeiro login!")
            print(f"\nAo fazer login, este usuário verá apenas o departamento {jubrac.nome}")
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    criar_lider_jubrac()
