"""initial

Revision ID: 001_initial
Revises: 
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute("CREATE EXTENSION IF NOT EXISTS pgvector;")

    op.create_table(
        'projects',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )

    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('input', sa.JSON),
        sa.Column('result', sa.JSON),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )

    op.create_table(
        'artifacts',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('job_id', sa.Integer, sa.ForeignKey('jobs.id')),
        sa.Column('filename', sa.String(512)),
        sa.Column('content_type', sa.String(128)),
        sa.Column('url', sa.String(1024)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    op.create_table(
        'agent_messages',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('job_id', sa.Integer, sa.ForeignKey('jobs.id')),
        sa.Column('role', sa.String(64)),
        sa.Column('content', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    op.create_table(
        'test_runs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('job_id', sa.Integer, sa.ForeignKey('jobs.id')),
        sa.Column('status', sa.String(50)),
        sa.Column('results', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    op.create_table(
        'bug_reports',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('test_run_id', sa.Integer, sa.ForeignKey('test_runs.id')),
        sa.Column('description', sa.Text),
        sa.Column('severity', sa.String(50)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    op.create_table(
        'security_findings',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('test_run_id', sa.Integer, sa.ForeignKey('test_runs.id')),
        sa.Column('rule', sa.String(255)),
        sa.Column('details', sa.Text),
        sa.Column('severity', sa.String(50)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )


def downgrade():
    op.drop_table('security_findings')
    op.drop_table('bug_reports')
    op.drop_table('test_runs')
    op.drop_table('agent_messages')
    op.drop_table('artifacts')
    op.drop_table('jobs')
    op.drop_table('projects')
