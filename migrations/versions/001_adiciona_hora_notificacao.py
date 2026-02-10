"""Adiciona coluna hora_notificacao_automatica

Revision ID: add_hora_notificacao
Revises: 
Create Date: 2026-02-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_hora_notificacao'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar coluna
    op.add_column('configuracao_notificacoes', 
                   sa.Column('hora_notificacao_automatica', 
                            sa.String(5), 
                            nullable=True))
    
    # Adicionar valor padrão
    op.execute("UPDATE configuracao_notificacoes SET hora_notificacao_automatica = '08:00' WHERE hora_notificacao_automatica IS NULL")
    op.alter_column('configuracao_notificacoes', 'hora_notificacao_automatica',
                    existing_type=sa.String(5),
                    nullable=False,
                    existing_nullable=True)


def downgrade():
    # Remover coluna se houver rollback
    op.drop_column('configuracao_notificacoes', 'hora_notificacao_automatica')
