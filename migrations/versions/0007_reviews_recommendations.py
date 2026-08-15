"""create review and recommendation tables"""
from alembic import op
import sqlalchemy as sa
revision='0007_reviews_recommendations'; down_revision='0006_analytics_ads'; branch_labels=None; depends_on=None
def upgrade():
    op.create_table('ad_recommendations',sa.Column('id',sa.Integer,primary_key=True),sa.Column('product_id',sa.Integer,sa.ForeignKey('products.id'),nullable=False),sa.Column('summary_text',sa.String(2000),nullable=False),sa.Column('confirm_status',sa.String(30),nullable=False,server_default='pending')); op.create_index('ix_ad_recommendations_product_id','ad_recommendations',['product_id'])
    # review_reports is created in 0003 for analytics; this migration is intentionally idempotent for fresh installs.
def downgrade():
    op.drop_index('ix_ad_recommendations_product_id',table_name='ad_recommendations'); op.drop_table('ad_recommendations')
