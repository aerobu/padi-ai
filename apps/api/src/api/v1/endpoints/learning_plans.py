"""
Learning Plan endpoints for personalized student learning plans.
"""
import logging
from datetime import datetime, timedelta
from typing import Annotated, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.database import get_db
from src.core.security import verify_jwt
from src.repositories.student_repository import StudentRepository
from src.models.models import (
    PracticeSession,
    PracticeSessionStatus,
    PracticeSessionQuestion,
    StudentSkillState,
    PlanLesson,
    PlanModule,
    Student,
    ModuleStatus,
)
from src.services.learning_plan_service import LearningPlanService
from src.services.skill_graph_service import get_cached_graph, SkillGraphService
from src.services.badge_service import BadgeService, BadgeType
from src.services.streak_service import StreakService
from src.schemas.learning_plan import (
    LearningPlanGenerateRequest,
    ModuleCompleteRequest,
    LearningPlanWithModulesResponse,
    NextLessonResponse,
    ResponseSubmission,
    SessionAnswerResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_learning_plan_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> LearningPlanService:
    """Get learning plan service from database session."""
    return LearningPlanService(db)


@router.post(
    "/learning-plans/generate",
    status_code=status.HTTP_201_CREATED,
    summary="Generate learning plan",
    description="Generate a personalized learning plan for a student based on their diagnostic assessment.",
)
async def generate_learning_plan(
    request: LearningPlanGenerateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_payload: Annotated[dict, Depends(verify_jwt)],
) -> dict:
    """
    Generate a learning plan for a student.

    The plan is based on the student's diagnostic assessment results and includes:
    - Ordered modules based on skill proficiency and prerequisites
    - Estimated time to mastery
    - Track classification (catch_up, on_track, accelerate)
    """
    try:
        # Verify student ownership
        student_repo = StudentRepository(db)
        student = await student_repo.get_by_id(request.student_id)

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {request.student_id} not found",
            )

        # Check if student belongs to authenticated user
        user_id = user_payload.get("sub") or user_payload.get("auth0_id")

        if user_id != student.parent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to generate a plan for this student",
            )

        # Generate learning plan
        service = LearningPlanService(db)
        plan = await service.generate_learning_plan(request.student_id, request.assessment_id)

        # Return plan details
        return {
            "plan_id": plan.id,
            "student_id": plan.student_id,
            "track": plan.track,
            "status": plan.status,
            "total_modules": plan.total_modules,
            "total_lessons": plan.total_lessons,
            "estimated_total_minutes": plan.estimated_total_minutes,
            "estimated_completion_date": plan.estimated_completion_date.isoformat()
            if plan.estimated_completion_date
            else None,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error generating learning plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/learning-plans/sequence",
    summary="Get skill sequence",
    description="Get the topological sort sequence for a set of skills.",
    tags=["internal"],
)
async def get_skill_sequence(
    standard_codes: str,  # Comma-separated list
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Get the topological sort sequence for a list of standard codes.

    This endpoint is for internal use and admin purposes.
    """
    try:
        codes = [c.strip() for c in standard_codes.split(",") if c.strip()]

        G = get_cached_graph()
        if G is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Skill graph not initialized",
            )

        service = SkillGraphService(db)
        sequence = service.get_topological_sequence(codes, G)

        return {
            "standard_codes": codes,
            "sequence": sequence,
            "length": len(sequence),
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error getting skill sequence: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/learning-plans/{student_id}",
    response_model=dict,
    summary="Get learning plan",
    description="Get the current active learning plan for a student.",
)
async def get_learning_plan(
    student_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_payload: Annotated[dict, Depends(verify_jwt)],
) -> dict:
    """
    Get a student's current learning plan.

    Returns the plan with all modules and their lessons.
    """
    try:
        # Verify student ownership
        student_repo = StudentRepository(db)
        student = await student_repo.get_by_id(student_id)

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {student_id} not found",
            )

        user_id = user_payload.get("sub") or user_payload.get("auth0_id")

        if user_id != student.parent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this student's plan",
            )

        # Get learning plan
        service = LearningPlanService(db)
        plan = await service.get_learning_plan(
            student_id,
            include_modules=True,
            include_lessons=True,
        )

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active learning plan found for student {student_id}",
            )

        # Build response
        return {
            "plan": {
                "id": plan.id,
                "student_id": plan.student_id,
                "track": plan.track,
                "status": plan.status,
                "total_modules": plan.total_modules,
                "completed_modules": plan.completed_modules,
                "total_lessons": plan.total_lessons,
                "completed_lessons": plan.completed_lessons,
                "estimated_total_minutes": plan.estimated_total_minutes,
                "estimated_completion_date": plan.estimated_completion_date.isoformat()
                if plan.estimated_completion_date
                else None,
                "created_at": plan.created_at.isoformat() if plan.created_at else None,
                "modules": [
                    {
                        "id": m.id,
                        "standard_code": m.standard_id,
                        "sequence_order": m.sequence_order,
                        "status": m.status,
                        "lesson_count": m.lesson_count,
                        "completed_lessons": m.completed_lessons,
                        "estimated_minutes": m.estimated_minutes,
                        "entry_p_mastery": m.entry_p_mastery,
                        "exit_p_mastery": m.exit_p_mastery,
                        "lessons": [
                            {
                                "id": l.id,
                                "sequence_order": l.sequence_order,
                                "lesson_type": l.lesson_type,
                                "title": l.title,
                                "status": l.status,
                                "question_count": l.question_count,
                            }
                            for l in getattr(m, "lessons", [])
                        ],
                    }
                    for m in getattr(plan, "modules", [])
                ],
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/learning-plans/{plan_id}/modules/{module_id}/complete",
    summary="Complete module",
    description="Mark a module as complete and update BKT state.",
)
async def complete_module(
    plan_id: str,
    module_id: str,
    request: ModuleCompleteRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_payload: Annotated[dict, Depends(verify_jwt)],
) -> dict:
    """
    Mark a module as complete after practice sessions.

    Updates the BKT P(mastered) and unlocks the next module if applicable.
    """
    try:
        # Verify plan ownership
        from src.models.models import LearningPlan as PlanModel

        result = await db.execute(select(PlanModel).where(PlanModel.id == plan_id))
        plan = result.scalar_one_or_none()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Learning plan {plan_id} not found",
            )

        # Verify the authenticated user owns this student's plan
        user_id = user_payload.get("sub") or user_payload.get("auth0_id")
        
        # Get student to check parent_id
        from src.models.models import Student as StudentModel
        student_result = await db.execute(select(StudentModel).where(StudentModel.id == plan.student_id))
        student = student_result.scalar_one_or_none()
        
        if not student or student.parent_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to complete this plan",
            )

        # Update module progress
        service = LearningPlanService(db)
        updated_module = await service.update_module_progress(
            module_id=module_id,
            p_mastered=request.p_mastered,
            lessons_completed=request.lessons_completed,
            minutes_spent=request.minutes_spent,
        )

        if not updated_module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module {module_id} not found",
            )

        return {
            "module_id": updated_module.id,
            "status": updated_module.status,
            "p_mastered": updated_module.exit_p_mastery,
            "next_module_unlocked": updated_module.status == "completed",
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing module: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/learning-plans/{student_id}/next-lesson",
    summary="Get next lesson",
    description="Get the next available lesson for a student's current module.",
)
async def get_next_lesson(
    student_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_payload: Annotated[dict, Depends(verify_jwt)],
) -> NextLessonResponse:
    """
    Get the next available lesson for a student.

    Returns the first available/in_progress lesson from the first
    available/in_progress module.
    """
    try:
        # Verify student ownership
        student_repo = StudentRepository(db)
        student = await student_repo.get_by_id(student_id)

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {student_id} not found",
            )

        user_id = user_payload.get("sub") or user_payload.get("auth0_id")

        if user_id != student.parent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this student's plan",
            )

        # Get learning plan
        service = LearningPlanService(db)
        plan = await service.get_learning_plan(
            student_id,
            include_modules=True,
            include_lessons=True,
        )

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active learning plan found for student {student_id}",
            )

        # Find first available or in_progress module
        modules = getattr(plan, "modules", [])
        target_module = None

        for module in modules:
            if module.status in ["available", "in_progress"]:
                target_module = module
                break

        if not target_module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No available modules in learning plan",
            )

        # Find first available lesson in the module
        lessons = getattr(target_module, "lessons", [])
        target_lesson = None

        for lesson in lessons:
            if lesson.status == "available":
                target_lesson = lesson
                break

        if not target_lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No available lessons in current module",
            )

        return {
            "module": {
                "id": target_module.id,
                "standard_code": target_module.standard_id,
                "module_name": SkillGraphService(None).get_module_name(target_module.standard_id)
                if hasattr(SkillGraphService, 'get_module_name')
                else target_module.standard_id,
            },
            "lesson": {
                "id": target_lesson.id,
                "title": target_lesson.title,
                "lesson_type": target_lesson.lesson_type,
                "question_count": target_lesson.question_count,
                "difficulty_range": {
                    "min": target_lesson.difficulty_range_min or 1,
                    "max": target_lesson.difficulty_range_max or 5,
                },
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting next lesson: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/students/{student_id}/badges",
    summary="Get student badges",
    description="Get all badges earned by a student.",
)
async def get_student_badges(
    student_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_payload: Annotated[dict, Depends(verify_jwt)],
) -> dict:
    """
    Get all badges for a student.

    Requires ownership of the student.
    """
    try:
        # Verify ownership
        student_repo = StudentRepository(db)
        student = await student_repo.get_by_id(student_id)

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {student_id} not found",
            )

        user_id = user_payload.get("sub") or user_payload.get("auth0_id")
        if user_id != student.parent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this student's badges",
            )

        # Get badges
        badge_service = BadgeService(db)
        badges = await badge_service.get_student_badges(student_id)

        return {"badges": badges}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting student badges: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/students/{student_id}/streak",
    summary="Get student streak",
    description="Get activity streak and stats for a student.",
)
async def get_student_streak(
    student_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_payload: Annotated[dict, Depends(verify_jwt)],
) -> dict:
    """
    Get streak info for a student.

    Requires ownership of the student.
    """
    try:
        # Verify ownership
        student_repo = StudentRepository(db)
        student = await student_repo.get_by_id(student_id)

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {student_id} not found",
            )

        user_id = user_payload.get("sub") or user_payload.get("auth0_id")
        if user_id != student.parent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this student's streak",
            )

        # Get streak info
        streak_service = StreakService(db)
        streak_info = await streak_service.get_streak_info(student_id)

        # Get weekly goal progress
        goal_progress = await streak_service.get_weekly_goal_progress(student_id)

        return {
            "streak": streak_info,
            "weekly_goal": goal_progress,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting student streak: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/sessions/{session_id}/answer",
    summary="Submit session answer",
    description="Submit an answer during a practice session and get feedback.",
)
async def submit_session_answer(
    session_id: str,
    request: ResponseSubmission,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_payload: Annotated[dict, Depends(verify_jwt)],
) -> SessionAnswerResponse:
    """
    Submit an answer during a practice session.

    Returns whether the answer is correct, the correct answer, explanation,
    and current progress. Also updates BKT state.
    """
    try:
        # Get practice session
        result = await db.execute(
            select(PracticeSession).where(PracticeSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Practice session {session_id} not found",
            )

        # Get lesson to verify ownership
        lesson_result = await db.execute(
            select(PlanLesson).where(PlanLesson.id == session.lesson_id)
        )
        lesson = lesson_result.scalar_one_or_none()

        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found",
            )

        module_result = await db.execute(
            select(PlanModule).where(PlanModule.id == lesson.module_id)
        )
        module = module_result.scalar_one_or_none()

        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found",
            )

        from src.models.models import LearningPlan as PlanModel

        plan_result = await db.execute(
            select(PlanModel).where(PlanModel.id == module.plan_id)
        )
        plan = plan_result.scalar_one_or_none()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning plan not found",
            )

        # Verify ownership - user must be the parent of the student
        student_id = plan.student_id
        student_result = await db.execute(
            select(Student).where(Student.id == student_id)
        )
        student = student_result.scalar_one_or_none()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {student_id} not found",
            )

        user_id = user_payload.get("sub") or user_payload.get("auth0_id")

        if user_id != student.parent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this session",
            )

        from src.models.models import GeneratedQuestion
        from sqlalchemy import func

        # Find the next unanswered PracticeSessionQuestion by sequence
        next_psq_result = await db.execute(
            select(PracticeSessionQuestion)
            .where(
                PracticeSessionQuestion.session_id == session_id,
                PracticeSessionQuestion.student_answer.is_(None),
            )
            .order_by(PracticeSessionQuestion.sequence.asc())
            .limit(1)
        )
        next_psq = next_psq_result.scalar_one_or_none()

        if next_psq is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Session has no unanswered questions remaining",
            )

        question_result = await db.execute(
            select(GeneratedQuestion).where(GeneratedQuestion.id == next_psq.question_id)
        )
        question = question_result.scalar_one_or_none()

        if question is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found",
            )

        is_correct = request.answer.strip().lower() == question.correct_answer.strip().lower()

        # Update the PSQ row in place (no new row)
        next_psq.student_answer = request.answer
        next_psq.is_correct = is_correct
        next_psq.time_spent_ms = request.time_spent_ms
        next_psq.answered_at = datetime.utcnow()

        # Update BKT for this skill
        skill_state_result = await db.execute(
            select(StudentSkillState)
            .where(
                StudentSkillState.student_id == student_id,
                StudentSkillState.standard_id == question.standard_id,
            )
        )
        skill_state = skill_state_result.scalar_one_or_none()

        if skill_state:
            from src.services.bkt_impl import PyBKT

            bkt = PyBKT.from_db_record(skill_state)
            bkt.forward_inference(1 if is_correct else 0)
            bkt.to_db_record(skill_state)

        await db.commit()

        # Compute progress: count answered PSQs for this session
        answered_count_result = await db.execute(
            select(func.count())
            .select_from(PracticeSessionQuestion)
            .where(
                PracticeSessionQuestion.session_id == session_id,
                PracticeSessionQuestion.student_answer.is_not(None),
            )
        )
        answered_count = answered_count_result.scalar_one()

        return SessionAnswerResponse(
            correct=is_correct,
            correct_answer=question.correct_answer,
            explanation=getattr(question, "explanation", None),
            progress={
                "current_question": answered_count,
                "total_questions": session.question_count,
            },
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting answer: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/sessions/{session_id}/complete",
    summary="Complete session",
    description="Mark practice session as complete and trigger gamification.",
)
async def complete_session(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_payload: Annotated[dict, Depends(verify_jwt)],
) -> dict:
    """
    Mark practice session as complete.

    Triggers BKT finalization, badge checks, and module progression.
    """
    try:
        # Get practice session
        result = await db.execute(
            select(PracticeSession).where(PracticeSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Practice session {session_id} not found",
            )

        # Verify ownership through the plan hierarchy
        from src.models.models import LearningPlan as PlanModel

        lesson_result = await db.execute(
            select(PlanLesson).where(PlanLesson.id == session.lesson_id)
        )
        lesson = lesson_result.scalar_one_or_none()

        if not lesson:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

        module_result = await db.execute(
            select(PlanModule).where(PlanModule.id == lesson.module_id)
        )
        module = module_result.scalar_one_or_none()

        if not module:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

        plan_result = await db.execute(
            select(PlanModel).where(PlanModel.id == module.plan_id)
        )
        plan = plan_result.scalar_one_or_none()

        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning plan not found")

        student_result = await db.execute(
            select(Student).where(Student.id == plan.student_id)
        )
        student = student_result.scalar_one_or_none()

        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

        user_id = user_payload.get("sub") or user_payload.get("auth0_id")

        if student.parent_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to complete this session",
            )

        # Mark session as complete
        session.status = PracticeSessionStatus.COMPLETED
        session.completed_at = datetime.utcnow()

        # Calculate accuracy from responses
        responses_result = await db.execute(
            select(PracticeSessionQuestion)
            .where(PracticeSessionQuestion.practice_session_id == session_id)
        )
        responses = responses_result.scalars().all()

        if responses:
            correct_count = sum(1 for r in responses if r.is_correct)
            session.accuracy_percentage = (correct_count / len(responses)) * 100

        await db.commit()

        # Get streak service and record activity
        streak_service = StreakService(db)
        await streak_service.record_activity(student.id, session_id)

        # Get badge service and check/award badges
        badge_service = BadgeService(db)

        # Check for plan progress badges
        modules_completed = sum(
            1 for m in plan.modules if m.status == ModuleStatus.COMPLETED.value
        )
        total_modules = len(plan.modules)

        new_badges = await badge_service.check_and_award_badges(
            student_id=student.id,
            activity_type="plan_progress",
            modules_completed=modules_completed,
            total_modules=total_modules,
        )

        # Check for perfect module badge
        if session.accuracy_percentage == 100:
            perfect_badges = await badge_service.check_and_award_badges(
                student_id=student.id,
                activity_type="module_complete",
                accuracy=100,
            )
            new_badges.extend(perfect_badges)

        return {
            "status": "completed",
            "accuracy": session.accuracy_percentage,
            "new_badges": [b.value for b in new_badges],
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
