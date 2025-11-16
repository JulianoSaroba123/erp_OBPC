"""
Script para atualizar o módulo financeiro com funcionalidades avançadas de conciliação bancária
Execute este script para aplicar todas as melhorias ao sistema
"""

import os
import sys

# Adicionar o diretório raiz do projeto ao path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento, ConciliacaoHistorico, ConciliacaoPar, ImportacaoExtrato

def atualizar_banco_dados():
    """Cria as novas tabelas e colunas necessárias"""
    print("🔄 Atualizando banco de dados...")
    
    try:
        # Criar todas as tabelas
        db.create_all()
        print("✅ Tabelas criadas/atualizadas com sucesso")
        
        # Adicionar colunas que podem estar faltando na tabela de lançamentos
        with db.engine.connect() as conn:
            try:
                # Verificar se as novas colunas existem, se não, criar
                result = conn.execute("PRAGMA table_info(lancamentos)")
                colunas_existentes = [row[1] for row in result.fetchall()]
                
                novas_colunas = [
                    ("hash_duplicata", "VARCHAR(64)"),
                    ("banco_origem", "VARCHAR(100)"),
                    ("documento_ref", "VARCHAR(50)"),
                    ("conciliado_em", "DATETIME"),
                    ("conciliado_por", "VARCHAR(100)"),
                    ("par_conciliacao_id", "INTEGER")
                ]
                
                for nome_coluna, tipo_coluna in novas_colunas:
                    if nome_coluna not in colunas_existentes:
                        try:
                            conn.execute(f"ALTER TABLE lancamentos ADD COLUMN {nome_coluna} {tipo_coluna}")
                            print(f"✅ Coluna '{nome_coluna}' adicionada à tabela lancamentos")
                        except Exception as e:
                            print(f"⚠️  Coluna '{nome_coluna}' já existe ou erro: {e}")
                
                conn.commit()
                
            except Exception as e:
                print(f"⚠️  Erro ao verificar/adicionar colunas: {e}")
        
        # Atualizar hashes de duplicatas para registros existentes
        print("🔄 Atualizando hashes de duplicatas...")
        lancamentos_sem_hash = Lancamento.query.filter_by(hash_duplicata=None).all()
        
        for lancamento in lancamentos_sem_hash:
            lancamento.hash_duplicata = lancamento.gerar_hash_duplicata()
        
        db.session.commit()
        print(f"✅ Hashes atualizados para {len(lancamentos_sem_hash)} lançamentos")
        
    except Exception as e:
        print(f"❌ Erro ao atualizar banco de dados: {e}")
        db.session.rollback()
        return False
    
    return True

def criar_dados_exemplo():
    """Cria dados de exemplo para demonstração"""
    print("🔄 Criando dados de exemplo...")
    
    try:
        from datetime import datetime, timedelta
        import random
        
        # Verificar se já existem dados
        if Lancamento.query.count() > 0:
            print("ℹ️  Dados já existem, pulando criação de exemplos")
            return True
        
        # Criar alguns lançamentos de exemplo
        categorias = ['Dízimo', 'Oferta', 'Doação', 'Venda', 'Despesas Gerais', 'Combustível', 'Material de Limpeza']
        contas = ['Banco', 'Dinheiro', 'Pix']
        
        for i in range(20):
            # Lançamentos manuais
            lancamento = Lancamento(
                data=datetime.now().date() - timedelta(days=random.randint(1, 30)),
                tipo='Entrada' if random.choice([True, False]) else 'Saída',
                categoria=random.choice(categorias),
                descricao=f'Lançamento manual de exemplo {i+1}',
                valor=round(random.uniform(50, 1000), 2),
                conta=random.choice(contas),
                origem='manual'
            )
            lancamento.save()
            
            # Alguns lançamentos importados para demonstrar conciliação
            if i < 10:
                lancamento_importado = Lancamento(
                    data=lancamento.data,
                    tipo=lancamento.tipo,
                    descricao=f'Extrato bancário - {lancamento.descricao}',
                    valor=lancamento.valor + random.uniform(-5, 5),  # Pequena variação
                    conta='Banco',
                    origem='importado',
                    banco_origem='Banco Exemplo'
                )
                lancamento_importado.save()
        
        print("✅ Dados de exemplo criados com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar dados de exemplo: {e}")
        db.session.rollback()
        return False

