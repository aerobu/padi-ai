"""Tests for question repository."""

import pytest


class TestQuestionRepository:
    """Test QuestionRepository."""

    @pytest.fixture
    def repository(self, session):
        """Create QuestionRepository for tests."""
        from src.repositories.question_repository import QuestionRepository

        return QuestionRepository(session)

    def test_get_by_standard_id(self, repository, standard, questions):
        """get_by_standard_id returns questions for standard."""
        results = repository.get_by_standard_id(standard.id)

        assert len(results) == 2
        question_ids = {q.id for q in results}
        assert "q1" in question_ids
        assert "q2" in question_ids

    def test_get_by_standard_id_inactive(self, repository, standard, questions):
        """get_by_standard_id excludes inactive questions."""
        from src.models.models import Question

        # Create inactive question
        inactive = Question(
            id="q-inactive",
            standard_id=standard.id,
            question_text="Inactive?",
            question_type="multiple_choice",
            difficulty=3,
            is_active=False,
        )
        repository.session.add(inactive)
        repository.session.commit()

        results = repository.get_by_standard_id(standard.id)

        # Should not include inactive question
        question_ids = {q.id for q in results}
        assert "q-inactive" not in question_ids

    def test_get_available_questions(self, repository, standard, questions):
        """get_available_questions returns filtered questions."""
        results = repository.get_available_questions(
            standard_ids=[standard.id],
            limit=10,
        )

        assert len(results) == 2

    def test_get_available_questions_with_difficulty_filter(self, repository, standard, questions):
        """get_available_questions filters by difficulty."""
        results = repository.get_available_questions(
            standard_ids=[standard.id],
            difficulty=3,
            limit=10,
        )

        # Should only return difficulty 3 questions
        for q in results:
            assert q.difficulty == 3

    def test_get_available_questions_exclude_ids(self, repository, standard, questions):
        """get_available_questions excludes specified IDs."""
        results = repository.get_available_questions(
            standard_ids=[standard.id],
            exclude_ids=["q1"],
            limit=10,
        )

        question_ids = {q.id for q in results}
        assert "q1" not in question_ids
        assert "q2" in question_ids

    def test_get_question_with_options(self, repository, standard, questions):
        """get_question_with_options returns question with options."""
        result = repository.get_question_with_options("q1")

        assert result is not None
        assert result["id"] == "q1"
        assert result["question_text"] == "Test question 1?"
        assert result["question_type"] == "multiple_choice"
        assert len(result["options"]) == 2
        assert result["options"][0]["is_correct"] is True
        assert result["options"][1]["is_correct"] is False

    def test_get_question_with_options_not_found(self, repository, standard, questions):
        """get_question_with_options returns None for missing question."""
        result = repository.get_question_with_options("missing-question")
        assert result is None

    def test_get_questions_by_difficulty_range(self, repository, standard, questions):
        """get_questions_by_difficulty_range returns questions in range."""
        results = repository.get_questions_by_difficulty_range(
            min_difficulty=3,
            max_difficulty=4,
            limit=10,
        )

        for q in results:
            assert 3 <= q.difficulty <= 4

    def test_get_questions_by_difficulty_range_exclude(self, repository, standard, questions):
        """get_questions_by_difficulty_range excludes specified IDs."""
        results = repository.get_questions_by_difficulty_range(
            min_difficulty=1,
            max_difficulty=5,
            exclude_ids=["q1"],
            limit=10,
        )

        question_ids = {q.id for q in results}
        assert "q1" not in question_ids

    def test_increment_shown_count(self, repository, standard, questions):
        """increment_shown_count increments times_shown."""
        # Initially should be 0 or None
        result = repository.increment_shown_count("q1")

        assert result is True

        # Refresh to check update
        from src.models.models import Question
        q = repository.session.query(Question).filter_by(id="q1").first()
        assert q.times_shown >= 1


class TestQuestionRepositoryWithPrerequisites:
    """Test QuestionRepository with prerequisite relationships."""

    @pytest.fixture
    def repository(self, session):
        """Create QuestionRepository for tests."""
        from src.repositories.question_repository import QuestionRepository

        return QuestionRepository(session)

    def test_get_available_questions_order_by_difficulty(self, repository, standard, questions):
        """get_available_questions orders by difficulty then ID."""
        results = repository.get_available_questions(
            standard_ids=[standard.id],
            limit=10,
        )

        # Results should be ordered
        for i in range(len(results) - 1):
            if results[i].difficulty == results[i + 1].difficulty:
                assert results[i].id <= results[i + 1].id
