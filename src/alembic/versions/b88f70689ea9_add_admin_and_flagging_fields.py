"""add_admin_and_flagging_fields

Revision ID: b88f70689ea9
Revises: 559eb19db0f4
Create Date: 2025-11-06 16:52:49.799971

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b88f70689ea9'
down_revision: Union[str, None] = '559eb19db0f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_admin column to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add is_flagged column to reviews table
    op.add_column('reviews', sa.Column('is_flagged', sa.Boolean(), nullable=False, server_default='false'))
    
    # Create indexes
    op.create_index('idx_users_is_admin', 'users', ['is_admin'])
    op.create_index('idx_reviews_is_flagged', 'reviews', ['is_flagged'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_reviews_is_flagged', table_name='reviews')
    op.drop_index('idx_users_is_admin', table_name='users')
    
    # Drop columns
    op.drop_column('reviews', 'is_flagged')
    op.drop_column('users', 'is_admin')
