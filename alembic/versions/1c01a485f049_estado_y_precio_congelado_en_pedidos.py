"""estado y precio congelado en pedidos

Revision ID: 1c01a485f049
Revises: f70fb95d10ae
Create Date: 2026-09-22 12:57:31.886248

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c01a485f049'
down_revision: Union[str, Sequence[str], None] = 'f70fb95d10ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — compatible con SQLite usando batch mode."""
    # SQLite no soporta ALTER COLUMN directo; batch_alter_table recrea la tabla.

    # items_pedido: cambiar precio_unitario de FLOAT a Numeric(12,2)
    with op.batch_alter_table('items_pedido') as batch_op:
        batch_op.alter_column(
            'precio_unitario',
            existing_type=sa.FLOAT(),
            type_=sa.Numeric(precision=12, scale=2),
            existing_nullable=False,
        )

    # pedidos: agregar creado_en y cambiar total de FLOAT a Numeric(12,2)
    with op.batch_alter_table('pedidos') as batch_op:
        batch_op.alter_column(
            'total',
            existing_type=sa.FLOAT(),
            type_=sa.Numeric(precision=12, scale=2),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('pedidos') as batch_op:
        batch_op.alter_column(
            'total',
            existing_type=sa.Numeric(precision=12, scale=2),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )

    with op.batch_alter_table('items_pedido') as batch_op:
        batch_op.alter_column(
            'precio_unitario',
            existing_type=sa.Numeric(precision=12, scale=2),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
