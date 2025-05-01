"""update question and answer models

Revision ID: 80bbab6a146a
Revises: a6ee2a3952c8
Create Date: 2024-03-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '80bbab6a146a'
down_revision = 'a6ee2a3952c8'
branch_labels = None
depends_on = None


def upgrade():
    # Rename content to answer_text in answers table
    with op.batch_alter_table('answers', schema=None) as batch_op:
        batch_op.alter_column('content', new_column_name='answer_text')
    
    # Add auction_id to questions table
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('auction_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_questions_auction_id', 'auctions', ['auction_id'], ['id'])
        
        # Rename content to question_text
        batch_op.alter_column('content', new_column_name='question_text')
        
        # Add is_answered column
        batch_op.add_column(sa.Column('is_answered', sa.Boolean(), nullable=True, server_default='0'))
        
        # Remove title and status columns
        batch_op.drop_column('title')
        batch_op.drop_column('status')


def downgrade():
    # Revert changes in questions table
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('title', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=True))
        batch_op.alter_column('question_text', new_column_name='content')
        batch_op.drop_column('is_answered')
        batch_op.drop_constraint('fk_questions_auction_id', type_='foreignkey')
        batch_op.drop_column('auction_id')
    
    # Revert changes in answers table
    with op.batch_alter_table('answers', schema=None) as batch_op:
        batch_op.alter_column('answer_text', new_column_name='content')
