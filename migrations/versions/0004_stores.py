"""create stores table"""
from alembic import op
import sqlalchemy as sa
revision='0004_stores'; down_revision='0003_operations'; branch_labels=None; depends_on=None
def upgrade():
    op.create_table('stores',sa.Column('id',sa.Integer,primary_key=True),sa.Column('store_name',sa.String(160),nullable=False),sa.Column('platform',sa.String(50),nullable=False,server_default='other'),sa.Column('owner_name',sa.String(120),nullable=False,server_default=''),sa.Column('remark',sa.String(500),nullable=False,server_default=''))
def downgrade(): op.drop_table('stores')
