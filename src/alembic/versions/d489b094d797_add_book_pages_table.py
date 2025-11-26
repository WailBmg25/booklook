"""add_book_pages_table

Revision ID: d489b094d797
Revises: b88f70689ea9
Create Date: 2025-11-10 15:08:56.325475

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd489b094d797'
down_revision: Union[str, None] = 'b88f70689ea9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create book_pages table
    op.create_table(
        'book_pages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('word_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('book_id', 'page_number', name='unique_book_page')
    )
    
    # Create indexes
    op.create_index('idx_book_pages_book_id', 'book_pages', ['book_id'])
    op.create_index('idx_book_pages_book_page', 'book_pages', ['book_id', 'page_number'])
    
    # Create GIN index for full-text search on content
    op.execute(
        "CREATE INDEX idx_book_pages_content_search ON book_pages USING gin(to_tsvector('english', content))"
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_book_pages_content_search', table_name='book_pages')
    op.drop_index('idx_book_pages_book_page', table_name='book_pages')
    op.drop_index('idx_book_pages_book_id', table_name='book_pages')
    
    # Drop table
    op.drop_table('book_pages')
