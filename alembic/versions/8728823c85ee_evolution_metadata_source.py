"""evolution_metadata_source

Revision ID: 8728823c85ee
Revises: 
Create Date: 2026-05-15 15:17:30.727137

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8728823c85ee'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Ajout des colonnes demandées
    op.add_column('demandes', sa.Column('received_at', sa.DateTime(), nullable=True))
    op.add_column('demandes', sa.Column('external_id', sa.String(length=255), nullable=True))
    op.add_column('demandes', sa.Column('canal_metadata', postgresql.JSONB(), nullable=True))

    # 2. Suppression de l'ancienne contrainte d'unicité (pour la remplacer)
    # Son nom est 'unique_input_version' dans votre schema.sql
    op.drop_constraint('unique_input_version', 'demandes', type_='unique')

    # 3. Nouvel index unique pour l'idempotence (canal + external_id)
    op.create_unique_constraint('uq_canal_external_id', 'demandes', ['canal', 'external_id'])

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_canal_external_id', 'demandes', type_='unique')
    op.create_unique_constraint('unique_input_version', 'demandes', ['input_text', 'dataset_version'])
    
    op.drop_column('demandes', 'canal_metadata')
    op.drop_column('demandes', 'external_id')
    op.drop_column('demandes', 'received_at')
