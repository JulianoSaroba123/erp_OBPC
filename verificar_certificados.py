"""
Script para verificar certificados no banco
"""

from app import create_app, db
from app.midia.midia_model import Certificado

# Criar aplicação
app = create_app()

with app.app_context():
    certificados = Certificado.query.all()
    print(f"Total de certificados: {len(certificados)}")
    
    for cert in certificados:
        print(f"ID: {cert.id}, Nome: {cert.nome_pessoa}, Tipo: {cert.tipo_certificado}")