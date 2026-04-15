"""
SQLAlchemy models for PADI.AI.
Maps to the database schema defined in ENG-001-stage1.md
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base


# === User/Student Models ===

class UserRole(str, Enum):
    PARENT = "parent"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    auth0_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    school_district = Column(String, nullable=True)
    role = Column(String, default=UserRole.PARENT.value)
    is_active = Column(Boolean, default=True)

    students = relationship("Student", back_populates="parent", cascade="all, delete-orphan")
    consent_records = relationship("ConsentRecord", back_populates="user", cascade="all, delete-orphan")


class Student(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True)
    parent_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    grade_level = Column(Integer, nullable=False, index=True)
    display_name = Column(String, nullable=False)
    avatar_id = Column(String, default="avatar_default")
    birth_year = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=None)
    updated_at = Column(DateTime(timezone=True), onupdate=None)

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

    standard = relationship("Standard", foreign_keys=[standard_id], back_populates="prerequisite_relationships_prereq")
    prerequisite = relationship("Standard", foreign_keys=[prerequisite_id], back_populates="prerequisite_relationships_prereq_of")


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
