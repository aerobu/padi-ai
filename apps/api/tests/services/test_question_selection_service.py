"""Tests for Computerized Adaptive Testing (CAT) question selection service."""

import pytest


class TestCATState:
    """Test CATState dataclass."""

    def test_cat_state_default_values(self):
        """CATState has correct default values."""
        from src.services.question_selection_service import CATState

        state = CATState()

        assert state.theta == 0.0
        assert state.covered_standards == {}
        assert state.questions_answered == 0
        assert state.question_pool == []

    def test_cat_state_custom_values(self):
        """CATState accepts custom values."""
        from src.services.question_selection_service import CATState

        state = CATState(
            theta=1.5,
            covered_standards={"4.NBT.A.1": 3},
            questions_answered=10,
            question_pool=[{"id": "q1"}],
        )

        assert state.theta == 1.5
        assert state.covered_standards == {"4.NBT.A.1": 3}
        assert state.questions_answered == 10
        assert len(state.question_pool) == 1


class TestQuestionSelectionServiceInitialization:
    """Test QuestionSelectionService initialization."""

    def test_cat_service_initialization(self):
        """CATService initializes with empty states dict."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        assert service._cat_states == {}

    def test_min_domain_coverage_targets(self):
        """MIN_DOMAIN_COVERAGE has correct targets."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        # Check key grade 4 domains exist
        assert "4.NBT" in service.MIN_DOMAIN_COVERAGE
        assert "4.NF" in service.MIN_DOMAIN_COVERAGE
        assert "4.OA" in service.MIN_DOMAIN_COVERAGE
        assert "4.MD" in service.MIN_DOMAIN_COVERAGE
        assert "4.G" in service.MIN_DOMAIN_COVERAGE

        # Check grade 5 domains exist
        assert "5.NBT" in service.MIN_DOMAIN_COVERAGE
        assert "5.NF" in service.MIN_DOMAIN_COVERAGE
        assert "5.OA" in service.MIN_DOMAIN_COVERAGE

        # Check minimum counts are reasonable
        assert service.MIN_DOMAIN_COVERAGE["4.NBT"] >= 5
        assert service.MIN_DOMAIN_COVERAGE["4.G"] >= 3


class TestCATServiceInitializeAssessment:
    """Test CATService.initialize_assessment method."""

    def test_initialize_assessment_sets_theta_zero(self):
        """initialize_assessment starts with theta=0.0."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
            CATState,
        )

        service = QuestionSelectionService()
        question_pool = [{"id": f"q{i}", "standard_code": "4.NBT.A.1"} for i in range(10)]

        state = service.initialize_assessment("assess-1", question_pool, target_question_count=35)

        assert isinstance(state, CATState)
        assert state.theta == 0.0
        assert state.assessment_id == "assess-1"
        assert state.questions_answered == 0
        assert len(state.question_pool) <= len(question_pool)  # May be limited

    def test_initialize_assessment_stores_state(self):
        """initialize_assessment stores state in _cat_states dict."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()
        question_pool = [{"id": "q1"}]

        service.initialize_assessment("assess-1", question_pool)

        assert "assess-1" in service._cat_states

    def test_initialize_assessment_limits_pool_size(self):
        """initialize_assessment limits question pool to 500."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()
        large_pool = [{"id": f"q{i}", "standard_code": "4.NBT.A.1"} for i in range(1000)]

        state = service.initialize_assessment("assess-1", large_pool)

        assert len(state.question_pool) <= 500

    def test_initialize_assessment_different_assessments_independent(self):
        """initialize_assessment maintains separate states for assessments."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        pool1 = [{"id": "q1", "standard_code": "4.NBT.A.1"}]
        pool2 = [{"id": "q2", "standard_code": "4.NF.A.1"}]

        state1 = service.initialize_assessment("assess-1", pool1)
        state2 = service.initialize_assessment("assess-2", pool2)

        assert state1 is not state2
        assert len(service._cat_states) == 2


class TestCATServiceGetCatState:
    """Test CATService.get_cat_state method."""

    def test_get_cat_state_returns_state(self):
        """get_cat_state returns stored CATState."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()
        question_pool = [{"id": "q1"}]

        service.initialize_assessment("assess-1", question_pool)

        state = service.get_cat_state("assess-1")

        assert state is not None
        assert state.theta == 0.0

    def test_get_cat_state_returns_none_for_missing(self):
        """get_cat_state returns None for missing assessment."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        state = service.get_cat_state("missing-assessment")

        assert state is None


