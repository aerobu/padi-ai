"""003_add_stage2_tables

Revision ID: 003
Revises: 1a4a929746ac
Create Date: 2026-04-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '1a4a929746ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Stage 2 tables: learning_plans, plan_modules, plan_lessons,
    student_badges, student_streaks, generation_jobs, generated_questions,
    question_validation_results, content_review_queue, practice_sessions."""

    # === TABLE: learning_plans ===
    op.create_table(
        'learning_plans',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('assessment_id', sa.String(), nullable=True),
        sa.Column('track', sa.String(), nullable=False),
        sa.Column('status', sa.String(), default='active', nullable=False),
        sa.Column('total_modules', sa.Integer(), nullable=False),
        sa.Column('completed_modules', sa.Integer(), default=0, nullable=False),
        sa.Column('total_lessons', sa.Integer(), nullable=False),
        sa.Column('completed_lessons', sa.Integer(), default=0, nullable=False),
        sa.Column('estimated_total_minutes', sa.Integer(), nullable=False),
        sa.Column('actual_total_minutes', sa.Integer(), default=0, nullable=False),
        sa.Column('sessions_per_week', sa.Integer(), default=3, nullable=False),
        sa.Column('minutes_per_session', sa.Integer(), default=20, nullable=False),
        sa.Column('estimated_completion_date', sa.Date(), nullable=False),
        sa.Column('overall_progress', sa.Float(), default=0.0, nullable=False),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("track IN ('catch_up', 'on_track', 'accelerate')", name='ck_learning_plans_track'),
        sa.CheckConstraint("status IN ('draft', 'active', 'completed', 'archived', 'superseded')", name='ck_learning_plans_status'),
        sa.CheckConstraint('overall_progress >= 0.0 AND overall_progress <= 1.0', name='ck_learning_plans_progress_range'),
    )
    op.create_index('idx_learning_plans_student_active', 'learning_plans', ['student_id', 'status'], postgresql_where=sa.text("status = 'active'"))
    op.create_index('idx_learning_plans_assessment', 'learning_plans', ['assessment_id'])

    # === TABLE: plan_modules ===
    op.create_table(
        'plan_modules',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('plan_id', sa.String(), nullable=False),
        sa.Column('standard_id', sa.String(), nullable=False),
        sa.Column('sequence_order', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), default='locked', nullable=False),
        sa.Column('lesson_count', sa.Integer(), nullable=False),
        sa.Column('completed_lessons', sa.Integer(), default=0, nullable=False),
        sa.Column('estimated_minutes', sa.Integer(), nullable=False),
        sa.Column('actual_minutes', sa.Integer(), default=0, nullable=False),
        sa.Column('prerequisite_module_ids', postgresql.ARRAY(sa.String()), default=list),
        sa.Column('entry_p_mastery', sa.Float(), nullable=True),
        sa.Column('exit_p_mastery', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['learning_plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['standard_id'], ['standards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan_id', 'sequence_order', name='uq_module_plan_order'),
        sa.UniqueConstraint('plan_id', 'standard_id', name='uq_module_plan_standard'),
        sa.CheckConstraint("status IN ('locked', 'available', 'in_progress', 'completed', 'skipped')", name='ck_plan_modules_status'),
    )
    op.create_index('idx_plan_modules_plan_order', 'plan_modules', ['plan_id', 'sequence_order'])
    op.create_index('idx_plan_modules_status', 'plan_modules', ['plan_id', 'status'], postgresql_where=sa.text("status IN ('available', 'in_progress')"))

    # === TABLE: plan_lessons ===
    op.create_table(
        'plan_lessons',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('module_id', sa.String(), nullable=False),
        sa.Column('sequence_order', sa.Integer(), nullable=False),
        sa.Column('lesson_type', sa.String(), default='practice', nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('question_count', sa.Integer(), default=5, nullable=False),
        sa.Column('difficulty_range_min', sa.Integer(), nullable=True),
        sa.Column('difficulty_range_max', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), default='locked', nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('time_spent_ms', sa.Integer(), default=0, nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['module_id'], ['plan_modules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('module_id', 'sequence_order', name='uq_lesson_module_order'),
        sa.CheckConstraint("lesson_type IN ('instruction', 'practice', 'review', 'assessment')", name='ck_plan_lessons_type'),
        sa.CheckConstraint("status IN ('locked', 'available', 'in_progress', 'completed')", name='ck_plan_lessons_status'),
    )
    op.create_index('idx_plan_lessons_module_order', 'plan_lessons', ['module_id', 'sequence_order'])

    # === TABLE: student_badges ===
    op.create_table(
        'student_badges',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('badge_type', sa.String(), nullable=False),
        sa.Column('badge_name', sa.String(), nullable=False),
        sa.Column('badge_description', sa.Text(), nullable=False),
        sa.Column('badge_icon_url', sa.String(), nullable=False),
        sa.Column('badge_tier', sa.String(), default='bronze', nullable=False),
        sa.Column('earned_context', sa.JSON(), nullable=True),
        sa.Column('earned_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'badge_type', name='uq_student_badge'),
        sa.CheckConstraint("badge_tier IN ('bronze', 'silver', 'gold', 'platinum')", name='ck_badge_tier'),
    )
    op.create_index('idx_student_badges_student', 'student_badges', ['student_id', 'earned_at'], descending=[False, True])
    op.create_index('idx_student_badges_type', 'student_badges', ['badge_type'])

    # === TABLE: student_streaks ===
    op.create_table(
        'student_streaks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('current_streak_days', sa.Integer(), default=0, nullable=False),
        sa.Column('longest_streak_days', sa.Integer(), default=0, nullable=False),
        sa.Column('last_activity_date', sa.Date(), server_default=sa.func.current_date(), nullable=False),
        sa.Column('activity_dates', postgresql.ARRAY(sa.Date()), default=list),
        sa.Column('activities_this_week', sa.Integer(), default=0, nullable=False),
        sa.Column('activities_this_month', sa.Integer(), default=0, nullable=False),
        sa.Column('total_practice_sessions', sa.Integer(), default=0, nullable=False),
        sa.Column('total_questions_answered', sa.Integer(), default=0, nullable=False),
        sa.Column('total_time_spent_minutes', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', name='uq_student_streaks'),
    )
    op.create_index('idx_student_streaks_student', 'student_streaks', ['student_id'])
    op.create_index('idx_student_streaks_active', 'student_streaks', ['current_streak_days'], postgresql_where=sa.text('current_streak_days > 0'), descending=[True])

    # === TABLE: generation_jobs ===
    op.create_table(
        'generation_jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('standard_id', sa.String(), nullable=False),
        sa.Column('requested_count', sa.Integer(), nullable=False),
        sa.Column('difficulty_levels', postgresql.ARRAY(sa.Integer()), default=[1, 2, 3, 4, 5]),
        sa.Column('context_themes', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('model', sa.String(), default='o3-mini', nullable=False),
        sa.Column('status', sa.String(), default='queued', nullable=False),
        sa.Column('total_generated', sa.Integer(), default=0, nullable=True),
        sa.Column('auto_approved', sa.Integer(), default=0, nullable=True),
        sa.Column('needs_review', sa.Integer(), default=0, nullable=True),
        sa.Column('failed_validation', sa.Integer(), default=0, nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0, nullable=False),
        sa.Column('max_retries', sa.Integer(), default=3, nullable=False),
        sa.Column('input_tokens', sa.Integer(), default=0, nullable=True),
        sa.Column('output_tokens', sa.Integer(), default=0, nullable=True),
        sa.Column('estimated_cost_usd', sa.Float(), default=0.0, nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['standard_id'], ['standards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('queued', 'running', 'completed', 'failed', 'cancelled')", name='ck_generation_jobs_status'),
        sa.CheckConstraint('requested_count >= 1 AND requested_count <= 100', name='ck_generation_jobs_count_range'),
    )
    op.create_index('idx_generation_jobs_status', 'generation_jobs', ['status', 'created_at'], postgresql_where=sa.text("status = 'queued'"))
    op.create_index('idx_generation_jobs_created', 'generation_jobs', ['created_at'], descending=[True])
    op.create_index('idx_generation_jobs_standard', 'generation_jobs', ['standard_id'])

    # === TABLE: generated_questions ===
    op.create_table(
        'generated_questions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('standard_id', sa.String(), nullable=False),
        sa.Column('difficulty', sa.Integer(), nullable=False),
        sa.Column('question_type', sa.String(), default='multiple_choice', nullable=False),
        sa.Column('stem', sa.Text(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('correct_answer', sa.String(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('solution_code', sa.Text(), nullable=True),
        sa.Column('model_used', sa.String(), nullable=False),
        sa.Column('prompt_template', sa.String(), nullable=True),
        sa.Column('raw_response', sa.JSON(), nullable=True),
        sa.Column('generation_time_ms', sa.Integer(), nullable=True),
        sa.Column('validation_status', sa.String(), default='pending', nullable=False),
        sa.Column('confidence_score', sa.Float(), default=0.0, nullable=True),
        sa.Column('content_embedding', sa.ARRAY(sa.Float(), dimensions=1536), nullable=True),
        sa.Column('promoted_to_question_id', sa.String(), nullable=True),
        sa.Column('promoted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['generation_jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['standard_id'], ['standards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['promoted_to_question_id'], ['questions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("difficulty >= 1 AND difficulty <= 5", name='ck_generated_questions_difficulty'),
        sa.CheckConstraint("validation_status IN ('pending', 'passed', 'failed')", name='ck_generated_questions_validation'),
    )
    op.create_index('idx_generated_questions_job', 'generated_questions', ['job_id'])
    op.create_index('idx_generated_questions_validation', 'generated_questions', ['validation_status'])
    # Vector index for pgvector (if pgvector extension is enabled)
    op.create_index('idx_generated_questions_embedding', 'generated_questions', ['content_embedding'], postgresql_using='gin', postgresql_with={'lists': 50})

    # === TABLE: question_validation_results ===
    op.create_table(
        'question_validation_results',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('generated_question_id', sa.String(), nullable=False),
        sa.Column('solution_execution_passed', sa.Boolean(), default=False, nullable=False),
        sa.Column('solution_output', sa.Text(), nullable=True),
        sa.Column('solution_error', sa.Text(), nullable=True),
        sa.Column('solution_execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('age_appropriateness_passed', sa.Boolean(), default=False, nullable=False),
        sa.Column('age_appropriateness_score', sa.Float(), nullable=True),
        sa.Column('age_appropriateness_notes', sa.Text(), nullable=True),
        sa.Column('dedup_passed', sa.Boolean(), default=False, nullable=False),
        sa.Column('max_similarity_score', sa.Float(), nullable=True),
        sa.Column('similar_question_id', sa.String(), nullable=True),
        sa.Column('math_correctness_passed', sa.Boolean(), default=False, nullable=False),
        sa.Column('math_correctness_notes', sa.Text(), nullable=True),
        sa.Column('difficulty_alignment_passed', sa.Boolean(), default=False, nullable=False),
        sa.Column('estimated_difficulty', sa.Integer(), nullable=True),
        sa.Column('overall_passed', sa.Boolean(), default=False, nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['generated_question_id'], ['generated_questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_question_validation_results_gen_question', 'question_validation_results', ['generated_question_id'])

    # === TABLE: content_review_queue ===
    op.create_table(
        'content_review_queue',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('generated_question_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), default='pending', nullable=False),
        sa.Column('priority', sa.Integer(), default=5, nullable=False),
        sa.Column('assigned_to', sa.String(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decision_by', sa.String(), nullable=True),
        sa.Column('decision_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decision_notes', sa.Text(), nullable=True),
        sa.Column('edited_stem', sa.Text(), nullable=True),
        sa.Column('edited_options', sa.JSON(), nullable=True),
        sa.Column('edited_answer', sa.String(), nullable=True),
        sa.Column('edited_explanation', sa.Text(), nullable=True),
        sa.Column('flags', postgresql.ARRAY(sa.String()), default=list),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['generated_question_id'], ['generated_questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['decision_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("priority >= 1 AND priority <= 10", name='ck_content_review_priority'),
        sa.CheckConstraint("status IN ('pending', 'in_review', 'approved', 'rejected', 'needs_edit')", name='ck_content_review_status'),
    )
    # Index defined in __table_args__ of ContentReviewQueue model
    op.create_index('idx_content_review_assigned', 'content_review_queue', ['assigned_to', 'status'])

    # === TABLE: practice_sessions ===
    op.create_table(
        'practice_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('lesson_id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('standard_code', sa.String(), nullable=False),
        sa.Column('question_count', sa.Integer(), nullable=False),
        sa.Column('difficulty_target', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), default='in_progress', nullable=False),
        sa.Column('bkt_state_before', sa.JSON(), nullable=True),
        sa.Column('bkt_state_after', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['lesson_id'], ['plan_lessons.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('draft', 'in_progress', 'completed', 'abandoned')", name='ck_practice_sessions_status'),
    )
    op.create_index('idx_practice_sessions_student', 'practice_sessions', ['student_id', 'status'])
    op.create_index('idx_practice_sessions_lesson', 'practice_sessions', ['lesson_id'])

    # === TABLE: practice_session_questions ===
    op.create_table(
        'practice_session_questions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('question_id', sa.String(), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('difficulty', sa.Integer(), nullable=False),
        sa.Column('student_answer', sa.Text(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('points_earned', sa.Float(), nullable=True),
        sa.Column('time_spent_ms', sa.Integer(), nullable=True),
        sa.Column('hint_count', sa.Integer(), default=0, nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['practice_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_practice_session_questions_session', 'practice_session_questions', ['session_id'])
    op.create_index('idx_practice_session_questions_question', 'practice_session_questions', ['question_id'])

    # === SEED: prerequisite_relationships table (if using strength column) ===
    # Note: This migration assumes the prerequisite_relationships table already exists
    # from Stage 1. We're just adding the 'strength' column if it doesn't exist.
    try:
        # Check if strength column exists
        result = op.execute(sa.text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'prerequisite_relationships' AND column_name = 'strength'
        """))
        if not result.fetchone():
            # Add strength column to prerequisite_relationships
            op.add_column('prerequisite_relationships', sa.Column('strength', sa.String(), nullable=False, default='required'))
    except Exception:
        # Column might already exist, ignore
        pass

    # === SEED: prerequisite_relationships edges ===
    prerequisite_edges = [
        # Grade 3 -> Grade 4 prerequisites (required)
        ('3.OA.C.7', '4.OA.A.1', 'required'),
        ('3.OA.C.7', '4.OA.A.2', 'required'),
        ('3.OA.C.7', '4.NBT.B.5', 'required'),
        ('3.OA.C.7', '4.NBT.B.6', 'required'),
        ('3.OA.C.7', '4.NF.B.4', 'required'),
        ('3.OA.A.4', '4.OA.A.2', 'required'),
        ('3.OA.D.8', '4.OA.A.3', 'required'),
        ('3.NBT.A.2', '4.NBT.B.4', 'required'),
        ('3.NBT.A.3', '4.NBT.B.5', 'required'),
        ('3.NBT.A.2', '4.NBT.A.2', 'recommended'),
        ('3.NF.A.1', '4.NF.A.1', 'required'),
        ('3.NF.A.1', '4.NF.B.3', 'required'),
        ('3.NF.A.3', '4.NF.A.2', 'required'),
        ('3.GM.C.7', '4.GM.D.9', 'required'),
        ('3.GM.D.8', '4.GM.D.9', 'recommended'),

        # Grade 4 internal dependencies (required)
        ('4.NBT.A.1', '4.NBT.A.2', 'required'),
        ('4.NBT.A.2', '4.NBT.A.3', 'required'),
        ('4.NBT.B.4', '4.OA.A.3', 'required'),
        ('4.NBT.B.5', '4.OA.A.3', 'required'),
        ('4.NBT.B.5', '4.NBT.B.6', 'required'),
        ('4.NF.A.1', '4.NF.A.2', 'required'),
        ('4.NF.A.1', '4.NF.B.3', 'required'),
        ('4.NF.A.1', '4.NF.C.5', 'required'),
        ('4.NF.B.3', '4.NF.B.4', 'required'),
        ('4.NF.B.4', '4.DR.A.1', 'recommended'),
        ('4.NF.C.5', '4.NF.C.6', 'required'),
        ('4.NF.C.6', '4.NF.C.7', 'required'),
        ('4.NF.C.7', '4.DR.A.1', 'recommended'),
        ('4.GM.A.1', '4.GM.A.2', 'required'),
        ('4.GM.A.2', '4.GM.A.3', 'required'),
        ('4.GM.C.6', '4.GM.C.7', 'required'),
        ('4.GM.C.7', '4.GM.C.8', 'required'),
        ('4.GM.D.9', '4.GM.B.5', 'recommended'),
        ('4.OA.B.4', '4.OA.C.5', 'recommended'),
        ('4.DR.B.2', '4.DR.C.3', 'required'),
    ]

    for prereq_code, dependent_code, strength in prerequisite_edges:
        try:
            # Use insert to avoid duplicate key errors
            op.execute(sa.text("""
                INSERT INTO prerequisite_relationships (prerequisite_code, dependent_code, strength)
                VALUES (:prereq, :dep, :strength)
                ON CONFLICT (prerequisite_code, dependent_code) DO NOTHING
            """), {
                'prereq': prereq_code,
                'dep': dependent_code,
                'strength': strength
            })
        except Exception:
            # Edge might already exist, ignore
            pass


def downgrade() -> None:
    """Remove Stage 2 tables."""

    # Drop tables in reverse dependency order
    op.drop_table('practice_session_questions')
    op.drop_table('practice_sessions')
    op.drop_table('content_review_queue')
    op.drop_table('question_validation_results')
    op.drop_table('generated_questions')
    op.drop_table('generation_jobs')
    op.drop_table('student_streaks')
    op.drop_table('student_badges')
    op.drop_table('plan_lessons')
    op.drop_table('plan_modules')
    op.drop_table('learning_plans')
