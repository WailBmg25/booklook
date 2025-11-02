"""Add performance indexes and partitioning

Revision ID: 559eb19db0f4
Revises: 2ab652388644
Create Date: 2025-11-02 18:06:40.981825

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '559eb19db0f4'
down_revision: Union[str, None] = '2ab652388644'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create GIN indexes for full-text search on book titles
    op.execute("CREATE INDEX IF NOT EXISTS idx_books_title_gin ON books USING gin(to_tsvector('english', titre))")
    
    # Create GIN indexes for array fields (author_names and genre_names)
    op.execute("CREATE INDEX IF NOT EXISTS idx_books_authors_gin ON books USING gin(author_names)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_books_genres_gin ON books USING gin(genre_names)")
    
    # Create performance indexes for common queries
    op.execute("CREATE INDEX IF NOT EXISTS idx_books_rating ON books(average_rating DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_books_publication_year ON books(EXTRACT(YEAR FROM date_publication))")
    op.execute("CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_reading_progress_last_read ON reading_progress(last_read_at DESC)")
    
    # Create composite indexes for common query patterns
    op.execute("CREATE INDEX IF NOT EXISTS idx_books_rating_year ON books(average_rating DESC, EXTRACT(YEAR FROM date_publication))")
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_favorites_added ON user_favorites(user_id, added_at DESC)")


def downgrade() -> None:
    # Drop performance indexes
    op.execute("DROP INDEX IF EXISTS idx_books_title_gin")
    op.execute("DROP INDEX IF EXISTS idx_books_authors_gin")
    op.execute("DROP INDEX IF EXISTS idx_books_genres_gin")
    op.execute("DROP INDEX IF EXISTS idx_books_rating")
    op.execute("DROP INDEX IF EXISTS idx_books_publication_year")
    op.execute("DROP INDEX IF EXISTS idx_reviews_rating")
    op.execute("DROP INDEX IF EXISTS idx_reading_progress_last_read")
    op.execute("DROP INDEX IF EXISTS idx_books_rating_year")
    op.execute("DROP INDEX IF EXISTS idx_user_favorites_added")
