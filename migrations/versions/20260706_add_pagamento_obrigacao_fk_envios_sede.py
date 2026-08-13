"""Adiciona FK explicita de EnvioSede para PagamentoObrigacao

Revision ID: add_envio_pagamento_obrigacao_fk
Revises: add_hora_notificacao
Create Date: 2026-07-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_envio_pagamento_obrigacao_fk'
down_revision = 'add_hora_notificacao'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('envios_sede', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pagamento_obrigacao_id', sa.Integer(), nullable=True))
        batch_op.create_unique_constraint(
            'uq_envios_sede_pagamento_obrigacao_id',
            ['pagamento_obrigacao_id'],
        )
        batch_op.create_foreign_key(
            'fk_envios_sede_pagamento_obrigacao_id',
            'pagamentos_obrigacao',
            ['pagamento_obrigacao_id'],
            ['id'],
            ondelete='SET NULL',
        )


def downgrade():
    with op.batch_alter_table('envios_sede', schema=None) as batch_op:
        batch_op.drop_constraint('fk_envios_sede_pagamento_obrigacao_id', type_='foreignkey')
        batch_op.drop_constraint('uq_envios_sede_pagamento_obrigacao_id', type_='unique')
        batch_op.drop_column('pagamento_obrigacao_id')
