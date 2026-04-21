"""
Tests for SkillGraphService.
"""
import pytest
import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.skill_graph_service import (
    SkillGraphService,
    get_topological_sequence,
    compute_priority_score,
    rank_skills_by_priority,
)


class TestSkillGraphService:
    """Tests for SkillGraphService."""

    @pytest.mark.asyncio
    async def test_get_graph_success(
        self,
        db_session: AsyncSession,
        standards_repo,
    ):
        """Test successful graph loading."""
        service = SkillGraphService(db_session)
        graph = await service.get_graph()

        assert isinstance(graph, nx.DiGraph)
        assert len(graph.nodes()) > 0

    @pytest.mark.asyncio
    async def test_graph_is_dag(
        self,
        db_session: AsyncSession,
    ):
        """Test that the graph is a DAG (no cycles)."""
        service = SkillGraphService(db_session)
        graph = await service.get_graph()

        assert nx.is_directed_acyclic_graph(graph)

    @pytest.mark.asyncio
    async def test_get_topological_sequence(
        self,
        db_session: AsyncSession,
        standards_repo,
    ):
        """Test topological sort produces valid ordering."""
        service = SkillGraphService(db_session)
        graph = await service.get_graph()

        # Get a subset of codes
        codes = ["3.OA.C.7", "4.OA.A.1", "4.NBT.B.5"]
        sequence = service.get_topological_sequence(codes, graph)

        # Check all codes are in sequence
        assert set(sequence) >= set(codes)

        # Check prerequisite order (3.OA.C.7 should come before 4.OA.A.1)
        if "3.OA.C.7" in sequence and "4.OA.A.1" in sequence:
            assert sequence.index("3.OA.C.7") < sequence.index("4.OA.A.1")

    def test_compute_priority_score_high_centrality(self):
        """Test priority scoring for high centrality skills."""
        G = nx.DiGraph()
        G.add_node("3.OA.C.7", grade=3)

        # Add edges from this node to simulate high centrality
        for i in range(5):
            G.add_edge("3.OA.C.7", f"4.standard.{i}")

        score = compute_priority_score("3.OA.C.7", 0.3, G)

        # Should have centrality bonus (5 * 10 = 50) + deficiency (0.7 * 20 = 14) + grade bonus (5)
        assert score == 69.0

    def test_compute_priority_score_low_centrality(self):
        """Test priority scoring for low centrality skills."""
        G = nx.DiGraph()
        G.add_node("4.DR.C.3", grade=4)

        score = compute_priority_score("4.DR.C.3", 0.5, G)

        # Centrality = 0, deficiency = 10, grade bonus = 0
        assert score == 10.0

    def test_rank_skills_by_priority(self):
        """Test skill ranking by priority."""
        G = nx.DiGraph()

        # Add nodes with different centralities
        G.add_node("3.OA.C.7", grade=3)
        G.add_node("4.DR.C.3", grade=4)

        # 3.OA.C.7 has high centrality
        for i in range(5):
            G.add_edge("3.OA.C.7", f"4.s{i}")

        skill_states = {"3.OA.C.7": 0.3, "4.DR.C.3": 0.5}
        ranked = rank_skills_by_priority(skill_states, G)

        # 3.OA.C.7 should be first due to higher centrality
        assert ranked[0][0] == "3.OA.C.7"


class TestPrerequisiteChain:
    """Tests for prerequisite chain detection."""

    @pytest.mark.asyncio
    async def test_get_prerequisite_chain(
        self,
        db_session: AsyncSession,
    ):
        """Test prerequisite chain retrieval."""
        service = SkillGraphService(db_session)
        graph = await service.get_graph()

        # Get prerequisites for a Grade 4 standard
        chain = service.get_prerequisite_chain("4.NBT.B.5", {"4.NBT.B.5": 0.3}, graph)

        assert len(chain) > 0
        assert "4.NBT.B.5" in chain

        # All items should be prerequisites
        for prereq in chain[:-1]:  # Exclude the final item
            assert prereq in graph.predecessors("4.NBT.B.5") or prereq in graph.predecessors(prereq)


class TestModuleNames:
    """Tests for module name mappings."""

    @pytest.mark.asyncio
    async def test_get_module_name(self, db_session: AsyncSession):
        """Test module name retrieval."""
        service = SkillGraphService(db_session)

        assert service.get_module_name("3.OA.C.7") == "Multiplication & Division Facts"
        assert service.get_module_name("4.NBT.B.5") == "Multi-Digit Multiplication"
        assert service.get_module_name("4.OA.A.1") == "Multiplicative Comparisons"

        # Unknown code returns default
        assert "Unknown" in service.get_module_name("UNKNOWN.CODE")


class TestEstimateSessions:
    """Tests for session estimation."""

    @pytest.mark.asyncio
    async def test_estimate_sessions_to_mastery(
        self,
        db_session: AsyncSession,
    ):
        """Test session estimation for various P(mastered) values."""
        service = SkillGraphService(db_session)

        assert service.estimate_sessions_to_mastery(0.90) == 0
        assert service.estimate_sessions_to_mastery(0.75) == 2
        assert service.estimate_sessions_to_mastery(0.60) == 4
        assert service.estimate_sessions_to_mastery(0.40) == 6
        assert service.estimate_sessions_to_mastery(0.20) == 8
