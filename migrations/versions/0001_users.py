"""create users table"""
from alembic import op
import sqlalchemy as sa
revision='0001_users'; down_revision=None; branch_labels=None; depends_on=None
def upgrade():
    op.create_table('users',sa.Column('id',sa.Integer,primary_key=True),sa.Column('username',sa.String(80),nullable=False),sa.Column('display_name',sa.String(120),nullable=False),sa.Column('password_hash',sa.String(128),nullable=False),sa.Column('role',sa.String(30),nullable=False,server_default='viewer'),sa.Column('status',sa.String(30),nullable=False,server_default='active')); op.create_index('ix_users_username','users',['username'],unique=True)
def downgrade(): op.drop_index('ix_users_username',table_name='users'); op.drop_table('users')
