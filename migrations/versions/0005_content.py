"""create diagnosis and creative plan tables"""
from alembic import op
import sqlalchemy as sa
revision='0005_content'; down_revision='0004_stores'; branch_labels=None; depends_on=None
def upgrade():
    op.create_table('product_diagnoses',sa.Column('id',sa.Integer,primary_key=True),sa.Column('product_id',sa.Integer,sa.ForeignKey('products.id'),nullable=False),sa.Column('positioning',sa.String(1000),nullable=False,server_default=''),sa.Column('recommendations',sa.String(2000),nullable=False,server_default=''))
    op.create_index('ix_product_diagnoses_product_id','product_diagnoses',['product_id'])
    op.create_table('creative_plans',sa.Column('id',sa.Integer,primary_key=True),sa.Column('product_id',sa.Integer,sa.ForeignKey('products.id'),nullable=False),sa.Column('plan_type',sa.String(40),nullable=False),sa.Column('title',sa.String(200),nullable=False),sa.Column('content_json',sa.String(10000),nullable=False,server_default='[]'),sa.Column('status',sa.String(30),nullable=False,server_default='draft'))
    op.create_index('ix_creative_plans_product_id','creative_plans',['product_id'])
def downgrade():
    op.drop_index('ix_creative_plans_product_id',table_name='creative_plans'); op.drop_table('creative_plans'); op.drop_index('ix_product_diagnoses_product_id',table_name='product_diagnoses'); op.drop_table('product_diagnoses')
