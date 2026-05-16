"""
Computerized Adaptive Testing (CAT) question selection service.
Uses item response theory principles to select optimal questions.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import random

logger = logging.getLogger(__name__)


@dataclass
class CATState:
    """State for Computerized Adaptive Testing."""

    theta: float = 0.0  # Ability estimate
    covered_standards: Dict[str, int] = None  # standard_code -> count
    questions_answered: int = 0
    question_pool: List[Dict[str, Any]] = None


class QuestionSelectionService:
    """Service for CAT question selection."""

    # Target information: questions with difficulty closest to theta are most informative
    # Optimal when |theta - difficulty| is minimal

    # Domain coverage targets (minimum questions per domain)
    MIN_DOMAIN_COVERAGE = {
        "4.NBT": 5,  # Number & Operations in Base Ten
        "4.NF": 5,   # Number & Operations - Fractions
        "4.OA": 5,   # Operations & Algebraic Thinking
        "4.MD": 4,   # Measurement & Data
        "4.G": 3,    # Geometry
        "5.NBT": 5,  # Grade 5 Number & Operations
        "5.NF": 5,   # Grade 5 Fractions
        "5.OA": 5,   # Grade 5 Operations & Algebra
        "5.MD": 4,   # Grade 5 Measurement & Data
        "5.G": 3,    # Grade 5 Geometry
    }

    def __init__(self):
        """Initialize CAT service."""
        self._cat_states: Dict[str, CATState] = {}

    def initialize_assessment(
        self,
        assessment_id: str,
        question_pool: List[Dict[str, Any]],
        target_question_count: int = 35,
    ) -> CATState:
        """
        Initialize CAT state for an assessment.

        Args:
            assessment_id: Unique assessment identifier
            question_pool: List of available questions
            target_question_count: Target total questions

        Returns:
            Initialized CAT state
        """
        # Shuffle pool for initial randomization
        shuffled_pool = question_pool.copy()
        random.shuffle(shuffled_pool)

        state = CATState(
            theta=0.0,  # Start at mean ability
            covered_standards={},
            questions_answered=0,
            question_pool=shuffled_pool[:500],  # Limit pool size
        )

        self._cat_states[assessment_id] = state
        return state

    def get_cat_state(self, assessment_id: str) -> Optional[CATState]:
        """Get CAT state for an assessment."""
        return self._cat_states.get(assessment_id)

    def select_next_question(
        self,
        assessment_id: str,
        student_id: str,
        covered_standards: Dict[str, int],
        questions_answered: int,
        question_pool: List[Dict[str, Any]],
        exclude_question_ids: List[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Select the next question using CAT algorithm.

        Algorithm:
        1. Filter out already-answered questions
        2. Calculate domain coverage needs
        3. Select question that:
           - Maximizes information at current theta
           - Balances domain coverage
           - Matches estimated difficulty to student ability

        Args:
            assessment_id: Unique assessment identifier
            student_id: Student identifier
            covered_standards: Dict of standard_code -> count covered
            questions_answered: Total questions answered so far
            question_pool: Available questions
            exclude_question_ids: Questions already answered

        Returns:
            Selected question or None if should end assessment
        """
        exclude_ids = exclude_question_ids or []

        # Filter available questions
        available = [
            q for q in question_pool
            if q.get("id") not in exclude_ids and q.get("is_active", True)
        ]

        if not available:
            return None

        # Check if we should end assessment
        if questions_answered >= 35:  # Target question count
            return None

        # Ensure domain coverage
        selected = self._select_with_domain_coverage(
            available, covered_standards, questions_answered
        )

        if selected:
            # Update theta based on difficulty (simplified)
            # In production, use full IRT calibration
            difficulty = selected.get("difficulty", 3)
            # Adjust theta: correct -> increase, incorrect -> decrease
            # For selection phase, we use a heuristic
            selected["theta_estimate"] = self._estimate_theta(
                questions_answered, difficulty
            )

        return selected

    def _select_with_domain_coverage(
        self,
        available: List[Dict[str, Any]],
        covered_standards: Dict[str, int],
        questions_answered: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Select question with domain coverage priority.

        Priority:
        1. Underserved domains (below minimum threshold)
        2. Questions near current ability estimate
        """
        # Calculate coverage gaps
        gaps = self._calculate_coverage_gaps(covered_standards)

        if gaps:
            # Prioritize underserved domains
            candidates = [
                q for q in available
                if q.get("standard_code", "").split(".")[0] in gaps
            ]

            if candidates:
                # Among gap candidates, select by information maximization
                return self._select_by_information(candidates, questions_answered)

        # No gaps, select by information maximization
        return self._select_by_information(available, questions_answered)

    def _calculate_coverage_gaps(
        self, covered_standards: Dict[str, int]
    ) -> List[str]:
        """Calculate which domains need more questions."""
        gaps = []
        for standard_code, count in covered_standards.items():
            # Extract grade+domain prefix (e.g., "4.OA" from "4.OA.A.1")
            parts = standard_code.split(".")
            if len(parts) >= 2:
                domain_key = f"{parts[0]}.{parts[1]}"
                min_count = self.MIN_DOMAIN_COVERAGE.get(domain_key, 3)
                if count < min_count:
                    if domain_key not in gaps:
                        gaps.append(domain_key)
        return gaps

    def _select_by_information(
        self,
        candidates: List[Dict[str, Any]],
        questions_answered: int,
    ) -> Optional[Dict[str, Any]]:
        """Select the question with the highest 2PL Fisher information at θ.

        Uses `src.services.irt_service` (P3-T03). Each candidate is expected
        to carry a `difficulty_b` (logit-scale) and an optional
        `discrimination_a`. Falls back to mapping the legacy integer
        `difficulty` (1..5) to a b-parameter when explicit IRT params are
        absent.
        """
        from src.services.irt_service import (
            IRTItem,
            difficulty_integer_to_b,
            select_max_information,
        )

        estimated_theta = self._estimate_theta(questions_answered)
        if not candidates:
            return None

        irt_items = []
        by_id: dict[str, Dict[str, Any]] = {}
        for q in candidates:
            qid = str(q.get("id"))
            b = q.get("difficulty_b")
            if b is None:
                b = difficulty_integer_to_b(int(q.get("difficulty", 3)))
            a = float(q.get("discrimination_a", 1.0))
            irt_items.append(IRTItem(id=qid, b=float(b), a=a))
            by_id[qid] = q

        pick = select_max_information(estimated_theta, irt_items)
        if pick is None:
            return None
        # Light randomization between the top few (avoid deterministic loops).
        # Pick from items within 5% of best information.
        from src.services.irt_service import information

        top_score = information(estimated_theta, pick)
        near_top = [it for it in irt_items if information(estimated_theta, it) >= 0.95 * top_score]
        chosen = random.choice(near_top)
        return by_id[chosen.id]

    def _estimate_theta(
        self,
        questions_answered: int,
        difficulty: Optional[int] = None,
    ) -> float:
        """
        Estimate student ability (theta) using heuristic.

        Simplified IRT-based estimate:
        - Start at theta = 0 (mean)
        - Increase with correct answers on difficult questions
        - Decrease with incorrect answers on easy questions

        Note: This is a heuristic. Production should use full IRT calibration.
        """
        # Heuristic: theta based on average difficulty of answered questions
        # In production, this would use MLE from IRT model
        if difficulty:
            # Adjust based on this question's difficulty
            return 0.0 + (difficulty - 3) * 0.1  # Small adjustment

        # Default estimate
        return 0.0

    def get_progress(
        self,
        assessment_id: str,
        questions_answered: int,
        covered_standards: Dict[str, int],
    ) -> Dict[str, Any]:
        """
        Get assessment progress information.

        Args:
            assessment_id: Unique assessment identifier
            questions_answered: Total questions answered
            covered_standards: Standard coverage counts

        Returns:
            Progress dictionary
        """
        # Count questions per domain
        domains_covered = {}
        for standard_code in covered_standards.keys():
            parts = standard_code.split(".")
            if len(parts) >= 2:
                domain = f"{parts[0]}.{parts[1]}"
                domains_covered[domain] = domains_covered.get(domain, 0) + 1

        # Estimate time remaining (avg 90 seconds per question)
        remaining = max(0, 35 - questions_answered)
        estimated_time_remaining = remaining * 90  # seconds

        return {
            "questions_answered": questions_answered,
            "target_total": 35,
            "domains_covered": domains_covered,
            "estimated_time_remaining_min": max(1, estimated_time_remaining // 60),
        }

    def should_end_assessment(
        self,
        questions_answered: int,
        covered_standards: Dict[str, int],
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if assessment should end.

        Returns:
            Tuple of (should_end, end_reason)
        """
        if questions_answered >= 35:
            return True, "max_questions_reached"

        # Check domain coverage
        domain_counts = {}
        for standard_code in covered_standards.keys():
            parts = standard_code.split(".")
            if len(parts) >= 2:
                domain = f"{parts[0]}.{parts[1]}"
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

        # Ensure minimum coverage for key domains
        min_domains = ["4.NBT", "4.NF", "4.OA", "4.MD", "4.G"]
        for domain in min_domains:
            if domain_counts.get(domain, 0) < 3:
                return False, None

        # All requirements met
        return True, "all_standards_covered"

    def clear_assessment(self, assessment_id: str) -> None:
        """Clear CAT state for an assessment."""
        if assessment_id in self._cat_states:
            del self._cat_states[assessment_id]


# Singleton instance
_cat_service: Optional[QuestionSelectionService] = None


def get_question_selection_service() -> QuestionSelectionService:
    """Get singleton CAT service instance."""
    global _cat_service
    if _cat_service is None:
        _cat_service = QuestionSelectionService()
    return _cat_service
