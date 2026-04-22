"""
Skill Graph Service for managing the skill dependency graph.
Uses NetworkX to represent the prerequisite relationships as a DAG.
"""
from typing import Optional
from uuid import uuid4

import networkx as nx
from networkx import NetworkXError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import PrerequisiteRelationship, Standard


class SkillGraphService:
    """
    Service for managing the skill dependency graph.

    The graph is a Directed Acyclic Graph (DAG) where:
    - Nodes = standards (both Grade 3 prerequisites and Grade 4 standards)
    - Edges = prerequisite relationships
    - Edge direction: prerequisite_code -> dependent_code

    The graph is cached in memory and rebuilt on application restart
    or when prerequisite relationships are updated via admin.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._graph: Optional[nx.DiGraph] = None

    async def get_graph(self) -> nx.DiGraph:
        """
        Get the skill dependency graph, loading from DB if not cached.

        Returns a NetworkX DiGraph with:
        - Nodes: standard codes with attributes (grade, domain, etc.)
        - Edges: (prereq_code, dependent_code) with strength attribute
        """
        if self._graph is not None:
            return self._graph

        self._graph = nx.DiGraph()

        # Add all active standard nodes
        result = await self.session.execute(
            select(Standard).where(Standard.is_active == True)
        )
        standards = result.scalars().all()

        for std in standards:
            self._graph.add_node(
                std.standard_code,
                grade=std.grade_level,
                domain=std.domain,
                title=std.title,
                description=std.description,
                is_prerequisite=std.is_active,
                strand=std.domain,  # Map domain to strand
            )

        # Add all prerequisite relationship edges
        result = await self.session.execute(
            select(PrerequisiteRelationship)
        )
        relationships = result.scalars().all()

        for rel in relationships:
            # Fetch the actual Standard records to get their standard_code
            prereq_result = await self.session.execute(
                select(Standard).where(Standard.id == rel.prerequisite_id)
            )
            prerequisite = prereq_result.scalars().first()

            target_result = await self.session.execute(
                select(Standard).where(Standard.id == rel.standard_id)
            )
            target = target_result.scalars().first()

            if prerequisite and target:
                self._graph.add_edge(
                    prerequisite.standard_code,
                    target.standard_code,
                    strength=rel.strength or "required",
                )

        # Validate: graph must be a DAG (no cycles)
        if not nx.is_directed_acyclic_graph(self._graph):
            raise ValueError(
                "Skill dependency graph contains a cycle - check prerequisite_relationships data"
            )

        return self._graph

    async def clear_cache(self) -> None:
        """Clear the cached graph. Call when prerequisite relationships are updated."""
        self._graph = None

    def get_topological_sequence(
        self, relevant_codes: list[str], G: Optional[nx.DiGraph] = None
    ) -> list[str]:
        """
        Given a set of standard codes the student needs to work on,
        return them in topologically sorted order (prerequisites first).

        Uses Kahn's algorithm (BFS-based topological sort) for stable ordering.

        Args:
            relevant_codes: List of standard codes to include
            G: Optional pre-loaded graph (uses cached graph if None)

        Returns:
            Ordered list of standard codes
        """
        if G is None:
            raise ValueError("Graph must be loaded before calling get_topological_sequence")

        # Build subgraph containing only relevant nodes + their ancestors
        subgraph_nodes = set(relevant_codes)
        for code in relevant_codes:
            if code in G.nodes:
                ancestors = nx.ancestors(G, code)
                subgraph_nodes.update(ancestors)

        subgraph = G.subgraph(subgraph_nodes)

        # Kahn's algorithm
        in_degree = {node: subgraph.in_degree(node) for node in subgraph.nodes()}
        queue = sorted([node for node, deg in in_degree.items() if deg == 0])
        result = []

        while queue:
            node = queue.pop(0)
            if node in relevant_codes:
                result.append(node)
            for successor in subgraph.successors(node):
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    queue.append(successor)
                    queue.sort()

        return result

    def compute_priority_score(
        self,
        standard_code: str,
        p_mastered: float,
        G: nx.DiGraph,
    ) -> float:
        """
        Compute a priority score for a skill (higher = more urgent to address).

        Priority is based on:
        1. Out-degree centrality (number of skills that depend on this one)
        2. Deficiency severity (how far from mastery)
        3. Grade-level bonus (Grade 3 prerequisites get +5)

        Args:
            standard_code: Standard code to score
            p_mastered: Current P(mastered) probability
            G: Skill dependency graph

        Returns:
            Priority score (higher = more urgent)
        """
        # Out-degree centrality
        try:
            out_degree = G.out_degree[standard_code]
        except (KeyError, NetworkXError):
            out_degree = 0
            
        centrality_score = out_degree * 10

        # Deficiency severity
        deficiency_score = (1.0 - p_mastered) * 20

        # Grade-level bonus
        try:
            grade = G.nodes[standard_code].get('grade', 4)
        except KeyError:
            grade = 4
            
        grade_bonus = 5 if grade == 3 else 0

        return centrality_score + deficiency_score + grade_bonus

    def rank_skills_by_priority(
        self,
        skill_states: dict[str, float],
        G: nx.DiGraph,
        mastery_threshold: float = 0.85,
    ) -> list[tuple[str, float]]:
        """
        Returns skills sorted by priority (highest first),
        excluding already-mastered skills.

        Args:
            skill_states: Dict mapping standard_code -> p_mastered
            G: Skill dependency graph
            mastery_threshold: Skills above this are considered mastered

        Returns:
            List of (standard_code, priority_score) tuples, sorted by score descending
        """
        non_mastered = {code: p for code, p in skill_states.items() if p < mastery_threshold}
        scored = [
            (code, self.compute_priority_score(code, p, G))
            for code, p in non_mastered.items()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def get_prerequisite_chain(
        self,
        standard_code: str,
        skill_states: dict[str, float],
        G: nx.DiGraph,
        mastery_threshold: float = 0.85,
    ) -> list[str]:
        """
        Given a standard code, traverse the prerequisite graph backwards
        to identify all prerequisite skills that are below mastery threshold.

        Args:
            standard_code: The standard to find prerequisites for
            skill_states: Dict mapping standard_code -> p_mastered
            G: Skill dependency graph
            mastery_threshold: Skills below this are considered not mastered

        Returns:
            Ordered list of prerequisite standard codes (deepest first)
        """
        chain = []
        visited = set()

        def dfs_predecessors(code: str):
            if code in visited:
                return
            visited.add(code)

            for predecessor in G.predecessors(code):
                p_mastered = skill_states.get(predecessor, 0.5)
                if p_mastered < mastery_threshold:
                    dfs_predecessors(predecessor)

            p_mastered = skill_states.get(code, 0.5)
            if p_mastered < mastery_threshold:
                chain.append(code)

        dfs_predecessors(standard_code)
        return chain

    def find_unmet_prerequisites(
        self,
        standard_code: str,
        G: nx.DiGraph,
    ) -> list[str]:
        """
        Find all prerequisites for a standard, regardless of mastery level.

        Args:
            standard_code: The standard to find prerequisites for
            G: Skill dependency graph

        Returns:
            List of prerequisite standard codes (topologically sorted)
        """
        if standard_code not in G.nodes:
            return []

        # Get all ancestors (prerequisites)
        ancestors = nx.ancestors(G, standard_code)
        ancestors.add(standard_code)

        # Topological sort
        subgraph = G.subgraph(ancestors)
        try:
            return list(nx.topological_sort(subgraph))
        except nx.NetworkXUnfeasible:
            # Graph has a cycle - return empty list
            return []

    def get_module_name(self, standard_code: str) -> str:
        """
        Get the child-friendly module name for a standard code.

        Args:
            standard_code: Standard code

        Returns:
            Child-friendly module name
        """
        module_names = {
            # Grade 3 prerequisites
            "3.OA.A.4": "Finding the Missing Number",
            "3.OA.C.7": "Multiplication & Division Facts",
            "3.OA.D.8": "Two-Step Problem Solving",
            "3.NBT.A.2": "Adding & Subtracting Big Numbers",
            "3.NBT.A.3": "Multiplying by Tens",
            "3.NF.A.1": "Understanding Fractions",
            "3.NF.A.3": "Comparing Fractions",
            "3.GM.C.7": "Finding Area",
            "3.GM.D.8": "Measuring Perimeter",

            # Grade 4 standards
            "4.OA.A.1": "Multiplicative Comparisons",
            "4.OA.A.2": "Comparison Word Problems",
            "4.OA.A.3": "Multi-Step Problem Solving",
            "4.OA.B.4": "Factors, Multiples & Primes",
            "4.OA.C.5": "Number Patterns",
            "4.NBT.A.1": "Place Value: How Digits Work",
            "4.NBT.A.2": "Reading & Writing Big Numbers",
            "4.NBT.A.3": "Rounding to Any Place",
            "4.NBT.B.4": "Adding & Subtracting Large Numbers",
            "4.NBT.B.5": "Multi-Digit Multiplication",
            "4.NBT.B.6": "Division with Remainders",
            "4.NF.A.1": "Equivalent Fractions",
            "4.NF.A.2": "Comparing Fractions (Different Denominators)",
            "4.NF.B.3": "Adding & Subtracting Fractions",
            "4.NF.B.4": "Multiplying Fractions by Whole Numbers",
            "4.NF.C.5": "Fractions and Hundredths",
            "4.NF.C.6": "Decimal Notation",
            "4.NF.C.7": "Comparing Decimals",
            "4.GM.A.1": "Lines, Rays & Angles",
            "4.GM.A.2": "Classifying Shapes",
            "4.GM.A.3": "Lines of Symmetry",
            "4.GM.B.4": "Measurement Conversions",
            "4.GM.B.5": "Measurement Word Problems",
            "4.GM.C.6": "Understanding Angles",
            "4.GM.C.7": "Measuring Angles",
            "4.GM.C.8": "Adding Angles",
            "4.GM.D.9": "Area & Perimeter",
            "4.DR.A.1": "Line Plots with Fractions",
            "4.DR.B.2": "Reading Bar Graphs & Tables",
            "4.DR.C.3": "Mean, Median, Mode, Range",
        }

        return module_names.get(standard_code, f"Skill {standard_code}")

    def estimate_sessions_to_mastery(
        self,
        p_mastered: float,
        learning_rate: float = 0.10,
    ) -> int:
        """
        Estimate number of practice sessions to reach mastery (P > 0.85).

        Based on BKT default P(learn) = learning_rate per session.

        Args:
            p_mastered: Current P(mastered) probability
            learning_rate: Default BKT learning rate

        Returns:
            Estimated number of sessions needed
        """
        if p_mastered >= 0.85:
            return 0
        if p_mastered >= 0.70:
            return 2
        if p_mastered >= 0.50:
            return 4
        if p_mastered >= 0.30:
            return 6
        return 8


# Singleton instance for cached graph access
_graph_service: Optional[SkillGraphService] = None
_cached_graph: Optional[nx.DiGraph] = None


def get_cached_graph() -> Optional[nx.DiGraph]:
    """Get the cached skill graph if available."""
    return _cached_graph


def set_cached_graph(graph: nx.DiGraph) -> None:
    """Set the cached skill graph."""
    global _cached_graph
    _cached_graph = graph


def clear_cached_graph() -> None:
    """Clear the global cached skill graph."""
    global _cached_graph
    _cached_graph = None


async def initialize_skill_graph(db_session: AsyncSession) -> nx.DiGraph:
    """
    Initialize the global cached skill graph.
    Call this at application startup.
    """
    global _cached_graph
    service = SkillGraphService(db_session)
    _cached_graph = await service.get_graph()
    return _cached_graph
