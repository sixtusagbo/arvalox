"""Remove STARTER plan type from subscription plans

Revision ID: 6a1e5f4f35fe
Revises: d3a8e684cbb5
Create Date: 2025-08-24 15:01:42.113247

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a1e5f4f35fe'
down_revision = 'd3a8e684cbb5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove any existing STARTER plan records
    op.execute("DELETE FROM subscription_plans WHERE plan_type = 'starter'")
    
    # Update any subscriptions using STARTER plan to use FREE plan instead
    op.execute("""
        UPDATE subscriptions 
        SET plan_id = (SELECT id FROM subscription_plans WHERE plan_type = 'free' LIMIT 1)
        WHERE plan_id IN (SELECT id FROM subscription_plans WHERE plan_type = 'starter')
    """)
    
    # Recreate the enum without STARTER
    op.execute("ALTER TYPE plantype RENAME TO plantype_old")
    op.execute("CREATE TYPE plantype AS ENUM ('FREE', 'PROFESSIONAL', 'ENTERPRISE')")
    op.execute("ALTER TABLE subscription_plans ALTER COLUMN plan_type TYPE plantype USING plan_type::text::plantype")
    op.execute("DROP TYPE plantype_old")


def downgrade() -> None:
    # Recreate the old enum with STARTER
    op.execute("ALTER TYPE plantype RENAME TO plantype_old")
    op.execute("CREATE TYPE plantype AS ENUM ('FREE', 'STARTER', 'PROFESSIONAL', 'ENTERPRISE')")
    op.execute("ALTER TABLE subscription_plans ALTER COLUMN plan_type TYPE plantype USING plan_type::text::plantype")
    op.execute("DROP TYPE plantype_old")