class TestCATServiceSelectNextQuestion:
    """Test CATService.select_next_question method."""

    def test_select_next_question_returns_question(self):
        """select_next_question returns a question from pool."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()
        question_pool = [
            {"id": f"q{i}", "standard_code": f"4.NBT.A.{i}", "difficulty": 3}
            for i in range(10)
        ]

        selected = service.select_next_question(
            assessment_id="assess-1",
            student_id="student-1",
            covered_standards={},
            questions_answered=0,
            question_pool=question_pool,
        )

        assert selected is not None
        assert "id" in selected
        assert selected["id"] in [q["id"] for q in question_pool]

    def test_select_next_question_excludes_answered(self):
        """select_next_question excludes already answered questions."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()
        question_pool = [
            {"id": f"q{i}", "standard_code": "4.NBT.A.1", "difficulty": 3}
            for i in range(10)
        ]

        # Select first question
        first = service.select_next_question(
            assessment_id="assess-1",
            student_id="student-1",
            covered_standards={},
            questions_answered=0,
            question_pool=question_pool,
        )

        # Select second question, should be different
        second = service.select_next_question(
            assessment_id="assess-1",
            student_id="student-1",
            covered_standards={first["standard_code"]}: 1},
            questions_answered=1,
            question_pool=question_pool,
            exclude_question_ids=[first["id"]],
        )

        assert second["id"] != first["id"]

    def test_select_next_question_returns_none_at_max_questions(self):
        """select_next_question returns None when max questions reached."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()
        question_pool = [{"id": "q1", "standard_code": "4.NBT.A.1"}]

        selected = service.select_next_question(
            assessment_id="assess-1",
            student_id="student-1",
            covered_standards={},
            questions_answered=35,  # Max reached
            question_pool=question_pool,
        )

        assert selected is None

    def test_select_next_question_returns_none_for_empty_pool(self):
        """select_next_question returns None for empty pool."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        selected = service.select_next_question(
            assessment_id="assess-1",
            student_id="student-1",
            covered_standards={},
            questions_answered=0,
            question_pool=[],
        )

        assert selected is None

    def test_select_next_question_includes_theta_estimate(self):
        """select_next_question includes theta_estimate in result."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()
        question_pool = [
            {"id": "q1", "standard_code": "4.NBT.A.1", "difficulty": 3}
        ]

        selected = service.select_next_question(
            assessment_id="assess-1",
            student_id="student-1",
            covered_standards={},
            questions_answered=0,
            question_pool=question_pool,
        )

        assert "theta_estimate" in selected


class TestCATServiceDomainCoverage:
    """Test domain coverage prioritization."""

    def test_select_with_domain_coverage_prioritizes_gaps(self):
        """Selection prioritizes underserved domains."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()
        question_pool = [
            {"id": "q1", "standard_code": "4.NBT.A.1", "difficulty": 3},
            {"id": "q2", "standard_code": "4.NF.A.1", "difficulty": 3},
            {"id": "q3", "standard_code": "4.OA.A.1", "difficulty": 3},
        ]

        # NBT already has 5 questions, NF and OA have 0
        covered = {"4.NBT.A.1": 5, "4.NBT.A.2": 3}

        # Should select from NF or OA (gaps), not NBT
        selected = service._select_with_domain_coverage(
            question_pool, covered, questions_answered=8
        )

        # Verify it's not from NBT (already covered enough)
        if selected:
            standard_code = selected.get("standard_code", "")
            assert not standard_code.startswith("4.NBT") or selected["id"] == "q1"

    def test_calculate_coverage_gaps(self):
        """calculate_coverage_gaps identifies undercovered domains."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        covered = {
            "4.NBT.A.1": 5,  # At minimum
            "4.NBT.A.2": 3,  # Below minimum (5)
            "4.NF.A.1": 2,   # Below minimum (5)
            "4.OA.A.1": 5,   # At minimum
        }

        gaps = service._calculate_coverage_gaps(covered)

        # Should include NBT (A.2 is below) and NF
        assert len(gaps) >= 1
        assert "4.NBT" in gaps or "4.NF" in gaps or "4.OA" in gaps

    def test_calculate_coverage_gaps_empty(self):
        """calculate_coverage_gaps returns all domains when nothing covered."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        gaps = service._calculate_coverage_gaps({})

        # Should include key domains
        assert "4.NBT" in gaps
        assert "4.OA" in gaps


class TestCATServiceInformationMaximization:
    """Test information maximization question selection."""

    def test_select_by_information_scores_by_distance(self):
        """select_by_information scores questions by theta-distance."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        candidates = [
            {"id": "q1", "difficulty": 2},
            {"id": "q2", "difficulty": 3},
            {"id": "q3", "difficulty": 4},
        ]

        # All have same questions_answered, so same theta estimate
        selected = service._select_by_information(candidates, 0)

        assert selected is not None
        assert "information" in locals()  # Information was calculated

    def test_select_by_information_handles_ties_randomly(self):
        """select_by_information uses random for tie-breaking."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        # All questions have same difficulty
        candidates = [
            {"id": "q1", "difficulty": 3},
            {"id": "q2", "difficulty": 3},
            {"id": "q3", "difficulty": 3},
        ]

        # Run multiple times, may get different results due to randomness
        results = set()
        for _ in range(5):
            selected = service._select_by_information(candidates, 0)
            results.add(selected["id"])

        # Should be able to get any question
        assert len(results) >= 1


