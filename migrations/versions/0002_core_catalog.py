"""create products, skus and inventory"""
from alembic import op
import sqlalchemy as sa
revision='0002_core_catalog'; down_revision='0001_users'; branch_labels=None; depends_on=None
def upgrade():
    op.create_table('products',sa.Column('id',sa.Integer,primary_key=True),sa.Column('store_id',sa.Integer,nullable=False),sa.Column('name',sa.String(200),nullable=False),sa.Column('platform',sa.String(50),nullable=False,server_default='other'),sa.Column('category',sa.String(120),nullable=False,server_default=''),sa.Column('price',sa.Float,nullable=False,server_default='0'),sa.Column('cost',sa.Float,nullable=False,server_default='0'),sa.Column('status',sa.String(30),nullable=False,server_default='draft'))
    op.create_index('ix_products_store_id','products',['store_id'])
    op.create_table('product_skus',sa.Column('id',sa.Integer,primary_key=True),sa.Column('product_id',sa.Integer,sa.ForeignKey('products.id'),nullable=False),sa.Column('sku_code',sa.String(100),nullable=False),sa.Column('sku_name',sa.String(200),nullable=False),sa.Column('price',sa.Float,nullable=False,server_default='0'),sa.Column('status',sa.String(30),nullable=False,server_default='active'))
    op.create_index('ix_product_skus_product_id','product_skus',['product_id'])
    op.create_table('inventory_items',sa.Column('id',sa.Integer,primary_key=True),sa.Column('sku_id',sa.Integer,sa.ForeignKey('product_skus.id'),nullable=False,unique=True),sa.Column('stock_qty',sa.Integer,nullable=False,server_default='0'),sa.Column('locked_qty',sa.Integer,nullable=False,server_default='0'),sa.Column('warning_threshold',sa.Integer,nullable=False,server_default='10'))
def downgrade():
    op.drop_table('inventory_items'); op.drop_index('ix_product_skus_product_id',table_name='product_skus'); op.drop_table('product_skus'); op.drop_index('ix_products_store_id',table_name='products'); op.drop_table('products')
