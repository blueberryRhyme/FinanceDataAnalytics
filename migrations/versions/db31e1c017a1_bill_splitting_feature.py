"""Bill splitting feature

Revision ID: db31e1c017a1
Revises: af456b3a9dc8
Create Date: 2025-05-11 11:31:37.736695

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'db31e1c017a1'
down_revision = 'af456b3a9dc8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('bill',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('total', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('settled', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('bill_member',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bill_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('share', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('paid', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('settled', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['bill_id'], ['bill.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('transaction_friend',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('transaction_id', sa.Integer(), nullable=False),
    sa.Column('friend_id', sa.Integer(), nullable=False),
    sa.Column('confidence', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['friend_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('transaction_friend')
    op.drop_table('bill_member')
    op.drop_table('bill')
    # ### end Alembic commands ###
