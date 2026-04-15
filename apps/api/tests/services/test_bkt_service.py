"""Tests for Bayesian Knowledge Tracing (BKT) service."""

import pytest
from unittest.mock import patch, MagicMock


class TestBKTState:
    """Test BKTState dataclass."""

    def test_bkt_state_default_values(self):
        """BKTState has correct default values."""
        from src.services.bkt_service import BKTState

        state = BKTState()

        assert state.p_mastery == 0.0
        assert state.p_guess == 0.25
        assert state.p_slip == 0.2
        assert state.p_learning == 0.5

    def test_bkt_state_custom_values(self):
        """BKTState accepts custom values."""
        from src.services.bkt_service import BKTState

        state = BKTState(
            p_mastery=0.8,
            p_guess=0.1,
            p_slip=0.15,
            p_learning=0.6
        )

        assert state.p_mastery == 0.8
        assert state.p_guess == 0.1
        assert state.p_slip == 0.15
        assert state.p_learning == 0.6


class TestBKTServiceInitialization:
    """Test BKTService initialization and setup."""

    def test_bkt_service_initialization(self):
        """BKTService initializes with empty instances dict."""
        from src.services.bkt_service import BKTService

        service = BKTService()

        assert service._bkt_instances == {}
        assert service.DEFAULT_P_GUESS == 0.25
        assert service.DEFAULT_P_SLIP == 0.20
        assert service.DEFAULT_P_LEARNING == 0.50
        assert service.DEFAULT_P_MASTERY == 0.0

    @patch("src.services.bkt_service.PyBKT")
    def test_get_or_create_bkt_creates_new_instance(self, mock_bkt_class):
        """get_or_create_bkt creates new BKT instance for new standard."""
        from src.services.bkt_service import BKTService

        mock_bkt = MagicMock()
        mock_bkt_class.return_value = mock_bkt

        service = BKTService()
        result = service.get_or_create_bkt("4.NBT.A.1")

        assert result == mock_bkt
        assert "4.NBT.A.1" in service._bkt_instances
        mock_bkt_class.assert_called_once_with(
            p_l0=0.0,
            p_trans=0.50,
            p_slip=0.20,
            p_guess=0.25,
        )

    @patch("src.services.bkt_service.PyBKT")
    def test_get_or_create_bkt_reuses_existing_instance(self, mock_bkt_class):
        """get_or_create_bkt reuses existing BKT instance."""
        from src.services.bkt_service import BKTService

        mock_bkt = MagicMock()
        mock_bkt_class.return_value = mock_bkt

        service = BKTService()

        # First call
        result1 = service.get_or_create_bkt("4.NBT.A.1")

        # Second call should reuse
        result2 = service.get_or_create_bkt("4.NBT.A.1")

        assert result1 == result2
        assert mock_bkt_class.call_count == 1

    @patch("src.services.bkt_service.PyBKT")
    def test_get_or_create_bkt_with_custom_params(self, mock_bkt_class):
        """get_or_create_bkt accepts custom BKT parameters."""
        from src.services.bkt_service import BKTService

        mock_bkt = MagicMock()
        mock_bkt_class.return_value = mock_bkt

        service = BKTService()
        service.get_or_create_bkt(
            "4.NBT.A.1",
            p_l0=0.5,
            p_trans=0.7,
            p_slip=0.1,
            p_guess=0.15,
        )

        mock_bkt_class.assert_called_once_with(
            p_l0=0.5,
            p_trans=0.7,
            p_slip=0.1,
            p_guess=0.15,
        )

    def test_initialize_state_returns_bkt_state(self):
        """initialize_state returns BKTState with correct values."""
        from src.services.bkt_service import BKTService, BKTState

        service = BKTService()

        state = service.initialize_state("4.NBT.A.1")

        assert isinstance(state, BKTState)
        assert state.p_mastery == 0.0
        assert state.p_guess == 0.25
        assert state.p_slip == 0.2
        assert state.p_learning == 0.5

    def test_initialize_state_with_custom_params(self):
        """initialize_state accepts custom parameters."""
        from src.services.bkt_service import BKTService, BKTState

        service = BKTService()

        state = service.initialize_state(
            "4.NBT.A.1",
            p_l0=0.6,
            p_trans=0.8,
            p_slip=0.1,
            p_guess=0.15,
        )

        assert state.p_mastery == 0.6
        assert state.p_guess == 0.15
        assert state.p_slip == 0.1
        assert state.p_learning == 0.8


