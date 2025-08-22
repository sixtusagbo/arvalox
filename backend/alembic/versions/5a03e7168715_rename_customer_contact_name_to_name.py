"""rename_customer_contact_name_to_name

Revision ID: 5a03e7168715
Revises: 2763d85a744d
Create Date: 2025-08-22 08:16:17.786002

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a03e7168715'
down_revision = '2763d85a744d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename contact_name column to name in customers table
    op.alter_column('customers', 'contact_name', new_column_name='name')


def downgrade() -> None:
    # Rename name column back to contact_name in customers table
    op.alter_column('customers', 'name', new_column_name='contact_name')
