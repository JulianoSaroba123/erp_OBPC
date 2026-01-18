"""
Script para criar a tabela agenda_pastoral no banco de dados
"""

import os
import sqlite3

def criar_tabela_agenda_pastoral():
    """Cria a tabela agenda_pastoral diretamente no SQLite"""
    
    # Caminho do banco de dados
    db_path = os.path.join('instance', 'database.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado em: {db_path}")
        return
    
    try:
        print("📅 Criando tabela agenda_pastoral...")
        
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # SQL para criar a tabela
        sql = """
            CREATE TABLE IF NOT EXISTS agenda_pastoral (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                titulo VARCHAR(200) NOT NULL,
                descricao TEXT,
                data DATE NOT NULL,
                hora_inicio TIME,
                hora_fim TIME,
                local VARCHAR(200),
                tipo_atividade VARCHAR(50),
                prioridade VARCHAR(20) DEFAULT 'Normal',
                status VARCHAR(20) DEFAULT 'Pendente',
                observacoes TEXT,
                concluida BOOLEAN DEFAULT 0,
                data_conclusao DATETIME,
                data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        """
        
        cursor.execute(sql)
        conn.commit()
        conn.close()
        
        print("✅ Tabela agenda_pastoral criada com sucesso!")
        print("\n📋 Campos da tabela:")
        print("   • usuario_id - Dono da agenda (pastor)")
        print("   • titulo - Título da atividade")
        print("   • descricao - Descrição detalhada")
        print("   • data - Data da atividade")
        print("   • hora_inicio/hora_fim - Horário")
        print("   • local - Local da atividade")
        print("   • tipo_atividade - Tipo (Visita, Reunião, etc)")
        print("   • prioridade - Baixa, Normal, Alta, Urgente")
        print("   • status - Pendente, Em Andamento, Concluída, Cancelada")
        print("   • observacoes - Notas adicionais")
        print("   • concluida - Se foi concluída")
        
    except Exception as e:
        print(f"\n❌ Erro ao criar tabela: {e}")
        raise

if __name__ == "__main__":
    criar_tabela_agenda_pastoral()
