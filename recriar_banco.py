"""
Script para recriar o banco de dados do zero
"""
from app import create_app
from app.extensoes import db
import os

def recriar_banco():
    app = create_app()
    
    # Remover banco antigo se existir
    db_path = os.path.join(os.getcwd(), 'instance', 'igreja.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Banco antigo removido: {db_path}")
    
    # Criar diretório instance se não existir
    instance_dir = os.path.join(os.getcwd(), 'instance')
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
    
    with app.app_context():
        # Criar todas as tabelas
        db.create_all()
        print("✓ Novo banco criado!")
        
        # Criar usuário admin padrão
        from app.usuario.usuario_model import Usuario, NivelAcesso
        
        admin = Usuario(
            nome="Administrador OBPC",
            email="admin@obpc.com",
            nivel_acesso=NivelAcesso.MASTER.value,
            ativo=True
        )
        admin.set_senha("admin123")
        
        db.session.add(admin)
        db.session.commit()
        
        print("✓ Usuário admin criado!")
        print("Email: admin@obpc.com")
        print("Senha: admin123")

if __name__ == "__main__":
    recriar_banco()