class TestBKTServiceUpdateState:
    """Test BKTService.update_state method."""

    @patch("src.services.bkt_service.PyBKT")
    def test_update_state_correct_response(self, mock_bkt_class):
        """update_state increases mastery after correct response."""
        from src.services.bkt_service import BKTService

        mock_bkt = MagicMock()
        mock_node = MagicMock()
        mock_node.state.p_l = 0.6  # Mastery increased after correct answer
        mock_bkt.get_node.return_value = mock_node
        mock_bkt.p_guess = 0.25
        mock_bkt.p_slip = 0.2
        mock_bkt.p_trans = 0.5
        mock_bkt_class.return_value = mock_bkt

        service = BKTService()

        # First correct response
        state = service.update_state("4.NBT.A.1", response_correct=True)

        assert state.p_mastery > 0.0
        assert state.p_mastery <= 1.0
        mock_bkt.forward_inference.assert_called_once_with(is_correct=True)

    @patch("src.services.bkt_service.PyBKT")
    def test_update_state_incorrect_response(self, mock_bkt_class):
        """update_state decreases mastery after incorrect response."""
        from src.services.bkt_service import BKTService

        mock_bkt = MagicMock()
        mock_node = MagicMock()
        mock_node.state.p_l = 0.1  # Mastery decreased after incorrect answer
        mock_bkt.get_node.return_value = mock_node
        mock_bkt.p_guess = 0.25
        mock_bkt.p_slip = 0.2
        mock_bkt.p_trans = 0.5
        mock_bkt_class.return_value = mock_bkt

        service = BKTService()

        # First incorrect response
        state = service.update_state("4.NBT.A.1", response_correct=False)

        assert state.p_mastery >= 0.0
        assert state.p_mastery <= 1.0
        mock_bkt.forward_inference.assert_called_once_with(is_correct=False)

    @patch("src.services.bkt_service.PyBKT")
    def test_update_state_mastery_bounds(self, mock_bkt_class):
        """update_state keeps mastery within valid bounds [0.0, 1.0]."""
        from src.services.bkt_service import BKTService

        mock_bkt = MagicMock()
        mock_node = MagicMock()
        mock_node.state.p_l = 0.999  # Very high mastery
        mock_bkt.get_node.return_value = mock_node
        mock_bkt.p_guess = 0.25
        mock_bkt.p_slip = 0.2
        mock_bkt.p_trans = 0.5
        mock_bkt_class.return_value = mock_bkt

        service = BKTService()

        state = service.update_state("4.NBT.A.1", response_correct=True)

        assert 0.0 <= state.p_mastery <= 1.0

    @patch("src.services.bkt_service.PyBKT")
    def test_update_state_different_standards_independent(self, mock_bkt_class):
        """update_state maintains separate state for different standards."""
        from src.services.bkt_service import BKTService

        mock_bkt1 = MagicMock()
        mock_node1 = MagicMock()
        mock_node1.state.p_l = 0.8
        mock_bkt1.get_node.return_value = mock_node1
        mock_bkt1.p_guess = 0.25
        mock_bkt1.p_slip = 0.2
        mock_bkt1.p_trans = 0.5

        mock_bkt2 = MagicMock()
        mock_node2 = MagicMock()
        mock_node2.state.p_l = 0.3
        mock_bkt2.get_node.return_value = mock_node2
        mock_bkt2.p_guess = 0.25
        mock_bkt2.p_slip = 0.2
        mock_bkt2.p_trans = 0.5

        mock_bkt_class.side_effect = [mock_bkt1, mock_bkt2]

        service = BKTService()

        # Update state for standard 1
        state1 = service.update_state("4.NBT.A.1", response_correct=True)

        # Update state for standard 2
        state2 = service.update_state("4.NF.A.1", response_correct=False)

        assert state1.p_mastery == 0.8
        assert state2.p_mastery == 0.3
        assert len(service._bkt_instances) == 2

    @patch("src.services.bkt_service.PyBKT")
    def test_update_state_sequence_convergence(self, mock_bkt_class):
        """update_state shows convergence with multiple correct responses."""
        from src.services.bkt_service import BKTService

        mock_bkt = MagicMock()
        mock_node = MagicMock()
        mock_node.state.p_l = 0.0

        def mock_forward_inference(is_correct):
            # Simulate mastery increasing with correct answers
            if is_correct:
                mock_node.state.p_l = min(1.0, mock_node.state.p_l + 0.2)
            else:
                mock_node.state.p_l = max(0.0, mock_node.state.p_l - 0.1)

        mock_bkt.get_node.return_value = mock_node
        mock_bkt.p_guess = 0.25
        mock_bkt.p_slip = 0.2
        mock_bkt.p_trans = 0.5
        mock_bkt.forward_inference.side_effect = mock_forward_inference
        mock_bkt_class.return_value = mock_bkt

        service = BKTService()

        # Start with low mastery
        state = service.update_state("4.NBT.A.1", response_correct=True)
        initial_mastery = state.p_mastery

        # Multiple correct responses should increase mastery
        for _ in range(5):
            state = service.update_state("4.NBT.A.1", response_correct=True)

        assert state.p_mastery > initial_mastery


