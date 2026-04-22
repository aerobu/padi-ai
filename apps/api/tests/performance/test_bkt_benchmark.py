"""
Performance Benchmark: BKT Computation
=======================================

Purpose: Verify that Bayesian Knowledge Tracing computations meet performance SLA.

Target Metrics:
- Single student skill state update: < 50ms
- Full diagnostic assessment (35 questions): < 2000ms
- BKT state calculation for 50 standards: < 500ms

References:
- ENG-001-stage1.md (lines 1640-1680) - BKT performance requirements
- 10-lifecycle-stage1.md (lines 2400-2450) - Performance benchmarks
"""

import pytest
import time
import statistics
import os
import sys
from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure root of apps/api is in path so 'src' can be imported as a package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.services.bkt_service import BKTService


class TestBKTComputationPerformance:
    """Performance tests for BKT computations."""

    @pytest.fixture
    def bkt_service(self) -> BKTService:
        """Create BKT service instance."""
        return BKTService()

    def test_single_update_latency(self, bkt_service):
        """SVC-PERF-001: Single BKT update should be < 50ms."""
        latencies = []
        
        for i in range(100):
            start_time = time.perf_counter()
            bkt_service.update_state(
                standard_code=f"std.{i}",
                response_correct=(i % 2 == 0)
            )
            latencies.append((time.perf_counter() - start_time) * 1000)
            
        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        
        print(f"\nBKT Single Update Latency: Avg={avg_latency:.2f}ms, P95={p95_latency:.2f}ms")
        assert avg_latency < 50
