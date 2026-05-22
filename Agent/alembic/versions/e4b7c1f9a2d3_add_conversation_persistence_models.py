"""add conversation persistence models

Revision ID: e4b7c1f9a2d3
Revises: 83d869ecc25b
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4b7c1f9a2d3'
down_revision: Union[str, Sequence[str], None] = '83d869ecc25b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'conversation',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE', name=op.f('fk_conversation_user_id_user')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_conversation'))
    )
    op.create_index(op.f('ix_conversation_user_id'), 'conversation', ['user_id'], unique=False)

    op.create_table(
        'message',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=10), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('uploaded_filename', sa.String(length=200), nullable=True),
        sa.Column('session_file_id', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversation.id'], ondelete='CASCADE', name=op.f('fk_message_conversation_id_conversation')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_message'))
    )
    op.create_index(op.f('ix_message_conversation_id'), 'message', ['conversation_id'], unique=False)

    op.create_table(
        'conversation_file',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('session_file_id', sa.String(length=50), nullable=False),
        sa.Column('filename', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversation.id'], ondelete='CASCADE', name=op.f('fk_conversation_file_conversation_id_conversation')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_conversation_file'))
    )
    op.create_index(op.f('ix_conversation_file_conversation_id'), 'conversation_file', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_conversation_file_session_file_id'), 'conversation_file', ['session_file_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_conversation_file_session_file_id'), table_name='conversation_file')
    op.drop_index(op.f('ix_conversation_file_conversation_id'), table_name='conversation_file')
    op.drop_table('conversation_file')

    op.drop_index(op.f('ix_message_conversation_id'), table_name='message')
    op.drop_table('message')

    op.drop_index(op.f('ix_conversation_user_id'), table_name='conversation')
    op.drop_table('conversation')