def registrar_blueprints():
    """Registra os novos blueprints no app"""
    print("🔄 Verificando registro de blueprints...")
    
    # Verificar se o arquivo principal do app está registrando os blueprints
    app_init_path = os.path.join(project_root, 'app', '__init__.py')
    
    try:
        with open(app_init_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Verificar se o blueprint de conciliação já está registrado
        if 'conciliacao_bp' not in conteudo:
            print("⚠️  Blueprint de conciliação não encontrado no app/__init__.py")
            print("📝 Adicione as seguintes linhas ao seu app/__init__.py:")
            print()
            print("# Na seção de imports:")
            print("from app.financeiro.routes_conciliacao import conciliacao_bp")
            print()
            print("# Na função create_app, após os outros blueprints:")
            print("app.register_blueprint(conciliacao_bp)")
            print()
        else:
            print("✅ Blueprint de conciliação já registrado")
            
    except Exception as e:
        print(f"⚠️  Erro ao verificar app/__init__.py: {e}")

def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    print("🔄 Verificando dependências...")
    
    dependencias = [
        'pandas',
        'numpy', 
        'openpyxl',
        'xlrd'
    ]
    
    faltantes = []
    
    for dep in dependencias:
        try:
            __import__(dep)
            print(f"✅ {dep} instalado")
        except ImportError:
            faltantes.append(dep)
            print(f"❌ {dep} não encontrado")
    
    if faltantes:
        print()
        print("📦 Para instalar as dependências faltantes, execute:")
        print(f"pip install {' '.join(faltantes)}")
        return False
    
    return True

def criar_diretorio_uploads():
    """Cria diretório para uploads de extratos"""
    print("🔄 Criando diretórios necessários...")
    
    upload_dir = os.path.join(project_root, 'app', 'static', 'uploads', 'extratos')
    
    try:
        os.makedirs(upload_dir, exist_ok=True)
        print(f"✅ Diretório criado: {upload_dir}")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar diretório: {e}")
        return False

def main():
    """Função principal que executa todas as atualizações"""
    print("=" * 60)
    print("🚀 ATUALIZAÇÃO DO MÓDULO FINANCEIRO - CONCILIAÇÃO BANCÁRIA")
    print("=" * 60)
    print()
    
    # Criar aplicação Flask
    app = create_app()
    
    with app.app_context():
        etapas = [
            ("Verificar dependências", verificar_dependencias),
            ("Criar diretórios", criar_diretorio_uploads),
            ("Atualizar banco de dados", atualizar_banco_dados),
            ("Criar dados de exemplo", criar_dados_exemplo),
            ("Verificar blueprints", registrar_blueprints)
        ]
        
        sucessos = 0
        
        for nome, funcao in etapas:
            print(f"📋 {nome}...")
            if funcao():
                sucessos += 1
            print()
        
        print("=" * 60)
        print(f"✅ ATUALIZAÇÃO CONCLUÍDA: {sucessos}/{len(etapas)} etapas bem-sucedidas")
        print("=" * 60)
        print()
        
        if sucessos == len(etapas):
            print("🎉 Sistema atualizado com sucesso!")
            print()
            print("🔗 Novas funcionalidades disponíveis:")
            print("  • Dashboard de conciliação bancária")
            print("  • Importação de extratos CSV/XLSX")
            print("  • Conciliação automática inteligente")
            print("  • Conciliação manual assistida")
            print("  • Detecção automática de duplicatas")
            print("  • Histórico e auditoria de conciliações")
            print("  • Relatórios de discrepâncias")
            print("  • Exportação de dados")
            print()
            print("🌐 Acesse: /financeiro/conciliacao/dashboard")
        else:
            print("⚠️  Algumas etapas falharam. Verifique os erros acima.")
            print("💡 Você pode executar novamente após corrigir os problemas.")

if __name__ == "__main__":
    main()