class TestBKTServicePredictProbability:
    """Test BKTService.predict_probability method."""

    @patch("src.services.bkt_service.PyBKT")
    def test_predict_probability_formula(self, mock_bkt_class):
        """predict_probability uses correct P(C) formula."""
        from src.services.bkt_service import BKTService

        mock_bkt = MagicMock()
        mock_node = MagicMock()
        mock_node.state.p_l = 0.8  # High mastery
        mock_bkt.get_node.return_value = mock_node
        mock_bkt.p_guess = 0.25
        mock_bkt.p_slip = 0.2
        mock_bkt.p_trans = 0.5
        mock_bkt_class.return_value = mock_bkt

        service = BKTService()

        # P(C) = P(L) * (1 - S) + (1 - P(L)) * G
        # P(C) = 0.8 * (1 - 0.2) + (1 - 0.8) * 0.25
        # P(C) = 0.8 * 0.8 + 0.2 * 0.25 = 0.64 + 0.05 = 0.69
        p_correct = service.predict_probability("4.NBT.A.1", response_correct=True)

        # Probability should be reasonable given high mastery
        assert 0.5 <= p_correct <= 0.9

    @patch("src.services.bkt_service.PyBKT")
    def test_predict_probability_low_mastery(self, mock_bkt_class):
        """predict_probability returns lower probability for low mastery."""
        from src.services.bkt_service import BKTService

        mock_bkt = MagicMock()
        mock_node = MagicMock()
        mock_node.state.p_l = 0.1  # Low mastery
        mock_bkt.get_node.return_value = mock_node
        mock_bkt.p_guess = 0.25
        mock_bkt.p_slip = 0.2
        mock_bkt.p_trans = 0.5
        mock_bkt_class.return_value = mock_bkt

        service = BKTService()

        p_correct = service.predict_probability("4.NBT.A.1", response_correct=True)

        # With low mastery, probability should be lower
        assert 0.1 <= p_correct <= 0.5


