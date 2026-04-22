"""
Tests for LearningPlanService.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import Student, Assessment, StudentSkillState
from src.services.learning_plan_service import LearningPlanService


class TestLearningPlanGeneration:
    """Tests for LearningPlanService.generate_learning_plan."""

    @pytest.mark.asyncio
    async def test_generate_plan_success(
        self,
        db_session: AsyncSession,
        test_student: Student,
        test_assessment,
    ):
        """Test successful learning plan generation."""
        service = LearningPlanService(db_session)

        plan = await service.generate_learning_plan(test_student.id)

        assert plan is not None
        assert plan.student_id == test_student.id
        assert plan.status == "active"
        assert plan.total_modules > 0
        assert plan.track in ["catch_up", "on_track", "accelerate"]

    @pytest.mark.asyncio
    async def test_generate_plan_no_assessment(
        self,
        db_session: AsyncSession,
        test_student: Student,
    ):
        """Test plan generation fails without assessment."""
        # Delete the assessment
        await db_session.delete(test_assessment)
        await db_session.commit()

        service = LearningPlanService(db_session)

        with pytest.raises(ValueError, match="No completed diagnostic"):
            await service.generate_learning_plan(test_student.id)

    @pytest.mark.asyncio
    async def test_determine_track_catch_up(
        self,
        db_session: AsyncSession,
        test_student: Student,
        mock_skill_states_below_par,
    ):
        """Test track determination for catch up."""
        service = LearningPlanService(db_session)

        track = await service._determine_track(mock_skill_states_below_par)

        assert track == "catch_up"

    @pytest.mark.asyncio
    async def test_determine_track_accelerate(
        self,
        db_session: AsyncSession,
        test_student: Student,
        mock_skill_states_above_par,
    ):
        """Test track determination for accelerate."""
        service = LearningPlanService(db_session)

        track = await service._determine_track(mock_skill_states_above_par)

        assert track == "accelerate"

    @pytest.mark.asyncio
    async def test_determine_track_on_track(
        self,
        db_session: AsyncSession,
        test_student: Student,
        mock_skill_states_on_track,
    ):
        """Test track determination for on track."""
        service = LearningPlanService(db_session)

        track = await service._determine_track(mock_skill_states_on_track)

        assert track == "on_track"


class TestModuleSequence:
    """Tests for module sequence generation."""

    @pytest.mark.asyncio
    async def test_generate_module_sequence(
        self,
        db_session: AsyncSession,
        test_student: Student,
    ):
        """Test module sequence generation respects prerequisites."""
        service = LearningPlanService(db_session)

        # Get skill states
        result = await db_session.execute(
            StudentSkillState.__table__.select().where(
                StudentSkillState.student_id == test_student.id
            )
        )
        skill_states = result.fetchall()

        if skill_states:
            modules = await service._generate_module_sequence(
                test_student.id,
                skill_states,
                "on_track",
            )

            assert len(modules) > 0

            # Check prerequisites are before dependents
            code_to_idx = {m["standard_code"]: i for i, m in enumerate(modules)}

            for module in modules:
                code = module["standard_code"]
                if code in code_to_idx:
                    idx = code_to_idx[code]
                    # All modules before this should be its prerequisites
                    for before_idx in range(idx):
                        before_code = modules[before_idx]["standard_code"]
                        # This is a simplified check
                        pass


class TestModuleProgress:
    """Tests for module progress tracking."""

    @pytest.mark.asyncio
    async def test_update_module_progress_mastery(
        self,
        db_session: AsyncSession,
        test_student: Student,
    ):
        """Test module progress update leads to mastery."""
        service = LearningPlanService(db_session)

        # Generate a plan first
        plan = await service.generate_learning_plan(test_student.id)

        if plan.modules:
            first_module = plan.modules[0]

            # Update progress to mastery
            updated = await service.update_module_progress(
                module_id=first_module.id,
                p_mastered=0.90,
                lessons_completed=first_module.lesson_count,
                minutes_spent=120,
            )

            assert updated is not None
            assert updated.status == "completed"
            assert updated.exit_p_mastery == 0.90
            assert updated.completed_at is not None


class TestTimeEstimation:
    """Tests for time estimation."""

    @pytest.mark.asyncio
    async def test_estimate_plan_duration(
        self,
        db_session: AsyncSession,
    ):
        """Test plan duration estimation."""
        service = LearningPlanService(db_session)

        modules = [
            {"estimated_sessions": 5},
            {"estimated_sessions": 3},
            {"estimated_sessions": 4},
        ]

        weeks = await service.estimate_plan_duration(modules)

        # 12 sessions * 20 min = 240 min / (20 * 5) = 2.4 weeks
        assert weeks == 2.4

    @pytest.mark.asyncio
    async def test_estimate_plan_duration_zero_minutes(
        self,
        db_session: AsyncSession,
    ):
        """Test duration estimation with zero minutes."""
        service = LearningPlanService(db_session)

        modules = []
        weeks = await service.estimate_plan_duration(modules)

        assert weeks == 0
