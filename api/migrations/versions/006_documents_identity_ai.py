"""Documents, student identity collectible and AI call log

Revision ID: 006_documents_identity_ai
Revises: 005_policy_analytics_wellbeing
Create Date: 2026-11-01

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '006_documents_identity_ai'
down_revision = '005_policy_analytics_wellbeing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    now = sa.text('now()')
    op.create_table(
        'disha_documents',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('document_ref', sa.String(64), nullable=False),
        sa.Column('case_id', sa.String(36), sa.ForeignKey('disha_cases.id'), nullable=True),
        sa.Column('kind', sa.String(50), nullable=False, server_default='other'),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('storage_backend', sa.String(20), nullable=False),
        sa.Column('storage_key', sa.String(200), nullable=False),
        sa.Column('status', sa.String(30), nullable=False, server_default='draft'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('previous_version_id', sa.String(36), sa.ForeignKey('disha_documents.id'), nullable=True),
        sa.Column('uploaded_by', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=False),
        sa.Column('finalized_by', sa.String(36), nullable=True),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('anchor_requested_by', sa.String(36), nullable=True),
        sa.Column('anchor_requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('anchor_tx_hash', sa.String(80), nullable=True),
        sa.Column('anchor_submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('anchor_chain_id', sa.Integer(), nullable=True),
        sa.Column('anchor_block_number', sa.BigInteger(), nullable=True),
        sa.Column('anchored_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('anchor_error', sa.Text(), nullable=True),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_verification_ok', sa.String(5), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=now),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=now),
    )
    op.create_index('ix_disha_documents_campus_id', 'disha_documents', ['campus_id'])
    op.create_index('ix_disha_documents_document_ref', 'disha_documents', ['document_ref'], unique=True)
    op.create_index('ix_disha_documents_case_id', 'disha_documents', ['case_id'])
    op.create_index('ix_disha_documents_status', 'disha_documents', ['status'])
    op.create_index('ix_disha_documents_uploaded_by', 'disha_documents', ['uploaded_by'])

    op.create_table(
        'disha_student_identity',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('disha_roster.id'), nullable=False),
        sa.Column('disha_id', sa.String(24), nullable=False),
        sa.Column('id_hash', sa.String(64), nullable=False),
        sa.Column('art_seed', sa.String(64), nullable=False),
        sa.Column('wallet_address', sa.String(42), nullable=True),
        sa.Column('wallet_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='issued'),
        sa.Column('mint_requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('mint_tx_hash', sa.String(80), nullable=True),
        sa.Column('mint_submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('mint_chain_id', sa.BigInteger(), nullable=True),
        sa.Column('mint_block_number', sa.BigInteger(), nullable=True),
        sa.Column('minted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('mint_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=now),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=now),
        sa.UniqueConstraint('id_hash', name='uq_disha_student_identity_id_hash'),
    )
    op.create_index('ix_disha_student_identity_campus_id', 'disha_student_identity', ['campus_id'])
    op.create_index('ix_disha_student_identity_student_id', 'disha_student_identity', ['student_id'], unique=True)
    op.create_index('ix_disha_student_identity_disha_id', 'disha_student_identity', ['disha_id'], unique=True)
    op.create_index('ix_disha_student_identity_status', 'disha_student_identity', ['status'])

    op.create_table(
        'disha_wallet_challenges',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('identity_id', sa.String(36), sa.ForeignKey('disha_student_identity.id'), nullable=False),
        sa.Column('address', sa.String(42), nullable=False),
        sa.Column('nonce', sa.String(64), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=now),
    )
    op.create_index('ix_disha_wallet_challenges_identity_id', 'disha_wallet_challenges', ['identity_id'])

    op.create_table(
        'disha_ai_call_logs',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('feature', sa.String(50), nullable=False),
        sa.Column('subject_type', sa.String(20), nullable=True),
        sa.Column('subject_id', sa.String(36), nullable=True),
        sa.Column('provider', sa.String(30), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('prompt_version', sa.String(20), nullable=False),
        sa.Column('prompt_hash', sa.String(64), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('redactions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=now),
    )
    op.create_index('ix_disha_ai_call_logs_campus_id', 'disha_ai_call_logs', ['campus_id'])
    op.create_index('ix_disha_ai_call_logs_user_id', 'disha_ai_call_logs', ['user_id'])
    op.create_index('ix_disha_ai_call_logs_created_at', 'disha_ai_call_logs', ['created_at'])


def downgrade() -> None:
    op.drop_table('disha_ai_call_logs')
    op.drop_table('disha_wallet_challenges')
    op.drop_table('disha_student_identity')
    op.drop_table('disha_documents')