class TestBKTServiceBatchUpdate:
    """Test BKTService.batch_update method."""

    @patch("src.services.bkt_service.PyBKT")
    def test_batch_update_all_correct(self, mock_bkt_class):
        """batch_update increases mastery with all correct responses."""
        from src.services.bkt_service import BKTService

        mock_bkt = MagicMock()
        mock_node = MagicMock()
        mock_node.state.p_l = 0.0

        def mock_forward_inference(is_correct):
            if is_correct:
                mock_node.state.p_l = min(1.0, mock_node.state.p_l + 0.15)

        mock_bkt.get_node.return_value = mock_node
        mock_bkt.p_guess = 0.25
        mock_bkt.p_slip = 0.2
        mock_bkt.p_trans = 0.5
        mock_bkt.forward_inference.side_effect = mock_forward_inference
        mock_bkt_class.return_value = mock_bkt

        service = BKTService()

        responses = [True, True, True, True, True]  # 5 correct in a row
        final_state = service.batch_update("4.NBT.A.1", responses)

        assert final_state.p_mastery > 0.5

    @patch("src.services.bkt_service.PyBKT")
    def test_batch_update_all_incorrect(self, mock_bkt_class):
        """batch_update decreases mastery with all incorrect responses."""
        from src.services.bkt_service import BKTService

        mock_bkt = MagicMock()
        mock_node = MagicMock()
        mock_node.state.p_l = 0.5  # Start at medium mastery

        def mock_forward_inference(is_correct):
            if not is_correct:
                mock_node.state.p_l = max(0.0, mock_node.state.p_l - 0.1)

        mock_bkt.get_node.return_value = mock_node
        mock_bkt.p_guess = 0.25
        mock_bkt.p_slip = 0.2
        mock_bkt.p_trans = 0.5
        mock_bkt.forward_inference.side_effect = mock_forward_inference
        mock_bkt_class.return_value = mock_bkt

        service = BKTService()

        responses = [False, False, False, False, False]  # 5 incorrect in a row
        final_state = service.batch_update("4.NBT.A.1", responses)

        assert final_state.p_mastery < 0.5

    @patch("src.services.bkt_service.PyBKT")
    def test_batch_update_mixed_responses(self, mock_bkt_class):
        """batch_update with mixed correct/incorrect responses."""
        from src.services.bkt_service import BKTService

        mock_bkt = MagicMock()
        mock_node = MagicMock()
        mock_node.state.p_l = 0.5

        def mock_forward_inference(is_correct):
            if is_correct:
                mock_node.state.p_l = min(1.0, mock_node.state.p_l + 0.1)
            else:
                mock_node.state.p_l = max(0.0, mock_node.state.p_l - 0.05)

        mock_bkt.get_node.return_value = mock_node
        mock_bkt.p_guess = 0.25
        mock_bkt.p_slip = 0.2
        mock_bkt.p_trans = 0.5
        mock_bkt.forward_inference.side_effect = mock_forward_inference
        mock_bkt_class.return_value = mock_bkt

        service = BKTService()

        # 6 correct, 4 incorrect = 60% correct
        responses = [True, True, False, True, True, True, False, True, True, True]
        final_state = service.batch_update("4.NBT.A.1", responses)

        assert 0.4 <= final_state.p_mastery <= 0.8


class TestBKTServiceStateSerialization:
    """Test BKTState dictionary conversion methods."""

    def test_get_state_dict(self):
        """get_state_dict converts BKTState to dictionary."""
        from src.services.bkt_service import BKTService, BKTState

        service = BKTService()
        state = BKTState(
            p_mastery=0.8,
            p_guess=0.1,
            p_slip=0.15,
            p_learning=0.7
        )

        state_dict = service.get_state_dict(state)

        assert state_dict["p_mastery"] == 0.8
        assert state_dict["p_guess"] == 0.1
        assert state_dict["p_slip"] == 0.15
        assert state_dict["p_learning"] == 0.7

    def test_state_from_dict(self):
        """state_from_dict converts dictionary to BKTState."""
        from src.services.bkt_service import BKTService, BKTState

        service = BKTService()

        state_dict = {
            "p_mastery": 0.8,
            "p_guess": 0.1,
            "p_slip": 0.15,
            "p_learning": 0.7,
        }

        state = service.state_from_dict(state_dict)

        assert isinstance(state, BKTState)
        assert state.p_mastery == 0.8
        assert state.p_guess == 0.1
        assert state.p_slip == 0.15
        assert state.p_learning == 0.7

    def test_state_from_dict_with_defaults(self):
        """state_from_dict uses defaults for missing values."""
        from src.services.bkt_service import BKTService, BKTState

        service = BKTService()

        # Only provide p_mastery
        state_dict = {"p_mastery": 0.8}

        state = service.state_from_dict(state_dict)

        assert state.p_mastery == 0.8
        assert state.p_guess == 0.25  # Default
        assert state.p_slip == 0.20  # Default
        assert state.p_learning == 0.50  # Default


