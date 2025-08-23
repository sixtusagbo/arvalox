"""Add currency fields to organization

Revision ID: e8b6161a35e6
Revises: 5a03e7168715
Create Date: 2025-08-23 01:36:00.205547

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8b6161a35e6'
down_revision = '5a03e7168715'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add currency fields to organizations table (nullable first)
    op.add_column('organizations', sa.Column('currency_code', sa.String(3), nullable=True))
    op.add_column('organizations', sa.Column('currency_symbol', sa.String(10), nullable=True))
    op.add_column('organizations', sa.Column('currency_name', sa.String(100), nullable=True))
    
    # Update existing rows with default values
    op.execute("UPDATE organizations SET currency_code = 'NGN', currency_symbol = '₦', currency_name = 'Nigerian Naira' WHERE currency_code IS NULL")
    
    # Make columns NOT NULL after setting default values
    op.alter_column('organizations', 'currency_code', nullable=False)
    op.alter_column('organizations', 'currency_symbol', nullable=False)
    op.alter_column('organizations', 'currency_name', nullable=False)


def downgrade() -> None:
    # Remove currency fields from organizations table
    op.drop_column('organizations', 'currency_name')
    op.drop_column('organizations', 'currency_symbol')
    op.drop_column('organizations', 'currency_code')