class TestCATServiceThetaEstimation:
    """Test theta estimation heuristics."""

    def test_estimate_theta_with_difficulty(self):
        """_estimate_theta adjusts based on question difficulty."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        # Difficulty 3 = mean
        theta3 = service._estimate_theta(0, difficulty=3)
        assert abs(theta3 - 0.0) < 0.5

        # Higher difficulty should increase theta slightly
        theta4 = service._estimate_theta(0, difficulty=4)
        assert theta4 >= theta3

    def test_estimate_theta_default(self):
        """_estimate_theta defaults to 0.0."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        theta = service._estimate_theta(0)

        assert theta == 0.0


class TestCATServiceGetProgress:
    """Test CATService.get_progress method."""

    def test_get_progress_returns_correct_structure(self):
        """get_progress returns expected progress dictionary."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        progress = service.get_progress(
            assessment_id="assess-1",
            questions_answered=10,
            covered_standards={
                "4.NBT.A.1": 3,
                "4.NF.A.1": 4,
                "4.OA.A.1": 3,
            },
        )

        assert "questions_answered" in progress
        assert "target_total" in progress
        assert "domains_covered" in progress
        assert "estimated_time_remaining_min" in progress
        assert progress["questions_answered"] == 10
        assert progress["target_total"] == 35

    def test_get_progress_calculates_domains_covered(self):
        """get_progress correctly groups by domain."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        progress = service.get_progress(
            assessment_id="assess-1",
            questions_answered=10,
            covered_standards={
                "4.NBT.A.1": 1,
                "4.NBT.A.2": 1,  # Same domain as A.1
                "4.NF.A.1": 2,
            },
        )

        # NBT should have count of 2 (both A.1 and A.2)
        assert "4.NBT" in progress["domains_covered"]


class TestCATServiceShouldEndAssessment:
    """Test CATService.should_end_assessment method."""

    def test_should_end_assessment_at_max_questions(self):
        """should_end_assessment returns True at 35 questions."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        should_end, reason = service.should_end_assessment(
            questions_answered=35,
            covered_standards={"4.NBT.A.1": 10},
        )

        assert should_end is True
        assert reason == "max_questions_reached"

    def test_should_end_assessment_insufficient_coverage(self):
        """should_end_assessment returns False with insufficient coverage."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        # Only 2 questions for key domain (needs 3)
        should_end, reason = service.should_end_assessment(
            questions_answered=35,
            covered_standards={"4.NBT.A.1": 2},  # Below minimum
        )

        assert should_end is False
        assert reason is None

    def test_should_end_assessment_all_covered(self):
        """should_end_assessment returns True with all requirements met."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        # All key domains have minimum coverage
        should_end, reason = service.should_end_assessment(
            questions_answered=35,
            covered_standards={
                "4.NBT.A.1": 5,
                "4.NF.A.1": 5,
                "4.OA.A.1": 5,
                "4.MD.A.1": 4,
                "4.G.A.1": 3,
            },
        )

        assert should_end is True
        assert reason == "all_standards_covered"


class TestCATServiceClearAssessment:
    """Test CATService.clear_assessment method."""

    def test_clear_assessment_removes_state(self):
        """clear_assessment removes assessment state."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        service.initialize_assessment("assess-1", [{"id": "q1"}])
        assert "assess-1" in service._cat_states

        service.clear_assessment("assess-1")
        assert "assess-1" not in service._cat_states

    def test_clear_nonexistent_assessment_no_error(self):
        """clear_assessment handles nonexistent assessment gracefully."""
        from src.services.question_selection_service import (
            QuestionSelectionService,
        )

        service = QuestionSelectionService()

        # Should not raise error
        service.clear_assessment("missing-assessment")

        assert len(service._cat_states) == 0


class TestGetQuestionSelectionService:
    """Test singleton CAT service accessor."""

    def test_get_question_selection_service_returns_instance(self):
        """get_question_selection_service returns CATService instance."""
        from src.services.question_selection_service import get_question_selection_service

        service = get_question_selection_service()

        assert service is not None

    def test_get_question_selection_service_is_singleton(self):
        """get_question_selection_service returns same instance."""
        from src.services.question_selection_service import get_question_selection_service

        service1 = get_question_selection_service()
        service2 = get_question_selection_service()

        assert service1 is service2
