"""
Teste de Login para Módulo Mídia - Sistema OBPC
"""

from app import db, create_app
from app.usuario.usuario_model import Usuario

def criar_usuario_teste():
    """Cria um usuário de teste se não existir"""
    app = create_app()
    
    with app.app_context():
        # Verificar se já existe um usuário
        usuario_existente = Usuario.query.first()
        
        if not usuario_existente:
            print("❌ Nenhum usuário encontrado! Criando usuário de teste...")
            
            # Criar usuário admin de teste
            novo_usuario = Usuario(
                nome='Administrador',
                email='admin@obpc.com',
                perfil='Pastor'
            )
            novo_usuario.set_senha('123456')
            
            db.session.add(novo_usuario)
            db.session.commit()
            
            print("✅ Usuário criado com sucesso!")
            print("👤 Nome: Administrador")
            print("📧 Email: admin@obpc.com")
            print("🔑 Password: 123456")
            
        else:
            print("✅ Usuário já existe:")
            print(f"👤 Nome: {usuario_existente.nome}")
            print(f"📧 Email: {usuario_existente.email}")
            print("🔑 Use a senha cadastrada")
        
        print("\n" + "="*50)
        print("🚀 COMO TESTAR:")
        print("1. Acesse: http://127.0.0.1:5000")
        print("2. Faça login com as credenciais acima")
        print("3. Teste: http://127.0.0.1:5000/midia/agenda")
        print("="*50)

if __name__ == '__main__':
    criar_usuario_teste()