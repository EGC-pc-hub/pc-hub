"""update_publication_type_enum

Revision ID: 004
Revises: 003
Create Date: 2025-12-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Update ds_meta_data publication_type enum
    op.execute("""
        ALTER TABLE ds_meta_data 
        MODIFY COLUMN publication_type 
        ENUM('NONE', 'SOFTWARE', 'HARDWARE', 'OTHER') 
        NOT NULL
    """)
    
    # Update fm_meta_data publication_type enum
    op.execute("""
        ALTER TABLE fm_meta_data 
        MODIFY COLUMN publication_type 
        ENUM('NONE', 'SOFTWARE', 'HARDWARE', 'OTHER') 
        NOT NULL
    """)


def downgrade():
    # Revert to original enum values
    op.execute("""
        ALTER TABLE ds_meta_data 
        MODIFY COLUMN publication_type 
        ENUM('NONE', 'ANNOTATION_COLLECTION', 'BOOK', 'BOOK_SECTION', 
             'CONFERENCE_PAPER', 'DATA_MANAGEMENT_PLAN', 'JOURNAL_ARTICLE', 
             'PATENT', 'PREPRINT', 'PROJECT_DELIVERABLE', 'PROJECT_MILESTONE', 
             'PROPOSAL', 'REPORT', 'SOFTWARE_DOCUMENTATION', 'TAXONOMIC_TREATMENT', 
             'TECHNICAL_NOTE', 'THESIS', 'WORKING_PAPER', 'OTHER') 
        NOT NULL
    """)
    
    op.execute("""
        ALTER TABLE fm_meta_data 
        MODIFY COLUMN publication_type 
        ENUM('NONE', 'ANNOTATION_COLLECTION', 'BOOK', 'BOOK_SECTION', 
             'CONFERENCE_PAPER', 'DATA_MANAGEMENT_PLAN', 'JOURNAL_ARTICLE', 
             'PATENT', 'PREPRINT', 'PROJECT_DELIVERABLE', 'PROJECT_MILESTONE', 
             'PROPOSAL', 'REPORT', 'SOFTWARE_DOCUMENTATION', 'TAXONOMIC_TREATMENT', 
             'TECHNICAL_NOTE', 'THESIS', 'WORKING_PAPER', 'OTHER') 
        NOT NULL
    """)
