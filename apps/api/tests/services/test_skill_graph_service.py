"""
Tests for SkillGraphService.
"""
import pytest
import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.skill_graph_service import SkillGraphService


class TestSkillGraphBasics:
    """Tests for basic skill graph operations."""

    @pytest.mark.asyncio
    async def test_get_graph(self, db_session: AsyncSession):
        """Verify graph can be loaded from DB."""
        service = SkillGraphService(db_session)
        G = await service.get_graph()
        assert isinstance(G, nx.DiGraph)

    def test_topological_sequence(self, db_session: AsyncSession):
        """Verify topological sequence generation."""
        service = SkillGraphService(db_session)
        G = nx.DiGraph()
        G.add_edge("4.NBT.A.1", "4.NBT.A.2")
        
        sequence = service.get_topological_sequence(["4.NBT.A.2"], G)
        assert "4.NBT.A.1" in sequence
        assert sequence.index("4.NBT.A.1") < sequence.index("4.NBT.A.2")

    def test_priority_scoring(self, db_session: AsyncSession):
        """Verify priority scoring logic."""
        service = SkillGraphService(db_session)
        G = nx.DiGraph()
        G.add_node("4.NBT.A.1", grade=4)
        
        score = service.compute_priority_score("4.NBT.A.1", G, 0.5)
        assert score > 0

    def test_rank_skills(self, db_session: AsyncSession):
        """Verify skill ranking."""
        service = SkillGraphService(db_session)
        G = nx.DiGraph()
        G.add_node("4.NBT.A.1", grade=4)
        G.add_node("4.OA.A.1", grade=4)
        
        mastery_map = {"4.NBT.A.1": 0.3, "4.OA.A.1": 0.6}
        ranked = service.rank_skills_by_priority(mastery_map, G)
        
        assert len(ranked) == 2
        # Lower mastery usually means higher priority
        assert ranked[0][0] == "4.NBT.A.1"
