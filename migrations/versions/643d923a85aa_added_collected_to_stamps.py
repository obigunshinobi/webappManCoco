"""Added collected to stamps

Revision ID: 643d923a85aa
Revises: 7cb4fbd1a610
Create Date: 2023-06-19 11:26:25.984363

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '643d923a85aa'
down_revision = '7cb4fbd1a610'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('stamp', schema=None) as batch_op:
        batch_op.add_column(sa.Column('collected', sa.Boolean(), nullable=True))

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('password')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password', sa.TEXT(), nullable=True))

    with op.batch_alter_table('stamp', schema=None) as batch_op:
        batch_op.drop_column('collected')

    # ### end Alembic commands ###
