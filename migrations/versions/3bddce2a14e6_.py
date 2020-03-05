"""empty message

Revision ID: 3bddce2a14e6
Revises: a79b9a931dbb
Create Date: 2020-03-03 10:04:46.081048

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import expression, func


# revision identifiers, used by Alembic.
revision = '3bddce2a14e6'
down_revision = 'a79b9a931dbb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('is_active')
        batch_op.alter_column(
            column_name='verified',
            new_column_name='is_verified',
            nullable=False,
            server_default=expression.false()
        )
        batch_op.alter_column(
            column_name='admin_approved',
            new_column_name='is_active',
            nullable=False,
            server_default=expression.false()
        )
        batch_op.alter_column(
            column_name='admin_rights',
            new_column_name='is_admin',
            nullable=False,
            server_default=expression.false()
        )
        batch_op.alter_column(
            column_name='username',
            nullable=False
        )
        batch_op.alter_column(
            column_name='email',
            nullable=False
        )
        batch_op.alter_column(
            column_name='password',
            nullable=False
        )
        batch_op.alter_column(
            column_name='date created',
            new_column_name='date_created',
            nullable=False,
            server_default=func.now()
        )
        batch_op.alter_column(
            column_name='last query',
            new_column_name='last_query',
            nullable=True
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.BOOLEAN(), nullable=False))

    # ### end Alembic commands ###