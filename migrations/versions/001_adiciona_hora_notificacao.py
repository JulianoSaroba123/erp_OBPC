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
    # Adicionar coluna com valor padrão
    op.add_column('configuracao_notificacoes', 
                   sa.Column('hora_notificacao_automatica', 
                            sa.String(5), 
                            nullable=True,
                            server_default='08:00'))


def downgrade():
    # Remover coluna se houver rollback
    op.drop_column('configuracao_notificacoes', 'hora_notificacao_automatica')
