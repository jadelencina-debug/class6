"""usuarios con auth

Revision ID: f70fb95d10ae
Revises:
Create Date: 2026-09-14

Agrega a la tabla usuarios:
  - hashed_password (renombrada de password_hash)
  - acepto_tratamiento (BOOLEAN NOT NULL)
  - fecha_consentimiento (DATETIME)

Nota: SQLite no soporta ALTER COLUMN RENAME directamente en versiones <3.25.
Usamos la estrategia de agregar columna nueva + copiar datos + drop columna vieja
a través de batch_alter_table de Alembic (que hace el rebuild de la tabla).
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'f70fb95d10ae'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Usamos batch_alter_table para que SQLite pueda renombrar columna y agregar nuevas
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        # Renombrar password_hash -> hashed_password
        batch_op.alter_column('password_hash', new_column_name='hashed_password')
        # Agregar columnas nuevas con valores por defecto para las filas existentes
        batch_op.add_column(
            sa.Column('acepto_tratamiento', sa.Boolean(), nullable=False,
                      server_default=sa.false())
        )
        batch_op.add_column(
            sa.Column('fecha_consentimiento', sa.DateTime(),
                      nullable=False, server_default=sa.text("'2026-01-01 00:00:00'"))
        )


def downgrade() -> None:
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.drop_column('fecha_consentimiento')
        batch_op.drop_column('acepto_tratamiento')
        batch_op.alter_column('hashed_password', new_column_name='password_hash')