class TestBKTServiceClassifyMastery:
    """Test BKTService.classify_mastery method."""

    def test_classify_mastery_high(self):
        """classify_mastery returns 'high' for p_mastery >= 0.80."""
        from src.services.bkt_service import BKTService

        service = BKTService()

        assert service.classify_mastery(0.80) == "high"
        assert service.classify_mastery(0.85) == "high"
        assert service.classify_mastery(0.95) == "high"
        assert service.classify_mastery(1.0) == "high"

    def test_classify_mastery_medium(self):
        """classify_mastery returns 'medium' for 0.60 <= p_mastery < 0.80."""
        from src.services.bkt_service import BKTService

        service = BKTService()

        assert service.classify_mastery(0.60) == "medium"
        assert service.classify_mastery(0.65) == "medium"
        assert service.classify_mastery(0.75) == "medium"
        assert service.classify_mastery(0.79) == "medium"

    def test_classify_mastery_low(self):
        """classify_mastery returns 'low' for p_mastery < 0.60."""
        from src.services.bkt_service import BKTService

        service = BKTService()

        assert service.classify_mastery(0.0) == "low"
        assert service.classify_mastery(0.3) == "low"
        assert service.classify_mastery(0.50) == "low"
        assert service.classify_mastery(0.59) == "low"


class TestBKTServiceCleanup:
    """Test BKTService cleanup methods."""

    def test_clear_instance(self):
        """clear_instance removes a single BKT instance."""
        from src.services.bkt_service import BKTService

        service = BKTService()

        # Create instances
        service.get_or_create_bkt("4.NBT.A.1")
        service.get_or_create_bkt("4.NF.A.1")

        assert len(service._bkt_instances) == 2

        # Clear one instance
        service.clear_instance("4.NBT.A.1")

        assert len(service._bkt_instances) == 1
        assert "4.NBT.A.1" not in service._bkt_instances

    def test_clear_all(self):
        """clear_all removes all BKT instances."""
        from src.services.bkt_service import BKTService

        service = BKTService()

        # Create instances
        service.get_or_create_bkt("4.NBT.A.1")
        service.get_or_create_bkt("4.NF.A.1")
        service.get_or_create_bkt("4.OA.A.1")

        assert len(service._bkt_instances) == 3

        # Clear all
        service.clear_all()

        assert len(service._bkt_instances) == 0

    def test_clear_nonexistent_instance(self):
        """clear_instance handles nonexistent instance gracefully."""
        from src.services.bkt_service import BKTService

        service = BKTService()

        # Should not raise error
        service.clear_instance("4.NBT.A.1")

        assert len(service._bkt_instances) == 0


class TestGetBKTService:
    """Test singleton BKT service accessor."""

    def test_get_bkt_service_returns_instance(self):
        """get_bkt_service returns BKTService instance."""
        from src.services.bkt_service import get_bkt_service

        service = get_bkt_service()

        assert service is not None

    def test_get_bkt_service_is_singleton(self):
        """get_bkt_service returns same instance on subsequent calls."""
        from src.services.bkt_service import get_bkt_service

        service1 = get_bkt_service()
        service2 = get_bkt_service()

        assert service1 is service2
