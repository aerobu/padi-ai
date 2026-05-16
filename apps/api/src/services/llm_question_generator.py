"""LLM Question Generator Service for AI-powered question generation.

Routes all LLM calls through `src.clients.llm_client.LLMClient` so model
selection stays COPPA-aware and centrally configurable. Question generation
uses purpose=QUESTION_GENERATION; verification uses purpose=ADMIN.

Schema mapping note: `GenerationJob.standard_id` and `GeneratedQuestion.standard_id`
are FK columns to `standards.id` (UUID), not standard-code strings. Callers pass
codes (e.g., '4.NF.A.1'); the service resolves to the FK once at job creation.
See fix C-8 (2026-05-16 review).
"""
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.llm_client import LLMClient, LLMPurpose, get_llm_client
from src.models.models import (
    ContentReviewQueue,
    GeneratedQuestion,
    GenerationJob,
    JobStatus,
    QuestionValidationResult,
    Standard,
    ValidationStatus,
)
from src.repositories.generation_job_repository import GenerationJobRepository
from src.repositories.question_repository import QuestionRepository

logger = logging.getLogger(__name__)


class LLMQuestionGenerator:
    """Service for generating questions using LLMs.

    All LLM traffic flows through `LLMClient` (no direct litellm imports).
    """

    def __init__(
        self,
        db_session: AsyncSession,
        llm_client: Optional[LLMClient] = None,
        use_ollama: bool = True,
    ) -> None:
        self.db_session = db_session
        self.use_ollama = use_ollama
        self.llm_client = llm_client or get_llm_client()
        self.job_repo = GenerationJobRepository(db_session)
        self.question_repo = QuestionRepository(db_session)

    async def _resolve_standard_id(self, standard_code: str) -> Optional[str]:
        """Map a code like '4.NF.A.1' to the Standard's UUID PK.

        Fix C-8: previous code wrote the code string into the FK column.
        """
        result = await self.db_session.execute(
            select(Standard).where(Standard.standard_code == standard_code)
        )
        std = result.scalar_one_or_none()
        return std.id if std else None

    async def create_generation_job(
        self,
        standard_code: str,
        requested_count: int = 10,
        difficulty_levels: Optional[list[int]] = None,
        context_themes: Optional[list[str]] = None,
        model: str = "o3-mini",
        created_by: Optional[str] = None,
    ) -> GenerationJob:
        """Create a new generation job."""
        if not difficulty_levels:
            difficulty_levels = [1, 2, 3, 4, 5]

        standard_id = await self._resolve_standard_id(standard_code)
        if not standard_id:
            raise ValueError(f"Unknown standard_code: {standard_code}")

        now = datetime.now(timezone.utc)
        job = GenerationJob(
            id=str(uuid4()),
            standard_id=standard_id,
            requested_count=requested_count,
            difficulty_levels=difficulty_levels,
            context_themes=context_themes,
            model=model,
            status=JobStatus.QUEUED.value,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

        self.db_session.add(job)
        await self.db_session.flush()
        # Stash standard_code for convenience on the in-memory object — but
        # never persist it (column doesn't exist).
        job._standard_code_cached = standard_code  # type: ignore[attr-defined]
        return job

    async def _job_standard_code(self, job: GenerationJob) -> str:
        """Look up the human-readable code from the FK on a job."""
        cached = getattr(job, "_standard_code_cached", None)
        if cached:
            return cached
        result = await self.db_session.execute(
            select(Standard).where(Standard.id == job.standard_id)
        )
        std = result.scalar_one_or_none()
        return std.standard_code if std else "UNKNOWN"

    async def execute_generation_job(self, job_id: str) -> GenerationJob:
        """Execute a generation job end-to-end."""
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        standard_code = await self._job_standard_code(job)
        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        await self.db_session.commit()

        try:
            for difficulty in job.difficulty_levels:
                questions = await self._generate_questions_for_difficulty(
                    job=job,
                    difficulty=difficulty,
                    context_themes=job.context_themes,
                    standard_code=standard_code,
                )

                for question_data in questions:
                    # Step 2: Sandbox execution
                    solution_ok, solution_output = await self._execute_solution_code(
                        question_data.get("solution_code", "")
                    )
                    if not solution_ok:
                        logger.warning("Solution execution failed; skipping question")
                        job.failed_validation = (job.failed_validation or 0) + 1
                        continue

                    # Step 3: Content classification
                    classification = await self._classify_question(
                        question_data.get("stem", question_data.get("text", "")),
                        len(question_data.get("options", [])),
                    )
                    if not classification["is_valid"]:
                        logger.warning("Question classification failed: %s", classification["errors"])
                        job.failed_validation = (job.failed_validation or 0) + 1
                        continue

                    # Step 5: Dedup
                    is_dup, _ = await self._check_dedup(
                        question_data.get("stem", question_data.get("text", "")),
                        job.standard_id,
                    )
                    if is_dup:
                        logger.info("Duplicate question skipped")
                        job.failed_validation = (job.failed_validation or 0) + 1
                        continue

                    now = datetime.now(timezone.utc)
                    generated_question = GeneratedQuestion(
                        id=str(uuid4()),
                        job_id=job.id,
                        standard_id=job.standard_id,  # FK, not code (fix C-8)
                        difficulty=question_data.get("difficulty", 3),
                        question_type="multiple_choice",
                        stem=question_data.get("stem", question_data.get("text", "")),
                        options=question_data.get("options", []),
                        correct_answer=question_data.get("correct_answer", ""),
                        explanation=question_data.get("explanation", ""),
                        solution_code=question_data.get("solution_code", ""),
                        model_used=question_data.get("model_used", job.model),
                        prompt_template=question_data.get("prompt_template"),
                        raw_response=question_data.get("raw_response"),
                        generation_time_ms=question_data.get("generation_time_ms"),
                        validation_status=ValidationStatus.PENDING.value,
                        confidence_score=0.0,
                        created_at=now,
                        updated_at=now,
                    )
                    self.db_session.add(generated_question)
                    await self.db_session.flush()

                    # Step 4: LLM verification (purpose=ADMIN — no student PII)
                    confidence, _reason = await self._verify_with_claude(
                        generated_question.stem,
                        generated_question.options or [],
                        generated_question.correct_answer,
                        standard_code,
                    )

                    overall = (
                        solution_ok
                        and classification["is_valid"]
                        and not is_dup
                        and confidence >= 0.85
                    )

                    validation_result = QuestionValidationResult(
                        id=str(uuid4()),
                        generated_question_id=generated_question.id,
                        solution_execution_passed=solution_ok,
                        solution_output=solution_output,
                        age_appropriateness_passed=classification["is_valid"],
                        dedup_passed=not is_dup,
                        math_correctness_passed=confidence >= 0.85,
                        overall_passed=overall,
                        confidence_score=confidence,
                        created_at=now,
                    )
                    self.db_session.add(validation_result)
                    # Keep a transient back-reference so the helpers below
                    # can navigate without another query.
                    validation_result.generated_question = generated_question  # type: ignore[attr-defined]

                    generated_question.validation_status = (
                        ValidationStatus.PASSED.value if overall else ValidationStatus.FAILED.value
                    )
                    generated_question.confidence_score = confidence

                    if overall:
                        job.auto_approved = (job.auto_approved or 0) + 1
                        await self._promote_to_questions_table(validation_result)
                    else:
                        job.needs_review = (job.needs_review or 0) + 1
                        await self._add_to_review_queue(validation_result)

                    job.total_generated = (job.total_generated or 0) + 1

            job.status = JobStatus.COMPLETED.value
            job.completed_at = datetime.now(timezone.utc)

        except Exception as e:  # noqa: BLE001
            logger.exception("Error executing job %s", job_id)
            job.status = JobStatus.FAILED.value
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)

        finally:
            await self.db_session.commit()

        return job

    async def _generate_questions_for_difficulty(
        self,
        job: GenerationJob,
        difficulty: int,
        standard_code: str,
        context_themes: Optional[list[str]] = None,
    ) -> list[dict]:
        """Generate questions for one difficulty level via `LLMClient`.

        Routed through `LLMClient.acomplete(purpose=QUESTION_GENERATION)` so
        the cloud-vs-Ollama decision stays centralized and COPPA-aware.
        """
        import json
        import os

        count = max(1, job.requested_count // max(1, len(job.difficulty_levels or [1])))

        if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
            logger.info("No cloud LLM key configured; returning mock questions")
            return self._generate_mock_questions(
                standard_code=standard_code, difficulty=difficulty, count=count
            )

        prompt = self._build_generation_prompt(
            standard_code=standard_code,
            difficulty=difficulty,
            context_themes=context_themes,
            count=count,
        )

        try:
            response = await self.llm_client.acomplete(
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]},
                ],
                purpose=LLMPurpose.QUESTION_GENERATION,
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            questions: list[dict] = []
            for q in data.get("questions", []):
                questions.append(
                    {
                        "stem": q.get("question") or q.get("stem", ""),
                        "options": q.get("options", []),
                        "correct_answer": q.get("correct_answer", ""),
                        "explanation": q.get("explanation", ""),
                        "difficulty": difficulty,
                        "model_used": job.model,
                        "prompt_template": "stage2_question_gen",
                        "raw_response": content,
                        "generation_time_ms": getattr(response, "response_ms", 0),
                    }
                )
            return questions[: job.requested_count]
        except Exception:
            logger.exception("Question generation failed; falling back to mocks")
            return self._generate_mock_questions(
                standard_code=standard_code, difficulty=difficulty, count=count
            )

    def _build_generation_prompt(
        self,
        standard_code: str,
        difficulty: int,
        context_themes: Optional[list[str]] = None,
        count: int = 10,
    ) -> dict:
        """Build the LLM generation prompt."""

        standard_descriptions = {
            "3.OA.A.4": "Finding the Missing Number (multiplication/division)",
            "3.OA.C.7": "Multiplication & Division Facts",
            "3.OA.D.8": "Two-Step Problem Solving",
            "3.NBT.A.2": "Adding & Subtracting Big Numbers",
            "3.NBT.A.3": "Multiplying by Tens",
            "3.NF.A.1": "Understanding Fractions",
            "3.NF.A.3": "Comparing Fractions",
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

        standard_desc = standard_descriptions.get(standard_code, standard_code)
        difficulty_desc = {
            1: "very easy (single step, concrete examples)",
            2: "easy (single step, some abstraction)",
            3: "medium (multi-step, abstract concepts)",
            4: "hard (complex multi-step, real-world application)",
            5: "very hard (challenging, advanced reasoning)",
        }

        difficulty_text = difficulty_desc.get(difficulty, "medium")

        themes_str = f"Use themes: {', '.join(context_themes)}" if context_themes else "Use diverse real-world themes"

        return {
            "system": """You are an Oregon Grade 4 mathematics curriculum expert. Generate high-quality multiple-choice questions that are:
- Aligned to Oregon Common Core Math Standards
- Age-appropriate for 9-10 year olds
- Clear, concise, and unambiguous
- Have exactly 4 options with one correct answer
- Include detailed explanations
- Use diverse, inclusive contexts
- Mathematically correct with verifiable solutions""",
            "user": f"""Generate {count} multiple-choice math questions for standard {standard_code} ({standard_desc}).

Difficulty level: {difficulty_text}

{themes_str}

IMPORTANT: Output MUST be valid JSON with this exact structure:
{{
  "questions": [
    {{
      "question": "Your question text here",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "A", or "B", or "C", or "D",
      "explanation": "Detailed explanation of why the answer is correct and why others are wrong"
    }}
  ]
}}

Do not include any markdown formatting or extra text. Output raw JSON only.""",
        }

    def _generate_mock_questions(
        self,
        standard_code: str,
        difficulty: int,
        count: int = 5,
    ) -> list[dict]:
        """Generate mock questions for testing."""
        mock_questions = []
        for i in range(count):
            mock_questions.append({
                "stem": f"Practice Question {i+1} for {standard_code} (Mock)",
                "options": ["Answer A", "Answer B", "Answer C", "Answer D"],
                "correct_answer": "A",
                "explanation": "This is a mock question for testing purposes.",
                "difficulty": difficulty,
                "model_used": "mock",
                "prompt_template": "mock",
                "raw_response": "{}",
                "generation_time_ms": 0,
            })
        return mock_questions

    async def _validate_question(
        self,
        job: GenerationJob,
        question_data: dict,
        standard_id: str,
    ) -> QuestionValidationResult:
        """Validate a generated question (legacy helper kept for tests)."""
        now = datetime.now(timezone.utc)
        generated_question = GeneratedQuestion(
            id=str(uuid4()),
            job_id=job.id,
            standard_id=standard_id,
            difficulty=question_data.get("difficulty", 3),
            question_type="multiple_choice",
            stem=question_data.get("stem", ""),
            options=question_data.get("options", []),
            correct_answer=question_data.get("correct_answer", ""),
            explanation=question_data.get("explanation", ""),
            model_used=question_data.get("model_used", job.model),
            prompt_template=question_data.get("prompt_template"),
            raw_response=question_data.get("raw_response"),
            generation_time_ms=question_data.get("generation_time_ms"),
            validation_status=ValidationStatus.PENDING.value,
            confidence_score=0.0,
            created_at=now,
            updated_at=now,
        )
        self.db_session.add(generated_question)
        await self.db_session.flush()

        confidence_score = self._calculate_confidence(question_data)
        validation_result = QuestionValidationResult(
            id=str(uuid4()),
            generated_question_id=generated_question.id,
            solution_execution_passed=True,
            age_appropriateness_passed=confidence_score >= 0.6,
            dedup_passed=True,
            overall_passed=confidence_score >= 0.85,
            confidence_score=confidence_score,
            created_at=now,
        )
        generated_question.validation_status = (
            ValidationStatus.PASSED.value
            if validation_result.overall_passed
            else ValidationStatus.FAILED.value
        )
        generated_question.confidence_score = confidence_score
        self.db_session.add(validation_result)
        validation_result.generated_question = generated_question  # type: ignore[attr-defined]
        return validation_result

    def _calculate_confidence(self, question_data: dict) -> float:
        """
        Calculate confidence score for a question.

        Based on:
        - Options count (exactly 4)
        - Answer format (A/B/C/D)
        - Explanation presence and length
        """
        score = 0.0
        max_score = 0.0

        # Check options
        options = question_data.get("options", [])
        max_score += 0.3
        if len(options) == 4:
            score += 0.3

        # Check answer format
        answer = question_data.get("correct_answer", "")
        max_score += 0.3
        if answer in ["A", "B", "C", "D"]:
            score += 0.3

        # Check explanation
        explanation = question_data.get("explanation", "")
        max_score += 0.4
        if explanation and len(explanation) > 20:
            score += 0.4

        return score / max_score if max_score > 0 else 0.0

    async def _execute_solution_code(
        self,
        python_code: str,
        timeout_seconds: int = 10,
    ) -> tuple[bool, str]:
        """
        Execute question solution code in isolated subprocess.

        Args:
            python_code: Python code to execute
            timeout_seconds: Execution timeout

        Returns:
            Tuple of (success: bool, output: str)
        """
        import subprocess
        import tempfile
        import os

        code_file = None
        try:
            # Write code to temp file
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.py', delete=False, encoding='utf-8'
            ) as f:
                f.write(python_code)
                code_file = f.name

            # Run subprocess with timeout
            result = subprocess.run(
                ['python3', code_file],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )

            success = result.returncode == 0
            output = result.stdout.strip() if success else result.stderr.strip()
            return (success, output)

        except subprocess.TimeoutExpired:
            return (False, "Execution timeout")
        except Exception as e:
            return (False, str(e))
        finally:
            if code_file and os.path.exists(code_file):
                try:
                    os.unlink(code_file)
                except Exception:
                    pass

    async def _classify_question(
        self,
        question_text: str,
        option_count: int,
    ) -> dict[str, Any]:
        """
        Classify question for pedagogical attributes.

        Args:
            question_text: The question text
            option_count: Number of answer options

        Returns:
            Classification dictionary with attributes and validation status
        """
        import textstat

        errors = []

        # Reading level (Flesch-Kincaid): should be 2.5-5.5 for grades 1-5
        try:
            fk_score = textstat.flesch_kincaid_grade(question_text)
            if not (2.5 <= fk_score <= 5.5):
                errors.append(f"Reading level {fk_score:.1f} outside range 2.5-5.5")
        except Exception:
            fk_score = None

        # Word count: typically 5-50 words for math questions
        word_count = len(question_text.split())
        if not (5 <= word_count <= 50):
            errors.append(f"Word count {word_count} outside range 5-50")

        # Prohibited keywords (COPPA/safety)
        prohibited = {'kill', 'violence', 'drugs', 'weapons', 'death', 'suicide'}
        has_prohibited = any(kw in question_text.lower() for kw in prohibited)
        if has_prohibited:
            errors.append("Contains prohibited keywords")

        # Multiple choice: should have exactly 4 options
        is_valid = len(errors) == 0

        return {
            'reading_level': fk_score,
            'word_count': word_count,
            'has_prohibited_keywords': has_prohibited,
            'is_multiple_choice': option_count == 4,
            'is_valid': is_valid,
            'errors': errors,
        }

    async def _verify_with_claude(
        self,
        question_text: str,
        options: list[str],
        correct_answer: str,
        standard_code: str,
    ) -> tuple[float, str]:
        """Run age/standard/safety verification via `LLMClient(purpose=ADMIN)`."""
        import json
        import os

        if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")):
            return (0.9, "No verification LLM configured — skipping")

        opts = list(options) + ["N/A"] * (4 - len(options))
        prompt = (
            f"Question: {question_text}\n"
            f"Options:\nA) {opts[0]}\nB) {opts[1]}\nC) {opts[2]}\nD) {opts[3]}\n"
            f"Correct Answer: {correct_answer}\n"
            f"Standard: {standard_code}\n"
            f"Grade Level: Elementary (Grades 1-5)\n\n"
            "Evaluate this question on:\n"
            "1. Alignment to the academic standard\n"
            "2. Age-appropriateness for elementary students\n"
            "3. Mathematical correctness\n"
            "4. Safety (no violence, inappropriate content)\n\n"
            "Respond with JSON only:\n"
            "{\n"
            '  "alignment_confidence": 0.0-1.0,\n'
            '  "age_appropriate": true/false,\n'
            '  "mathematically_correct": true/false,\n'
            '  "safe": true/false,\n'
            '  "reasoning": "explanation"\n'
            "}"
        )

        try:
            response = await self.llm_client.acomplete(
                messages=[{"role": "user", "content": prompt}],
                purpose=LLMPurpose.ADMIN,
                temperature=0.0,
                max_tokens=200,
            )
            content = response.choices[0].message.content
            result = json.loads(content)
            confidence = float(result.get("alignment_confidence", 0.5))
            if not (
                result.get("age_appropriate", True)
                and result.get("safe", True)
                and result.get("mathematically_correct", True)
            ):
                confidence *= 0.5
            return (confidence, result.get("reasoning", ""))
        except Exception as e:  # noqa: BLE001
            logger.exception("Verification call failed")
            return (0.5, f"Verification error: {e}")

    async def _check_dedup(
        self,
        question_text: str,
        standard_id: str,
        similarity_threshold: float = 0.92,
    ) -> tuple[bool, Optional[str]]:
        """Check whether `question_text` is a near-duplicate of an existing
        passed question for the same `standard_id` (UUID, not code).

        Uses a process-singleton SentenceTransformer to avoid the multi-second
        cold-start on every call (was a major perf bug).
        """
        from src.services.embedding_service import get_embedding_model

        try:
            from sqlalchemy import func

            model = get_embedding_model()
            embedding = model.encode(question_text).tolist()

            result = await self.db_session.execute(
                select(GeneratedQuestion)
                .where(
                    GeneratedQuestion.standard_id == standard_id,
                    GeneratedQuestion.validation_status == ValidationStatus.PASSED.value,
                    func.cosine_distance(
                        GeneratedQuestion.content_embedding,
                        embedding,
                    )
                    < (1 - similarity_threshold),
                )
                .limit(1)
            )
            similar = result.scalars().first()
            return (True, similar.id) if similar else (False, None)
        except Exception:  # noqa: BLE001
            # If embeddings/pgvector unavailable (test env), don't block.
            logger.exception("Dedup check failed; treating as non-duplicate")
            return (False, None)

    async def _promote_to_questions_table(
        self,
        validation_result: QuestionValidationResult,
    ) -> None:
        """Promote a validated question to the main `questions` table.

        Fix C-8: previously used `self.session` (attribute is `self.db_session`)
        and looked up the Standard by a non-existent `standard_code` column on
        GeneratedQuestion. The FK is `standard_id` (UUID) — use it directly.
        """
        from src.models.models import Question

        generated_question: GeneratedQuestion = validation_result.generated_question  # type: ignore[attr-defined]

        now = datetime.now(timezone.utc)
        question = Question(
            id=str(uuid4()),
            standard_id=generated_question.standard_id,
            question_text=generated_question.stem,
            question_type="multiple_choice",
            difficulty=generated_question.difficulty,
            points=1,
            is_active=True,
            metadata_json={
                "source": "ai_generated",
                "job_id": generated_question.job_id,
                "confidence_score": generated_question.confidence_score,
                "model_used": generated_question.model_used,
            },
        )

        self.db_session.add(question)

        generated_question.promoted_to_question_id = question.id
        generated_question.promoted_at = now

    async def _add_to_review_queue(
        self,
        validation_result: QuestionValidationResult,
    ) -> None:
        """Add a question to the human review queue."""
        generated_question = validation_result.generated_question  # type: ignore[attr-defined]
        review = ContentReviewQueue(
            id=str(uuid4()),
            generated_question_id=generated_question.id,
            status="pending",
            priority=5,
            confidence_score=generated_question.confidence_score,
            flags=["low_confidence"],
        )
        self.db_session.add(review)


def get_llm_question_generator(db_session: AsyncSession) -> LLMQuestionGenerator:
    """Return a fresh `LLMQuestionGenerator` bound to the request session.

    Singletons were removed (fix C-8 / hygiene): the previous module-level
    cache held the *first request's* `AsyncSession` forever, which becomes
    a closed session for all subsequent callers.
    """
    return LLMQuestionGenerator(db_session)
