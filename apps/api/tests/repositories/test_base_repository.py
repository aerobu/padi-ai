"""Tests for base repository."""

import pytest


class TestAsyncRepository:
    """Test AsyncRepository base class."""

    @pytest.fixture
    def repository(self, session):
        """Create StudentRepository for tests."""
        from src.repositories.student_repository import StudentRepository

        return StudentRepository(session)

    def test_get_by_id(self, repository, student):
        """get_by_id retrieves record by ID."""
        result = repository.get_by_id(student.id)

        assert result is not None
        assert result.id == student.id
        assert result.display_name == student.display_name

    def test_get_by_id_not_found(self, repository, student):
        """get_by_id returns None for missing record."""
        result = repository.get_by_id("missing-id")
        assert result is None

    def test_get_all(self, repository, student, student2):
        """get_all returns all records."""
        results = repository.get_all(limit=100)

        assert len(results) == 2

    def test_get_all_with_pagination(self, repository, student, student2):
        """get_all respects pagination."""
        results = repository.get_all(limit=1, offset=0)

        assert len(results) == 1

        results = repository.get_all(limit=1, offset=1)

        assert len(results) == 1
        assert results[0].id != student.id

    def test_create(self, repository, user):
        """create adds new record."""
        student = repository.create({
            "parent_id": user.id,
            "grade_level": 4,
            "display_name": "New Student",
        })

        assert student.id is not None
        assert student.parent_id == user.id
        assert student.display_name == "New Student"

    def test_create_returns_instance(self, repository, user):
        """create returns SQLAlchemy model instance."""
        from src.models.models import Student

        student = repository.create({
            "parent_id": user.id,
            "grade_level": 4,
            "display_name": "New Student",
        })

        assert isinstance(student, Student)

    def test_update(self, repository, student):
        """update modifies existing record."""
        result = repository.update(student.id, {
            "display_name": "Updated Student",
        })

        assert result is not None
        assert result.display_name == "Updated Student"

    def test_update_not_found(self, repository, student):
        """update returns None for missing record."""
        result = repository.update("missing-id", {"display_name": "Updated"})
        assert result is None

    def test_delete(self, repository, student):
        """delete removes record."""
        result = repository.delete(student.id)

        assert result is True

        # Verify deletion
        remaining = repository.get_by_id(student.id)
        assert remaining is None

    def test_delete_not_found(self, repository, student):
        """delete returns False for missing record."""
        result = repository.delete("missing-id")
        assert result is False

    def test_exists(self, repository, student):
        """exists returns True for existing record."""
        result = repository.exists(student.id)
        assert result is True

    def test_exists_not_found(self, repository, student):
        """exists returns False for missing record."""
        result = repository.exists("missing-id")
        assert result is False

    def test_count(self, repository, student, student2):
        """count returns total number of records."""
        count = repository.count()

        assert count == 2
