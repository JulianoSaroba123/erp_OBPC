#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para atualizar o banco de dados - Adicionar campo arquivo_anexo em aulas
"""

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db
from app.departamentos.departamentos_model import AulaDepartamento

def atualizar_banco_aulas():
    """Atualiza o banco de dados para incluir campo arquivo_anexo"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Atualizando banco de dados para aulas com arquivos...")
            print("=" * 60)
            
            # Verificar se a coluna já existe
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('aulas_departamento')]
            
            if 'arquivo_anexo' in columns:
                print("✅ Campo 'arquivo_anexo' já existe na tabela aulas_departamento")
                return
            
            # Adicionar a nova coluna
            print("📝 Adicionando campo 'arquivo_anexo' na tabela aulas_departamento...")
            
            with db.engine.connect() as conn:
                # SQLite - adicionar coluna
                conn.execute(db.text("""
                    ALTER TABLE aulas_departamento 
                    ADD COLUMN arquivo_anexo VARCHAR(255)
                """))
                conn.commit()
            
            print("✅ Campo 'arquivo_anexo' adicionado com sucesso!")
            
            # Verificar se existem aulas
            total_aulas = AulaDepartamento.query.count()
            print(f"📊 Total de aulas existentes: {total_aulas}")
            
            if total_aulas > 0:
                print("ℹ️  As aulas existentes ficaram sem arquivos anexados (null)")
                print("ℹ️  Você pode editar cada aula para adicionar arquivos")
            
            print("\n🎯 ATUALIZAÇÃO CONCLUÍDA!")
            print("✅ Agora é possível anexar arquivos às aulas dos departamentos")
            print("📎 Tipos permitidos: PDF, DOC, DOCX, TXT, JPG, PNG")
            print("💾 Tamanho máximo: 5MB por arquivo")
            
        except Exception as e:
            print(f"❌ Erro ao atualizar banco: {str(e)}")
            return False
            
    return True

if __name__ == "__main__":
    success = atualizar_banco_aulas()
    if success:
        print("\n🚀 Execute o sistema novamente para testar as novas funcionalidades!")
    else:
        print("\n❌ Houve erro na atualização. Verifique os logs.")