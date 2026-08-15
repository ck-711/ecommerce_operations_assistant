"""create analytics and promotion tables"""
from alembic import op
import sqlalchemy as sa
revision='0006_analytics_ads'; down_revision='0005_content'; branch_labels=None; depends_on=None
def upgrade():
    op.create_table('promotion_links',sa.Column('id',sa.Integer,primary_key=True),sa.Column('product_id',sa.Integer,sa.ForeignKey('products.id'),nullable=False),sa.Column('link_name',sa.String(160),nullable=False),sa.Column('target_url',sa.String(500),nullable=False),sa.Column('tracking_code',sa.String(40),nullable=False,unique=True)); op.create_index('ix_promotion_links_product_id','promotion_links',['product_id'])
    op.create_table('ad_experiments',sa.Column('id',sa.Integer,primary_key=True),sa.Column('product_id',sa.Integer,sa.ForeignKey('products.id'),nullable=False),sa.Column('experiment_name',sa.String(200),nullable=False),sa.Column('experiment_status',sa.String(30),nullable=False,server_default='draft')); op.create_index('ix_ad_experiments_product_id','ad_experiments',['product_id'])
def downgrade():
    op.drop_index('ix_ad_experiments_product_id',table_name='ad_experiments'); op.drop_table('ad_experiments'); op.drop_index('ix_promotion_links_product_id',table_name='promotion_links'); op.drop_table('promotion_links')
