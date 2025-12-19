"""
Script para limpar arquivos de teste, debug e documentação temporária
Mantém apenas arquivos essenciais para produção
"""
import os
import shutil

# Diretório raiz do projeto
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Arquivos e padrões para remover
ARQUIVOS_REMOVER = [
    # Scripts de teste
    'testar_*.py',
    'teste_*.py',
    'test_*.py',
    'debug_*.py',
    'verificar_*.py',
    'criar_dados_*.py',
    'criar_certificados_*.py',
    'criar_eventos_*.py',
    'criar_oficios_*.py',
    'adicionar_*.py',
    'atualizar_*.py',
    'corrigir_*.py',
    'limpar_*.py',
    'diagnosticar_*.py',
    'analisar_*.py',
    'validar_*.py',
    'demonstrar_*.py',
    'investigar_*.py',
    'resumo_*.py',
    'inicializar_*.py',
    'migrar_*.py',
    'forcar_*.py',
    'inserir_*.py',
    'restaurar_*.py',
    'encontrar_*.py',
    'recriar_*.py',
    'padronizar_*.py',
    'buscar_*.py',
    'ver_*.py',
    
    # PDFs de teste
    'teste_*.pdf',
    'relatorio_*.pdf',
    'inventario_*.pdf',
    'oficio_*.pdf',
    'ata_*.pdf',
    
    # Arquivos HTML de debug
    'debug_*.html',
    'teste_*.html',
    'analise_*.html',
    
    # Arquivos CSV de teste
    'teste_*.csv',
    'Extrato da Conta - PagSeguro.csv',
    
    # Documentação temporária
    'TESTE_*.md',
    'GUIA_*.md',
    'MODULO_*.md',
    'RELATORIO_*.md',
    'IMPLEMENTACAO_*.md',
    'CORRECAO_*.md',
    'STATUS_*.md',
    'DIAGNOSTICO_*.md',
    'SOLUCAO_*.md',
    'PROBLEMA_*.md',
    'SISTEMA_*.md',
    'LISTA_*.md',
    'MIDIA_*.txt',
    'RELATORIO_*.txt',
    'ATUALIZACAO_*.txt',
    'ARQUIVOS_*.txt',
    'ENTREGA_FINAL.txt',
    
    # Scripts Python específicos
    'implementar_niveis_acesso.py',
    'criar_instalador_exe.py',
    'instalador_*.py',
    'criar_icone.py',
    'criar_icone_profissional.py',
    'criar_atalho_*.py',
    'criar_admin.py',
    'criar_configuracao_padrao.py',
    'criar_despesas_fixas_conselho.py',
    'criar_modulo_participacao.py',
    'criar_estrutura_financeira.py',
    'criar_banco_genero.py',
    'criar_tabelas_*.py',
    'iniciar_obpc_*.py',
    'executavel_profissional.py',
    'tela_carregamento.py',
    'utils_sistema.py',
    'fechar_obpc.py',
    'obpc_server.pid',
    
    # Arquivos JS de debug
    'debug_*.js',
    
    # Arquivos Python de instrução/deploy
    'INSTRUCOES_*.py',
    'DEPLOY_INSTRUCTIONS.py',
    'IMPLEMENTACAO_COMPLETA.py',
    
    # Arquivos .bat (exceto o principal se necessário)
    'build_EXE.bat',
    'IniciarOBPC_*.bat',
    'InstalarOBPC*.bat',
    'ExecutarOBPC*.bat',
    'run_OBPC.bat',
    'Iniciar_OBPC_Simples.bat',
    'Sistema OBPC.bat',
    'OBPC_Sistema_Automatico.bat',
    
    # Arquivos VBS
    '*.vbs',
]

# Diretórios para remover completamente
DIRETORIOS_REMOVER = [
    '__pycache__',
    'scripts',
    '.vscode',
    '.venv',
]

def remover_por_padrao(padrao):
    """Remove arquivos que correspondem ao padrão (glob)"""
    import glob
    arquivos = glob.glob(os.path.join(ROOT_DIR, padrao))
    removidos = []
    for arquivo in arquivos:
        if os.path.isfile(arquivo):
            try:
                os.remove(arquivo)
                removidos.append(os.path.basename(arquivo))
                print(f"✓ Removido: {os.path.basename(arquivo)}")
            except Exception as e:
                print(f"✗ Erro ao remover {os.path.basename(arquivo)}: {e}")
    return removidos

def remover_diretorio(dir_name):
    """Remove diretório completo"""
    dir_path = os.path.join(ROOT_DIR, dir_name)
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        try:
            shutil.rmtree(dir_path)
            print(f"✓ Diretório removido: {dir_name}")
            return True
        except Exception as e:
            print(f"✗ Erro ao remover diretório {dir_name}: {e}")
            return False
    return False

def main():
    print("=" * 60)
    print("LIMPEZA DE ARQUIVOS DESNECESSÁRIOS")
    print("=" * 60)
    print()
    
    # Remover arquivos por padrão
    total_removidos = 0
    for padrao in ARQUIVOS_REMOVER:
        removidos = remover_por_padrao(padrao)
        total_removidos += len(removidos)
    
    print()
    print("-" * 60)
    
    # Remover diretórios
    dirs_removidos = 0
    for dir_name in DIRETORIOS_REMOVER:
        if remover_diretorio(dir_name):
            dirs_removidos += 1
    
    print()
    print("=" * 60)
    print(f"RESUMO: {total_removidos} arquivos e {dirs_removidos} diretórios removidos")
    print("=" * 60)
    print()
    print("ARQUIVOS MANTIDOS (essenciais):")
    print("  - run.py")
    print("  - requirements.txt")
    print("  - README.md")
    print("  - .gitignore")
    print("  - .env.example")
    print("  - Procfile")
    print("  - render.yaml")
    print("  - app/ (toda estrutura da aplicação)")
    print("  - venv/ (ambiente virtual)")
    print("  - instance/ (banco de dados)")
    print()

if __name__ == '__main__':
    resposta = input("Deseja continuar com a limpeza? (s/n): ")
    if resposta.lower() == 's':
        main()
        print("Limpeza concluída! Sistema pronto para deploy.")
    else:
        print("Limpeza cancelada.")
