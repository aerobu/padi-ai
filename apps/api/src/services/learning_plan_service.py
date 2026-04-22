"""
Learning Plan Service for generating and managing personalized learning plans.
"""
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.models import (
    LearningPlan,
    LearningPlanStatus,
    LearningPlanTrack,
    PlanModule,
    PlanLesson,
    LessonType,
    LessonStatus,
    StudentSkillState,
    Assessment,
    AssessmentStatus,
)
from src.repositories.student_repository import StudentRepository
from src.repositories.assessment_repository import AssessmentRepository


class LearningPlanService:
    """
    Service for generating and managing learning plans.

    A learning plan is a personalized sequence of learning modules
    generated from a student's diagnostic assessment results.
    """

    MASTERY_THRESHOLD = 0.85

    def __init__(self, session: AsyncSession):
        self.session = session
        self.student_repo = StudentRepository(session)
        self.assessment_repo = AssessmentRepository(session)

    async def generate_learning_plan(
        self,
        student_id: str,
        assessment_id: Optional[str] = None,
    ) -> LearningPlan:
        """
        Generate a learning plan for a student based on their diagnostic results.

        Args:
            student_id: Student ID
            assessment_id: Optional assessment ID (uses latest diagnostic if not provided)

        Returns:
            Created LearningPlan

        Raises:
            ValueError: If student has no diagnostic results
        """
        # Get the student's latest diagnostic assessment
        if assessment_id is None:
            result = await self.session.execute(
                select(Assessment)
                .where(Assessment.student_id == student_id)
                .where(Assessment.assessment_type == "diagnostic")
                .where(Assessment.status == AssessmentStatus.COMPLETED)
                .order_by(Assessment.created_at.desc())
                .limit(1)
            )
            assessment = result.scalar_one_or_none()
        else:
            assessment = await self.assessment_repo.get_by_id(assessment_id)

        if not assessment:
            raise ValueError(
                f"No completed diagnostic assessment found for student {student_id}"
            )

        # Get student skill states
        result = await self.session.execute(
            select(StudentSkillState)
            .where(StudentSkillState.student_id == student_id)
        )
        skill_states = result.scalars().all()

        if not skill_states:
            raise ValueError(
                f"No skill states found for student {student_id}. "
                "Please run diagnostic assessment first."
            )

        # Determine track
        track = await self._determine_track(skill_states)

        # Generate module sequence
        modules = await self._generate_module_sequence(
            student_id,
            skill_states,
            track,
        )

        # Calculate estimates
        total_modules = len(modules)
        total_lessons = sum(m["estimated_sessions"] for m in modules) * 1.5  # ~1.5 lessons per session
        total_minutes = total_lessons * 20  # 20 minutes per lesson

        # Calculate estimated completion date
        sessions_per_week = 3
        minutes_per_session = 20
        minutes_per_week = sessions_per_week * minutes_per_session
        total_weeks = total_minutes / minutes_per_week if minutes_per_week > 0 else 0
        estimated_completion_date = date.today() + timedelta(weeks=total_weeks)

        # Create learning plan
        plan = LearningPlan(
            id=str(__import__("uuid").uuid4()),
            student_id=student_id,
            assessment_id=assessment.id,
            track=track,
            status=LearningPlanStatus.ACTIVE.value,
            total_modules=total_modules,
            total_lessons=total_lessons,
            estimated_total_minutes=total_minutes,
            sessions_per_week=sessions_per_week,
            minutes_per_session=minutes_per_session,
            estimated_completion_date=estimated_completion_date,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.session.add(plan)
        await self.session.flush()

        # Create plan modules
        for i, module_def in enumerate(modules):
            module_status = "available" if i == 0 else "locked"

            module = PlanModule(
                id=str(__import__("uuid").uuid4()),
                plan_id=plan.id,
                standard_id=module_def["standard_code"],
                sequence_order=i + 1,
                status=module_status,
                lesson_count=module_def["estimated_sessions"],
                estimated_minutes=module_def["estimated_sessions"] * 20,
                entry_p_mastery=module_def["p_mastered_initial"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.session.add(module)

            # Create initial lessons for available module
            if module_status == "available":
                await self._create_lessons_for_module(module)

        await self.session.commit()
        
        # Load with relationships for return
        return await self.get_learning_plan(student_id, include_modules=True, include_lessons=True)

    async def _determine_track(
        self,
        skill_states: list[StudentSkillState],
    ) -> str:
        """
        Determine the student's learning track based on skill states.

        - Catch Up: >= 40% Below Par
        - Accelerate: >= 70% Above Par
        - On Track: Otherwise
        """
        below_par_count = sum(
            1 for s in skill_states if s.proficiency_level == "Below Par"
        )
        above_par_count = sum(
            1 for s in skill_states if s.proficiency_level == "Above Par"
        )
        total = len(skill_states)

        if total == 0:
            return LearningPlanTrack.ON_TRACK.value

        below_ratio = below_par_count / total
        above_ratio = above_par_count / total

        if below_ratio >= 0.40:
            return LearningPlanTrack.CATCH_UP.value
        elif above_ratio >= 0.70:
            return LearningPlanTrack.ACCELERATE.value
        else:
            return LearningPlanTrack.ON_TRACK.value

    async def _generate_module_sequence(
        self,
        student_id: str,
        skill_states: list[StudentSkillState],
        track: str,
    ) -> list[dict]:
        """
        Generate ordered list of modules for the learning plan.

        Returns list of module definitions with:
        - standard_code
        - priority_score
        - p_mastered_initial
        - estimated_sessions
        """
        # Get skill states with proficiency levels, joined with standard codes
        from sqlalchemy.orm import selectinload
        result = await self.session.execute(
            select(StudentSkillState)
            .where(StudentSkillState.student_id == student_id)
            .options(selectinload(StudentSkillState.standard))
        )
        skill_states_joined = result.scalars().all()

        skill_state_dict = {
            ss.standard.standard_code: {
                "p_mastered": ss.mastery_prob,
                "proficiency_level": ss.proficiency_level,
            }
            for ss in skill_states_joined
        }

        # Identify deficient skills (p_mastered < 0.85)
        non_mastered = {
            code: data["p_mastered"]
            for code, data in skill_state_dict.items()
            if data["p_mastered"] < self.MASTERY_THRESHOLD
        }

        # Import here to avoid circular imports
        from src.services.skill_graph_service import get_cached_graph, SkillGraphService

        G = get_cached_graph()
        if G is None:
            raise ValueError("Skill graph not initialized. Call initialize_skill_graph() first.")

        # Use SkillGraphService to rank by priority
        skill_graph_service = SkillGraphService(self.session)
        ranked_skills = skill_graph_service.rank_skills_by_priority(
            non_mastered,
            G,
            self.MASTERY_THRESHOLD,
        )

        # Build module sequence
        modules = []
        for standard_code, priority_score in ranked_skills:
            p_mastered = non_mastered.get(standard_code, 0.5)
            estimated_sessions = skill_graph_service.estimate_sessions_to_mastery(p_mastered)

            modules.append({
                "standard_code": standard_code,
                "priority_score": priority_score,
                "p_mastered_initial": p_mastered,
                "estimated_sessions": estimated_sessions,
                "track": track,
            })

        return modules

    async def _create_lessons_for_module(
        self,
        module: PlanModule,
    ) -> list[PlanLesson]:
        """
        Create lessons for a module based on the student's starting P(mastered).

        Creates 1-3 lessons:
        - Intro lesson (always)
        - Practice lesson (if needed)
        - Challenge lesson (if needed)
        """
        lessons = []
        p_mastered = module.entry_p_mastery or 0.5

        # Determine how many lessons needed
        if p_mastered >= 0.75:
            lesson_types = ["instruction"]
        elif p_mastered >= 0.50:
            lesson_types = ["instruction", "practice"]
        else:
            lesson_types = ["instruction", "practice", "review"]

        for i, lesson_type in enumerate(lesson_types):
            if lesson_type == "instruction":
                title = f"Introduction: {module.standard_id}"
                question_count = 5
                difficulty_range = (1, 2)
            elif lesson_type == "practice":
                title = f"Practice: {module.standard_id}"
                question_count = 10
                difficulty_range = (2, 4)
            else:  # review
                title = f"Challenge: {module.standard_id}"
                question_count = 10
                difficulty_range = (3, 5)

            lesson = PlanLesson(
                id=str(__import__("uuid").uuid4()),
                module_id=module.id,
                sequence_order=i + 1,
                lesson_type=lesson_type,
                title=title,
                question_count=question_count,
                difficulty_range_min=difficulty_range[0],
                difficulty_range_max=difficulty_range[1],
                status=LessonStatus.AVAILABLE.value,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.session.add(lesson)
            lessons.append(lesson)

        await self.session.flush()
        return lessons

    async def get_learning_plan(
        self,
        student_id: str,
        include_modules: bool = False,
        include_lessons: bool = False,
    ) -> Optional[LearningPlan]:
        """
        Get student's active learning plan.

        Args:
            student_id: Student ID
            include_modules: Whether to include modules
            include_lessons: Whether to include lessons within modules

        Returns:
            LearningPlan or None if no active plan exists
        """
        from sqlalchemy.orm import selectinload

        stmt = select(LearningPlan).where(
            LearningPlan.student_id == student_id,
            LearningPlan.status == LearningPlanStatus.ACTIVE.value
        )

        if include_modules:
            if include_lessons:
                stmt = stmt.options(
                    selectinload(LearningPlan.modules).selectinload(PlanModule.lessons)
                )
            else:
                stmt = stmt.options(selectinload(LearningPlan.modules))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def unlock_next_module(
        self,
        plan_id: str,
        completed_module_id: str,
    ) -> Optional[PlanModule]:
        """
        Unlock the next module in the sequence if the completed module is now mastered.

        Args:
            plan_id: Learning plan ID
            completed_module_id: Module that was just completed

        Returns:
            Newly unlocked module or None if no more modules available
        """
        # Get the plan with modules loaded
        stmt = select(LearningPlan).where(LearningPlan.id == plan_id).options(selectinload(LearningPlan.modules))
        result = await self.session.execute(stmt)
        plan = result.scalar_one_or_none()

        if not plan or not plan.modules:
            return None

        # Modules are sorted by sequence_order
        modules = sorted(plan.modules, key=lambda m: m.sequence_order)

        # Find the completed module's position
        completed_idx = next(
            (i for i, m in enumerate(modules) if m.id == completed_module_id),
            None,
        )

        if completed_idx is None or completed_idx + 1 >= len(modules):
            return None

        # Unlock next module
        next_module = modules[completed_idx + 1]
        next_module.status = "available"
        next_module.started_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(next_module)

        return next_module

    async def update_module_progress(
        self,
        module_id: str,
        p_mastered: float,
        lessons_completed: int = 0,
        minutes_spent: int = 0,
    ) -> Optional[PlanModule]:
        """
        Update a module's progress after practice sessions.

        Args:
            module_id: Module ID
            p_mastered: Updated P(mastered) from BKT
            lessons_completed: Number of lessons completed
            minutes_spent: Minutes spent on this module

        Returns:
            Updated PlanModule or None
        """
        result = await self.session.execute(
            select(PlanModule).where(PlanModule.id == module_id)
        )
        module = result.scalar_one_or_none()

        if not module:
            return None

        module.exit_p_mastery = p_mastered
        module.completed_lessons = lessons_completed
        module.actual_minutes = (module.actual_minutes or 0) + minutes_spent

        # Check if module is now mastered
        if p_mastered >= self.MASTERY_THRESHOLD:
            module.status = "completed"
            module.completed_at = datetime.utcnow()

            # Unlock next module
            await self.unlock_next_module(module.plan_id, module_id)
        elif module.status == "locked":
            module.status = "in_progress"
            if not module.started_at:
                module.started_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(module)

        return module

    async def estimate_plan_duration(
        self,
        modules: list[dict],
        minutes_per_day: int = 20,
        days_per_week: int = 5,
    ) -> float:
        """
        Estimate total weeks to complete the learning plan.

        Args:
            modules: List of module definitions with estimated_sessions
            minutes_per_day: Minutes of practice per day
            days_per_week: Days of practice per week

        Returns:
            Estimated weeks to completion
        """
        total_sessions = sum(
            m.get("estimated_sessions", 0) for m in modules if m.get("estimated_sessions", 0) > 0
        )
        total_minutes = total_sessions * minutes_per_day
        minutes_per_week = minutes_per_day * days_per_week

        if minutes_per_week == 0:
            return 0

        return round(total_minutes / minutes_per_week, 1)


# Singleton pattern for service access
_service: Optional[LearningPlanService] = None


def get_learning_plan_service(db_session: AsyncSession) -> LearningPlanService:
    """Get or create a LearningPlanService instance."""
    global _service
    if _service is None:
        _service = LearningPlanService(db_session)
    return _service
