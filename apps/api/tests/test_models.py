"""Tests for SQLAlchemy models."""

import pytest
from datetime import datetime


class TestUserModel:
    """Test User model structure and constraints."""

    def test_user_model_has_required_fields(self):
        """User model has required fields."""
        from src.models.models import User

        # Check that User has required attributes
        assert hasattr(User, '__tablename__')
        assert User.__tablename__ == 'users'

        # Check required columns exist
        columns = [c.name for c in User.__table__.columns]
        assert 'id' in columns
        assert 'email' in columns
        assert 'first_name' in columns
        assert 'last_name' in columns
        assert 'role' in columns

    def test_user_model_has_relationships(self):
        """User model has relationships."""
        from src.models.models import User

        relationships = [r.key for r in User.__mapper__.relationships]
        # Should have relationships to students and consent records
        assert 'students' in relationships
        assert 'consent_records' in relationships

    def test_user_role_enum_values(self):
        """User role has valid enum values."""
        from src.models.models import User

        user_parent = User(
            id="parent-1",
            email="parent@example.com",
            first_name="Parent",
            last_name="User",
            role="parent"
        )
        assert user_parent.role == "parent"

        user_teacher = User(
            id="teacher-1",
            email="teacher@example.com",
            first_name="Teacher",
            last_name="User",
            role="teacher"
        )
        assert user_teacher.role == "teacher"


class TestStudentModel:
    """Test Student model structure and constraints."""

    def test_student_model_has_required_fields(self):
        """Student model has required fields."""
        from src.models.models import Student

        columns = [c.name for c in Student.__table__.columns]
        assert 'id' in columns
        assert 'parent_id' in columns
        assert 'grade_level' in columns
        assert 'first_name' in columns
        assert 'last_name' in columns

    def test_student_model_has_relationships(self):
        """Student model has relationships."""
        from src.models.models import Student

        relationships = [r.key for r in Student.__mapper__.relationships]
        assert 'parent' in relationships
        assert 'assessments' in relationships
        assert 'skill_states' in relationships
        assert 'assessment_sessions' in relationships

    def test_student_grade_level_range(self):
        """Student grade level is integer."""
        from src.models.models import Student

        for grade in [1, 2, 3, 4, 5]:
            student = Student(
                id=f"student-{grade}",
                parent_id="parent-1",
                grade_level=grade,
                first_name=f"Student{grade}",
                last_name="Test"
            )
            assert student.grade_level == grade


class TestStandardModel:
    """Test Standard model structure and constraints."""

    def test_standard_model_has_required_fields(self):
        """Standard model has required fields."""
        from src.models.models import Standard

        columns = [c.name for c in Standard.__table__.columns]
        assert 'id' in columns
        assert 'standard_code' in columns
        assert 'grade_level' in columns
        assert 'domain' in columns
        assert 'title' in columns
        assert 'description' in columns

    def test_standard_creation(self):
        """Standard can be created."""
        from src.models.models import Standard

        standard = Standard(
            id="std-1",
            standard_code="NBT.A.1",
            grade_level=4,
            domain="Numbers and Operations",
            title="Place Value",
            description="Understand place value relationships"
        )

        assert standard.standard_code == "NBT.A.1"
        assert standard.grade_level == 4


class TestQuestionModel:
    """Test Question model structure and constraints."""

    def test_question_model_has_required_fields(self):
        """Question model has required fields."""
        from src.models.models import Question

        columns = [c.name for c in Question.__table__.columns]
        assert 'id' in columns
        assert 'standard_id' in columns
        assert 'question_text' in columns
        assert 'question_type' in columns
        assert 'difficulty' in columns
        assert 'points' in columns

    def test_question_type_enum_values(self):
        """Question has valid type values."""
        from src.models.models import Question

        for qtype in ["multiple_choice", "numeric", "multi_step"]:
            question = Question(
                id=f"q-{qtype}",
                standard_id="std-1",
                question_text="Test question",
                question_type=qtype,
                difficulty=1,
                points=1
            )
            assert question.question_type == qtype

    def test_question_option_model(self):
        """QuestionOption model has required fields."""
        from src.models.models import QuestionOption

        columns = [c.name for c in QuestionOption.__table__.columns]
        assert 'id' in columns
        assert 'question_id' in columns
        assert 'option_text' in columns
        assert 'is_correct' in columns


class TestAssessmentModel:
    """Test Assessment model structure and constraints."""

    def test_assessment_model_has_required_fields(self):
        """Assessment model has required fields."""
        from src.models.models import Assessment

        columns = [c.name for c in Assessment.__table__.columns]
        assert 'id' in columns
        assert 'student_id' in columns
        assert 'assessment_type' in columns
        assert 'version' in columns
        assert 'status' in columns
        assert 'total_score' in columns
        assert 'max_score' in columns


