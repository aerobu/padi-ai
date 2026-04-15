"""Tests for student repository."""

import pytest


class TestStudentRepository:
    """Test StudentRepository."""

    @pytest.fixture
    def repository(self, session):
        """Create StudentRepository for tests."""
        from src.repositories.student_repository import StudentRepository

        return StudentRepository(session)

    def test_get_by_parent_id(self, repository, user):
        """get_by_parent_id returns all students for parent."""
        from src.models.models import Student

        student1 = Student(
            id="student-1",
            parent_id=user.id,
            grade_level=4,
            display_name="Student 1",
        )
        student2 = Student(
            id="student-2",
            parent_id=user.id,
            grade_level=5,
            display_name="Student 2",
        )
        repository.session.add(student1)
        repository.session.add(student2)
        repository.session.commit()

        results = repository.get_by_parent_id(user.id)

        assert len(results) == 2
        student_ids = {s.id for s in results}
        assert "student-1" in student_ids
        assert "student-2" in student_ids

    def test_get_by_parent_id_none(self, repository, user):
        """get_by_parent_id returns empty list when no students."""
        results = repository.get_by_parent_id(user.id)
        assert results == []

    def test_create_with_consent_check(self, repository, user):
        """create_with_consent_check creates student with active consent."""
        student = repository.create_with_consent_check(
            data={
                "display_name": "Test Student",
                "grade_level": 4,
            },
            parent_id=user.id,
            has_active_consent=True,
        )

        assert student.parent_id == user.id
        assert student.display_name == "Test Student"
        assert student.grade_level == 4

    def test_create_with_consent_check_no_consent(self, repository, user):
        """create_with_consent_check raises error without consent."""
        with pytest.raises(ValueError, match="Active COPPA consent required"):
            repository.create_with_consent_check(
                data={
                    "display_name": "Test Student",
                    "grade_level": 4,
                },
                parent_id=user.id,
                has_active_consent=False,
            )

    def test_update_skill_summary(self, repository, student):
        """update_skill_summary calculates skill summary."""
        from src.models.models import StudentSkillState

        # Add skill states
        state1 = StudentSkillState(
            student_id=student.id,
            standard_id="4.NBT.A.1",
            p_mastery=0.85,  # mastered
        )
        state2 = StudentSkillState(
            student_id=student.id,
            standard_id="4.NF.A.1",
            p_mastery=0.70,  # on_par
        )
        state3 = StudentSkillState(
            student_id=student.id,
            standard_id="4.OA.A.1",
            p_mastery=0.45,  # below_par
        )
        repository.session.add_all([state1, state2, state3])
        repository.session.commit()

        summary = repository.update_skill_summary(student.id)

        assert summary["total_standards"] == 3
        assert summary["mastered"] == 1
        assert summary["on_par"] == 1
        assert summary["below_par"] == 1
        assert summary["not_assessed"] == 0

    def test_delete(self, repository, student):
        """delete removes student."""
        result = repository.delete(student.id)

        assert result is True

        # Verify deletion
        from src.models.models import Student
        remaining = repository.session.query(Student).filter_by(id=student.id).first()
        assert remaining is None


class TestStudentRepositoryWithAssessments:
    """Test StudentRepository with assessment relationships."""

    @pytest.fixture
    def repository(self, session, student):
        """Create StudentRepository for tests."""
        from src.repositories.student_repository import StudentRepository

        return StudentRepository(session)

    def test_get_with_latest_assessment(self, repository, student):
        """get_with_latest_assessment includes latest assessment."""
        from src.models.models import Assessment

        # Create older assessment
        older = Assessment(
            id="assess-older",
            student_id=student.id,
            assessment_type="diagnostic",
            status="completed",
        )

        # Create newer assessment
        newer = Assessment(
            id="assess-newer",
            student_id=student.id,
            assessment_type="diagnostic",
            status="in_progress",
        )

        repository.session.add_all([older, newer])
        repository.session.commit()

        result = repository.get_with_latest_assessment(student.id)

        assert result is not None
        assert result.latest_assessment is not None
        assert result.latest_assessment.id == "assess-newer"

    def test_get_with_latest_assessment_none(self, repository, student):
        """get_with_latest_assessment returns None when no assessments."""
        result = repository.get_with_latest_assessment(student.id)

        assert result is not None
        assert result.latest_assessment is None
