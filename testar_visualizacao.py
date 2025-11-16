"""
Script para testar a visualização de certificado diretamente
"""

from app import create_app, db
from app.midia.midia_model import Certificado
from flask import render_template

# Criar aplicação
app = create_app()

with app.app_context():
    try:
        certificado = Certificado.query.get(1)
        if certificado:
            print(f"Certificado encontrado: {certificado.nome_pessoa}")
            # Tentar renderizar o template
            html = render_template('certificados/visualizar_certificado.html', certificado=certificado)
            print("Template renderizado com sucesso!")
            print(f"Tamanho do HTML: {len(html)} caracteres")
        else:
            print("Certificado não encontrado")
    except Exception as e:
        print(f"Erro: {str(e)}")
        import traceback
        traceback.print_exc()