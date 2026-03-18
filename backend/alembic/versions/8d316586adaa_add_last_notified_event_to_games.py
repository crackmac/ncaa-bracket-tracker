"""add last_notified_event to games

Revision ID: 8d316586adaa
Revises: 
Create Date: 2026-03-18 00:18:46.441988

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d316586adaa'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('games', sa.Column('last_notified_event', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('games', 'last_notified_event')
