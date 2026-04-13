"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table (parent accounts)
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('auth0_id', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('school_district', sa.String(), nullable=True),
        sa.Column('role', sa.String(), default='parent'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('auth0_id'),
        sa.UniqueConstraint('email'),
    )

    # Create students table
    op.create_table(
        'students',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('parent_id', sa.String(), nullable=False),
        sa.Column('grade_level', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['parent_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create consent_records table (COPPA compliance)
    op.create_table(
        'consent_records',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=True),
        sa.Column('consent_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='pending'),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('consented_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create standards table (Oregon math standards)
    op.create_table(
        'standards',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('standard_code', sa.String(), nullable=False),
        sa.Column('grade_level', sa.Integer(), nullable=False),
        sa.Column('domain', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('standard_code', 'grade_level'),
    )

    # Create prerequisite_relationships table
    op.create_table(
        'prerequisite_relationships',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('standard_id', sa.String(), nullable=False),
        sa.Column('prerequisite_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['standard_id'], ['standards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prerequisite_id'], ['standards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create questions table
    op.create_table(
        'questions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('standard_id', sa.String(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(), nullable=False),
        sa.Column('difficulty', sa.Integer(), nullable=False),
        sa.Column('points', sa.Integer(), default=1),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['standard_id'], ['standards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create question_options table
    op.create_table(
        'question_options',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('question_id', sa.String(), nullable=False),
        sa.Column('option_text', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), default=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create assessments table
    op.create_table(
        'assessments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('assessment_type', sa.String(), nullable=False),
        sa.Column('version', sa.String(), default='1.0'),
        sa.Column('status', sa.String(), default='draft'),
        sa.Column('total_score', sa.Float(), nullable=True),
        sa.Column('max_score', sa.Float(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create assessment_sessions table
    op.create_table(
        'assessment_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('assessment_id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), default='in_progress'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create assessment_responses table (partitioned)
    op.create_table(
        'assessment_responses',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('assessment_session_id', sa.String(), nullable=False),
        sa.Column('question_id', sa.String(), nullable=False),
        sa.Column('student_answer', sa.Text(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('points_earned', sa.Float(), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.Column('hint_count', sa.Integer(), default=0),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['assessment_session_id'], ['assessment_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create student_skill_states table (BKT knowledge tracing)
    op.create_table(
        'student_skill_states',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('standard_id', sa.String(), nullable=False),
        sa.Column('mastery_prob', sa.Float(), default=0.0),
        sa.Column('guess_prob', sa.Float(), default=0.1),
        sa.Column('slip_prob', sa.Float(), default=0.1),
        sa.Column('learning_rate', sa.Float(), default=0.1),
        sa.Column('times_practiced', sa.Integer(), default=0),
        sa.Column('last_practiced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['standard_id'], ['standards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'standard_id'),
    )

    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for performance
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_role', 'users', ['role'])
    op.create_index('idx_students_parent', 'students', ['parent_id'])
    op.create_index('idx_students_grade', 'students', ['grade_level'])
    op.create_index('idx_consent_user', 'consent_records', ['user_id'])
    op.create_index('idx_consent_status', 'consent_records', ['status'])
    op.create_index('idx_standards_grade', 'standards', ['grade_level'])
    op.create_index('idx_standards_code', 'standards', ['standard_code'])
    op.create_index('idx_questions_standard', 'questions', ['standard_id'])
    op.create_index('idx_questions_active', 'questions', ['is_active'])
    op.create_index('idx_assessments_student', 'assessments', ['student_id'])
    op.create_index('idx_assessments_type', 'assessments', ['assessment_type'])
    op.create_index('idx_assessment_sessions_student', 'assessment_sessions', ['student_id'])
    op.create_index('idx_assessment_responses_session', 'assessment_responses', ['assessment_session_id'])
    op.create_index('idx_skill_states_student', 'student_skill_states', ['student_id'])
    op.create_index('idx_audit_log_user', 'audit_log', ['user_id'])
    op.create_index('idx_audit_log_created', 'audit_log', ['created_at'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_audit_log_created', table_name='audit_log')
    op.drop_index('idx_audit_log_user', table_name='audit_log')
    op.drop_index('idx_skill_states_student', table_name='student_skill_states')
    op.drop_index('idx_assessment_responses_session', table_name='assessment_responses')
    op.drop_index('idx_assessment_sessions_student', table_name='assessment_sessions')
    op.drop_index('idx_assessments_type', table_name='assessments')
    op.drop_index('idx_assessments_student', table_name='assessments')
    op.drop_index('idx_questions_active', table_name='questions')
    op.drop_index('idx_questions_standard', table_name='questions')
    op.drop_index('idx_standards_code', table_name='standards')
    op.drop_index('idx_standards_grade', table_name='standards')
    op.drop_index('idx_consent_status', table_name='consent_records')
    op.drop_index('idx_consent_user', table_name='consent_records')
    op.drop_index('idx_students_grade', table_name='students')
    op.drop_index('idx_students_parent', table_name='students')
    op.drop_index('idx_users_role', table_name='users')
    op.drop_index('idx_users_email', table_name='users')

    # Drop tables in reverse order of creation
    op.drop_table('audit_log')
    op.drop_table('student_skill_states')
    op.drop_table('assessment_responses')
    op.drop_table('assessment_sessions')
    op.drop_table('assessments')
    op.drop_table('question_options')
    op.drop_table('questions')
    op.drop_table('prerequisite_relationships')
    op.drop_table('standards')
    op.drop_table('consent_records')
    op.drop_table('students')
    op.drop_table('users')
