"""add_sender_hash_and_dedup_status

Revision ID: c04ddbce2571
Revises: 8728823c85ee
Create Date: 2026-05-19 17:57:36.626030

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c04ddbce2571'
down_revision: Union[str, Sequence[str], None] = '8728823c85ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    import sqlalchemy as sa
    from alembic import op

    # La colonne pour le statut de déduplication 
    op.add_column('demandes', sa.Column('dedup_status', sa.String(length=50), nullable=True, server_default='unique'))
    
    # La colonne pour stocker l'identifiant technique/anonyme de l'expéditeur
    op.add_column('demandes', sa.Column('sender', sa.String(length=64), nullable=True))

def downgrade() -> None:
    from alembic import op
    op.drop_column('demandes', 'sender')
    op.drop_column('demandes', 'dedup_status')