"""
SQLAlchemy models for PADI.AI.
Maps to the database schema defined in ENG-001-stage1.md
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, BYTEA
# pgvector.sqlalchemy import Vector  # Uncomment when pgvector is installed
from sqlalchemy.orm import RelationshipProperty, relationship

from .base import Base
from src.core.encryption import EncryptionService

# Import Vector type for pgvector
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy import ARRAY, Float
    Vector = lambda dim: ARRAY(Float)  # fallback


# === User/Student Models ===

class UserRole(str, Enum):
    PARENT = "parent"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    auth0_id = Column(String, unique=True, index=True, nullable=True)

    # Encrypted PII (COPPA compliance)
    email_encrypted = Column(BYTEA, nullable=True)
    email_hash = Column(String(64), unique=True, index=True, nullable=False)

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    school_district = Column(String, nullable=True)
    role = Column(String, default=UserRole.PARENT.value)
    is_active = Column(Boolean, default=True)

    students = relationship("Student", back_populates="parent", cascade="all, delete-orphan")
    consent_records = relationship("ConsentRecord", back_populates="user", cascade="all, delete-orphan")

    def set_email(self, plaintext_email: str):
        """Encrypt email and set hash for lookups."""
        svc = EncryptionService()
        self.email_encrypted = svc.encrypt(plaintext_email)
        self.email_hash = svc.hash_for_lookup(plaintext_email.lower())

    def get_email(self) -> Optional[str]:
        """Decrypt and return email."""
        if not self.email_encrypted:
            return None
        svc = EncryptionService()
        return svc.decrypt(self.email_encrypted)


class Student(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True)
    parent_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    grade_level = Column(Integer, nullable=False, index=True)
    display_name = Column(String, nullable=False)
    avatar_id = Column(String, default="avatar_default")
    birth_year = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    parent = relationship("User", back_populates="students")
    assessments = relationship("Assessment", back_populates="student", cascade="all, delete-orphan")
    skill_states = relationship("StudentSkillState", back_populates="student", cascade="all, delete-orphan")
    assessment_sessions = relationship("AssessmentSession", back_populates="student", cascade="all, delete-orphan")


# === Consent Models ===

class ConsentType(str, Enum):
    DATA_PROCESSING = "data_processing"
    MEDIA_SHARING = "media_sharing"
    ANALYTICS = "analytics"


class ConsentStatus(str, Enum):
    PENDING = "pending"
    GRANTED = "granted"
    REVOKED = "revoked"


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String, ForeignKey("students.id", ondelete="SET NULL"), nullable=True)
    consent_type = Column(String, nullable=False)
    status = Column(String, default=ConsentStatus.PENDING.value, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    consented_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSON, nullable=True)

    user = relationship("User", back_populates="consent_records")
    student = relationship("Student")


# === Standards Models ===

class Standard(Base):
    __tablename__ = "standards"

    id = Column(String, primary_key=True)
    standard_code = Column(String, nullable=False)
    grade_level = Column(Integer, nullable=False, index=True)
    domain = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)

    questions = relationship("Question", back_populates="standard", cascade="all, delete-orphan")
    prerequisite_relationships_prereq = relationship(
        "PrerequisiteRelationship",
        foreign_keys="PrerequisiteRelationship.standard_id",
        back_populates="standard",
        cascade="all, delete-orphan",
    )
    prerequisite_relationships_prereq_of = relationship(
        "PrerequisiteRelationship",
        foreign_keys="PrerequisiteRelationship.prerequisite_id",
        back_populates="prerequisite",
        cascade="all, delete-orphan",
    )
    skill_states = relationship("StudentSkillState", back_populates="standard", cascade="all, delete-orphan")


class PrerequisiteRelationship(Base):
    __tablename__ = "prerequisite_relationships"

    id = Column(String, primary_key=True)
    standard_id = Column(String, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False)
    prerequisite_id = Column(String, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False)
    strength = Column(String, nullable=False, default="required")  # "required" | "recommended"

    standard = relationship("Standard", foreign_keys=[standard_id], back_populates="prerequisite_relationships_prereq")
    prerequisite = relationship("Standard", foreign_keys=[prerequisite_id], back_populates="prerequisite_relationships_prereq_of")


# === Stage 2: Learning Plans ===

class LearningPlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class LearningPlanTrack(str, Enum):
    CATCH_UP = "catch_up"
    ON_TRACK = "on_track"
    ACCELERATE = "accelerate"


class LearningPlan(Base):
    __tablename__ = "learning_plans"

    id = Column(String, primary_key=True)
    student_id = Column(String, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(String, ForeignKey("assessments.id", ondelete="SET NULL"), nullable=True)

    # Plan configuration
    track = Column(String, nullable=False)
    status = Column(String, default=LearningPlanStatus.ACTIVE.value, index=True)

    # Plan scope
    total_modules = Column(Integer, nullable=False)
    completed_modules = Column(Integer, default=0)
    total_lessons = Column(Integer, nullable=False)
    completed_lessons = Column(Integer, default=0)

    # Estimates
    estimated_total_minutes = Column(Integer, nullable=False)
    actual_total_minutes = Column(Integer, default=0)
    sessions_per_week = Column(Integer, default=3)
    minutes_per_session = Column(Integer, default=20)
    estimated_completion_date = Column(Date, nullable=False)

    # Progress (0.0 to 1.0)
    overall_progress = Column(Float, default=0.0)

    # Timestamps
    activated_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    student = relationship("Student", back_populates="learning_plans")
    assessment = relationship("Assessment")
    modules = relationship("PlanModule", back_populates="plan", cascade="all, delete-orphan")


class ModuleStatus(str, Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class PlanModule(Base):
    __tablename__ = "plan_modules"

    id = Column(String, primary_key=True)
    plan_id = Column(String, ForeignKey("learning_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    standard_id = Column(String, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False, index=True)

    # Module configuration
    sequence_order = Column(Integer, nullable=False)
    status = Column(String, default=ModuleStatus.LOCKED.value, index=True)

    # Lesson tracking
    lesson_count = Column(Integer, nullable=False)
    completed_lessons = Column(Integer, default=0)

    # Timing
    estimated_minutes = Column(Integer, nullable=False)
    actual_minutes = Column(Integer, default=0)

    # Prerequisite module IDs
    prerequisite_module_ids = Column("prerequisite_module_ids", ARRAY(String), default=list)

    # BKT state
    entry_p_mastery = Column(Float)
    exit_p_mastery = Column(Float)

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    plan = relationship("LearningPlan", back_populates="modules")
    lessons = relationship("PlanLesson", back_populates="module", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("plan_id", "sequence_order", name="uq_module_plan_order"),
        UniqueConstraint("plan_id", "standard_id", name="uq_module_plan_standard"),
    )


class LessonType(str, Enum):
    INSTRUCTION = "instruction"
    PRACTICE = "practice"
    REVIEW = "review"
    ASSESSMENT = "assessment"


class LessonStatus(str, Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class PlanLesson(Base):
    __tablename__ = "plan_lessons"

    id = Column(String, primary_key=True)
    module_id = Column(String, ForeignKey("plan_modules.id", ondelete="CASCADE"), nullable=False, index=True)

    sequence_order = Column(Integer, nullable=False)
    lesson_type = Column(String, default=LessonType.PRACTICE.value)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Lesson content
    question_count = Column(Integer, default=5)
    difficulty_range_min = Column(Integer)
    difficulty_range_max = Column(Integer)

    # Progress
    status = Column(String, default=LessonStatus.LOCKED.value, index=True)
    score = Column(Float)
    time_spent_ms = Column(Integer, default=0)

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    module = relationship("PlanModule", back_populates="lessons")

    __table_args__ = (
        UniqueConstraint("module_id", "sequence_order", name="uq_lesson_module_order"),
    )


# === Question Models ===

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    NUMERIC = "numeric"
    MULTI_STEP = "multi_step"


class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True)
    standard_id = Column(String, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=False)
    difficulty = Column(Integer, nullable=False)
    points = Column(Integer, default=1)
    is_active = Column(Boolean, default=True, index=True)
    metadata_json = Column(JSON, nullable=True)

    standard = relationship("Standard", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")
    assessment_responses = relationship("AssessmentResponse", back_populates="question", cascade="all, delete-orphan")


class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(String, primary_key=True)
    question_id = Column(String, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    explanation = Column(Text, nullable=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=None)

    question = relationship("Question", back_populates="options")


# === Assessment Models ===

class AssessmentType(str, Enum):
    DIAGNOSTIC = "diagnostic"
    PRACTICE = "practice"
    ASSESSMENT = "assessment"


class AssessmentStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String, primary_key=True)
    student_id = Column(String, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_type = Column(String, nullable=False, index=True)
    version = Column(String, default="1.0")
    status = Column(String, default=AssessmentStatus.DRAFT.value)
    total_score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    student = relationship("Student", back_populates="assessments")
    sessions = relationship("AssessmentSession", back_populates="assessment", cascade="all, delete-orphan")


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id = Column(String, primary_key=True)
    assessment_id = Column(String, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="in_progress")
    metadata_json = Column(JSON, nullable=True)

    assessment = relationship("Assessment", back_populates="sessions")
    student = relationship("Student", back_populates="assessment_sessions")
    responses = relationship("AssessmentResponse", back_populates="session", cascade="all, delete-orphan")


class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"

    id = Column(String, primary_key=True)
    assessment_session_id = Column(String, ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    student_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    points_earned = Column(Float, nullable=True)
    time_spent_seconds = Column(Integer, nullable=True)
    hint_count = Column(Integer, default=0)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("AssessmentSession", back_populates="responses")
    question = relationship("Question", back_populates="assessment_responses")


# === Knowledge Tracing Models ===

class StudentSkillState(Base):
    __tablename__ = "student_skill_states"

    id = Column(String, primary_key=True)
    student_id = Column(String, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    standard_id = Column(String, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False, index=True)
    mastery_prob = Column(Float, default=0.0)
    guess_prob = Column(Float, default=0.1)
    slip_prob = Column(Float, default=0.1)
    learning_rate = Column(Float, default=0.1)
    times_practiced = Column(Integer, default=0)
    last_practiced_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("Student", back_populates="skill_states")
    standard = relationship("Standard", back_populates="skill_states")

    __table_args__ = (
        # Already has primary_key on 'id', but adding unique constraint
        # UniqueConstraint('student_id', 'standard_id'),
    )

    @property
    def proficiency_level(self) -> str:
        """
        Derive proficiency level from mastery probability.

        Returns:
            "Above Par" if mastery_prob >= 0.80
            "Below Par" if mastery_prob <= 0.40
            "On Par" otherwise
        """
        if self.mastery_prob >= 0.80:
            return "Above Par"
        elif self.mastery_prob <= 0.40:
            return "Below Par"
        return "On Par"


# === Audit Models ===

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=None, index=True)


# === Stage 2: Badges & Streaks ===

class BadgeTier(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class StudentBadge(Base):
    __tablename__ = "student_badges"

    id = Column(String, primary_key=True)
    student_id = Column(String, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)

    badge_type = Column(String, nullable=False)
    badge_name = Column(String, nullable=False)
    badge_description = Column(Text, nullable=False)
    badge_icon_url = Column(String, nullable=False)
    badge_tier = Column(String, default=BadgeTier.BRONZE.value)

    # Context data
    earned_context = Column(JSON, nullable=True)

    earned_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("student_id", "badge_type", name="uq_student_badge"),
    )


class StudentStreak(Base):
    __tablename__ = "student_streaks"

    id = Column(String, primary_key=True)
    student_id = Column(String, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Current streak
    current_streak_days = Column(Integer, default=0)
    longest_streak_days = Column(Integer, default=0)

    # Last activity
    last_activity_date = Column(Date, default=func.current_date())

    # Activity log (array of dates)
    activity_dates = Column(ARRAY(Date), default=list)

    # Aggregates
    activities_this_week = Column(Integer, default=0)
    activities_this_month = Column(Integer, default=0)

    # Total stats
    total_practice_sessions = Column(Integer, default=0)
    total_questions_answered = Column(Integer, default=0)
    total_time_spent_minutes = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# === Stage 2: Generation Jobs ===

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String, primary_key=True)

    # Job spec
    standard_id = Column(String, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_count = Column(Integer, nullable=False)
    difficulty_levels = Column(ARRAY(Integer), default=[1, 2, 3, 4, 5])
    context_themes = Column(ARRAY(String), nullable=True)
    model = Column(String, default="o3-mini")

    # Job status
    status = Column(String, default=JobStatus.QUEUED.value, index=True)

    # Results
    total_generated = Column(Integer, default=0)
    auto_approved = Column(Integer, default=0)
    needs_review = Column(Integer, default=0)
    failed_validation = Column(Integer, default=0)

    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Cost tracking
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_by = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class GeneratedQuestion(Base):
    __tablename__ = "generated_questions"

    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    # Content (same schema as questions table)
    standard_id = Column(String, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False, index=True)
    difficulty = Column(Integer, nullable=False)
    question_type = Column(String, default="multiple_choice")
    stem = Column(Text, nullable=False)
    options = Column(JSON, nullable=False, default=list)
    correct_answer = Column(String, nullable=False)
    explanation = Column(Text, nullable=True)
    solution_code = Column(Text, nullable=True)

    # Generation metadata
    model_used = Column(String, nullable=False)
    prompt_template = Column(String, nullable=True)
    raw_response = Column(JSON, nullable=True)
    generation_time_ms = Column(Integer, nullable=True)

    # Validation results
    validation_status = Column(String, default="pending")
    confidence_score = Column(Float, default=0.0)

    # Embedding for dedup
    content_embedding = Column(ARRAY(Float), nullable=True)

    # Promotion tracking
    promoted_to_question_id = Column(String, ForeignKey("questions.id", ondelete="SET NULL"), nullable=True)
    promoted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ValidationStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


class QuestionValidationResult(Base):
    __tablename__ = "question_validation_results"

    id = Column(String, primary_key=True)
    generated_question_id = Column(
        String,
        ForeignKey("generated_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Individual validation checks
    solution_execution_passed = Column(Boolean, default=False)
    solution_output = Column(Text, nullable=True)
    solution_error = Column(Text, nullable=True)
    solution_execution_time_ms = Column(Integer, nullable=True)

    age_appropriateness_passed = Column(Boolean, default=False)
    age_appropriateness_score = Column(Float, nullable=True)
    age_appropriateness_notes = Column(Text, nullable=True)

    dedup_passed = Column(Boolean, default=False)
    max_similarity_score = Column(Float, nullable=True)
    similar_question_id = Column(String, nullable=True)

    math_correctness_passed = Column(Boolean, default=False)
    math_correctness_notes = Column(Text, nullable=True)

    difficulty_alignment_passed = Column(Boolean, default=False)
    estimated_difficulty = Column(Integer, nullable=True)

    # Aggregate
    overall_passed = Column(Boolean, default=False)
    confidence_score = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReviewPriority(str, Enum):
    LOW = 1
    MEDIUM = 5
    HIGH = 10


class ReviewStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_EDIT = "needs_edit"


class ContentReviewQueue(Base):
    __tablename__ = "content_review_queue"

    id = Column(String, primary_key=True)
    generated_question_id = Column(String, ForeignKey("generated_questions.id", ondelete="CASCADE"), nullable=False)

    status = Column(String, default=ReviewStatus.PENDING.value, index=True)
    priority = Column(Integer, default=ReviewPriority.MEDIUM.value)

    # Review assignment
    assigned_to = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)

    # Review decision
    decision_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decision_at = Column(DateTime(timezone=True), nullable=True)
    decision_notes = Column(Text, nullable=True)

    # If edited before approval
    edited_stem = Column(Text, nullable=True)
    edited_options = Column(JSON, nullable=True)
    edited_answer = Column(String, nullable=True)
    edited_explanation = Column(Text, nullable=True)

    # Flags from validation
    flags = Column(ARRAY(String), default=list)
    confidence_score = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("idx_review_pending", status, priority.desc(), created_at.desc(), postgresql_where=status.in_(["pending", "in_review"])),
    )


# === Stage 2: Practice Sessions ===

class PracticeSessionStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id = Column(String, primary_key=True)
    lesson_id = Column(String, ForeignKey("plan_lessons.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)

    # Target standard
    standard_code = Column(String, nullable=False)

    # Session config
    question_count = Column(Integer, nullable=False)
    difficulty_target = Column(Integer, nullable=True)

    # Status
    status = Column(String, default=PracticeSessionStatus.IN_PROGRESS.value, index=True)

    # BKT state
    bkt_state_before = Column(JSON, nullable=True)
    bkt_state_after = Column(JSON, nullable=True)

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PracticeSessionQuestion(Base):
    __tablename__ = "practice_session_questions"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("practice_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String, ForeignKey("generated_questions.id", ondelete="CASCADE"), nullable=False)

    sequence = Column(Integer, nullable=False)
    difficulty = Column(Integer, nullable=False)

    # Response
    student_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    points_earned = Column(Float, nullable=True)
    time_spent_ms = Column(Integer, nullable=True)
    hint_count = Column(Integer, default=0)

    # Timestamps
    answered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Add relationships to Student model
Student.learning_plans = relationship(
    "LearningPlan",
    back_populates="student",
    cascade="all, delete-orphan"
)
