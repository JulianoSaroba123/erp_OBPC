"""
Adicionar comprovante de teste a um lançamento
"""
from app import create_app, db
from app.financeiro.financeiro_model import Lancamento

app = create_app()

with app.app_context():
    # Pegar primeiro lançamento
    lancamento = Lancamento.query.first()
    
    if lancamento:
        print(f"✅ Lançamento encontrado: ID {lancamento.id}")
        print(f"   Descrição: {lancamento.descricao}")
        
        # Adicionar caminho do comprovante
        lancamento.comprovante = '/static/uploads/comprovantes/8cad0b27f9b24658ad718e0d5ac0a324_IMG_20251106_0006.pdf'
        
        db.session.commit()
        
        print(f"\n✅ Comprovante adicionado!")
        print(f"   Arquivo: {lancamento.comprovante}")
        print(f"\n📝 Para testar:")
        print(f"   1. Acesse: http://127.0.0.1:5000/financeiro/editar/{lancamento.id}")
        print(f"   2. Role até 'Comprovante'")
        print(f"   3. Você verá o botão 'Excluir' em vermelho")
    else:
        print("❌ Nenhum lançamento encontrado no banco de dados")
