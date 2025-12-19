from app import create_app
from app.extensoes import db
from app.usuario.usuario_model import Usuario

app = create_app()

with app.app_context():
    # Verifica se já existe um admin
    admin_existente = Usuario.query.filter_by(email="admin@obpc.com").first()
    
    if not admin_existente:
        # Cria usuário admin
        admin = Usuario(
            nome="Administrador OBPC",
            email="admin@obpc.com",
            perfil="Pastor"
        )
        admin.set_senha("123456")
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Usuário admin criado com sucesso!")
        print("📧 Email: admin@obpc.com")
        print("🔑 Senha: 123456")
    else:
        print("ℹ️ Usuário admin já existe")
        print("📧 Email: admin@obpc.com")
        print("🔑 Senha: 123456")