class TestStudentSkillStateModel:
    """Test StudentSkillState model (BKT knowledge tracing)."""

    def test_skill_state_model_has_required_fields(self):
        """Skill state model has required fields."""
        from src.models.models import StudentSkillState

        columns = [c.name for c in StudentSkillState.__table__.columns]
        assert 'id' in columns
        assert 'student_id' in columns
        assert 'standard_id' in columns
        assert 'mastery_prob' in columns
        assert 'guess_prob' in columns
        assert 'slip_prob' in columns
        assert 'learning_rate' in columns
        assert 'times_practiced' in columns
        assert 'last_practiced_at' in columns

    def test_skill_state_creation(self):
        """Skill state can be created."""
        from src.models.models import StudentSkillState

        state = StudentSkillState(
            id="state-1",
            student_id="student-1",
            standard_id="NBT.A.1",
            mastery_prob=0.5,
            guess_prob=0.1,
            slip_prob=0.1,
            learning_rate=0.1,
            times_practiced=5,
            last_practiced_at=datetime.utcnow()
        )

        assert state.student_id == "student-1"
        assert state.mastery_prob == 0.5

    def test_skill_state_update(self):
        """Skill state can be updated."""
        from src.models.models import StudentSkillState

        state = StudentSkillState(
            id="state-update-1",
            student_id="student-1",
            standard_id="NBT.A.1",
            mastery_prob=0.3,
            guess_prob=0.1,
            slip_prob=0.1,
            learning_rate=0.1,
            times_practiced=3
        )

        # Update state
        state.mastery_prob = 0.9
        state.times_practiced = 10
        state.last_practiced_at = datetime.utcnow()

        assert state.mastery_prob == 0.9
        assert state.times_practiced == 10


class TestConsentRecordModel:
    """Test ConsentRecord model."""

    def test_consent_record_model_has_required_fields(self):
        """Consent record model has required fields."""
        from src.models.models import ConsentRecord

        columns = [c.name for c in ConsentRecord.__table__.columns]
        assert 'id' in columns
        assert 'user_id' in columns
        assert 'student_id' in columns
        assert 'consent_type' in columns
        assert 'status' in columns
        assert 'consented_at' in columns
        assert 'metadata_json' in columns

    def test_consent_record_creation(self):
        """Consent record can be created."""
        from src.models.models import ConsentRecord, ConsentStatus

        consent = ConsentRecord(
            id="consent-1",
            user_id="user-1",
            student_id="student-1",
            consent_type="data_processing",
            status=ConsentStatus.GRANTED.value,
            consented_at=datetime.utcnow()
        )

        assert consent.consent_type == "data_processing"
        assert consent.status == ConsentStatus.GRANTED.value


class TestPrerequisiteRelationshipModel:
    """Test PrerequisiteRelationship model."""

    def test_prerequisite_relationship_model_has_required_fields(self):
        """Prerequisite relationship has required fields."""
        from src.models.models import PrerequisiteRelationship

        columns = [c.name for c in PrerequisiteRelationship.__table__.columns]
        assert 'id' in columns
        assert 'standard_id' in columns
        assert 'prerequisite_id' in columns

    def test_prerequisite_creation(self):
        """Prerequisite relationship can be created."""
        from src.models.models import PrerequisiteRelationship

        prereq = PrerequisiteRelationship(
            id="prereq-1",
            standard_id="NBT.A.2",  # Advanced
            prerequisite_id="NBT.A.1"  # Base
        )

        assert prereq.standard_id == "NBT.A.2"
        assert prereq.prerequisite_id == "NBT.A.1"


class TestQuestionOptionModel:
    """Test QuestionOption model."""

    def test_question_option_model_has_required_fields(self):
        """Question option has required fields."""
        from src.models.models import QuestionOption

        columns = [c.name for c in QuestionOption.__table__.columns]
        assert 'id' in columns
        assert 'question_id' in columns
        assert 'option_text' in columns
        assert 'is_correct' in columns
        assert 'explanation' in columns
        assert 'order' in columns

    def test_question_option_creation(self):
        """Question option can be created."""
        from src.models.models import QuestionOption

        option = QuestionOption(
            id="option-1",
            question_id="question-1",
            option_text="The correct answer",
            is_correct=True,
            order=1
        )

        assert option.is_correct is True
        assert option.option_text == "The correct answer"

    def test_question_option_wrong_answer(self):
        """Question option with wrong answer can be created."""
        from src.models.models import QuestionOption

        option = QuestionOption(
            id="option-2",
            question_id="question-1",
            option_text="The wrong answer",
            is_correct=False,
            order=2
        )

        assert option.is_correct is False


class TestAssessmentResponseModel:
    """Test AssessmentResponse model."""

    def test_assessment_response_model_has_required_fields(self):
        """Assessment response has required fields."""
        from src.models.models import AssessmentResponse

        columns = [c.name for c in AssessmentResponse.__table__.columns]
        assert 'id' in columns
        assert 'assessment_session_id' in columns
        assert 'question_id' in columns
        assert 'student_answer' in columns
        assert 'is_correct' in columns
        assert 'points_earned' in columns
        assert 'time_spent_seconds' in columns

    def test_assessment_response_creation(self):
        """Assessment response can be created."""
        from src.models.models import AssessmentResponse

        response = AssessmentResponse(
            id="resp-1",
            assessment_session_id="session-1",
            question_id="q-1",
            student_answer="42",
            is_correct=True,
            points_earned=1.0,
            time_spent_seconds=120
        )

        assert response.student_answer == "42"
        assert response.is_correct is True
