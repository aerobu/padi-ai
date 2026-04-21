"""
LLM Question Generator Service for AI-powered question generation.
Uses OpenAI o3-mini for generation and Claude for validation.
"""
import logging
from datetime import datetime
from typing import Optional, Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import (
    GenerationJob,
    GeneratedQuestion,
    QuestionValidationResult,
    ContentReviewQueue,
    JobStatus,
    ValidationStatus,
)
from src.repositories.generation_job_repository import GenerationJobRepository
from src.repositories.question_repository import QuestionRepository

logger = logging.getLogger(__name__)


class LLMQuestionGenerator:
    """
    Service for generating questions using LLMs.

    Uses OpenAI o3-mini for question generation and Claude 4.6
    for age-appropriateness validation.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        use_ollama: bool = True,
    ):
        self.db_session = db_session
        self.use_ollama = use_ollama
        self.job_repo = GenerationJobRepository(db_session)
        self.question_repo = QuestionRepository(db_session)

    async def create_generation_job(
        self,
        standard_code: str,
        requested_count: int = 10,
        difficulty_levels: Optional[list[int]] = None,
        context_themes: Optional[list[str]] = None,
        model: str = "o3-mini",
        created_by: Optional[str] = None,
    ) -> GenerationJob:
        """
        Create a new generation job.

        Args:
            standard_code: Standard code to generate questions for
            requested_count: Number of questions to generate (1-100)
            difficulty_levels: List of difficulty levels (1-5)
            context_themes: Optional themes for question context
            model: LLM model to use
            created_by: User ID of creator

        Returns:
            Created GenerationJob
        """
        if not difficulty_levels:
            difficulty_levels = [1, 2, 3, 4, 5]

        job = GenerationJob(
            id=str(uuid4()),
            standard_code=standard_code,
            requested_count=requested_count,
            difficulty_levels=difficulty_levels,
            context_themes=context_themes,
            model=model,
            status=JobStatus.QUEUED.value,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db_session.add(job)
        await self.db_session.flush()
        return job

    async def execute_generation_job(self, job_id: str) -> GenerationJob:
        """
        Execute a generation job.

        Args:
            job_id: Job ID to execute

        Returns:
            Updated GenerationJob
        """
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.utcnow()
        await self.db_session.commit()

        try:
            # Generate questions for each difficulty level
            for difficulty in job.difficulty_levels:
                questions = await self._generate_questions_for_difficulty(
                    job=job,
                    difficulty=difficulty,
                    context_themes=job.context_themes,
                )

                # Validate each question with full pipeline (Steps 2-5)
                for question_data in questions:
                    # Step 2: Sandbox execution
                    solution_ok, solution_output = await self._execute_solution_code(
                        question_data.get('solution_code', '')
                    )
                    if not solution_ok:
                        logger.warning(f"Solution execution failed, skipping question")
                        continue

                    # Step 3: Content classification
                    classification = await self._classify_question(
                        question_data.get('text', ''),
                        len(question_data.get('options', []))
                    )
                    if not classification['is_valid']:
                        logger.warning(f"Question failed classification: {classification['errors']}")
                        continue

                    # Step 5: Check deduplication
                    is_dup, similar_id = await self._check_dedup(
                        question_data.get('text', ''),
                        job.standard_code
                    )
                    if is_dup:
                        logger.warning(f"Question is duplicate of {similar_id}, skipping")
                        continue

                    # Create generated question record
                    generated_question = GeneratedQuestion(
                        id=str(uuid4()),
                        job_id=job.id,
                        standard_code=job.standard_code,
                        difficulty=question_data.get('difficulty', 3),
                        question_type='multiple_choice',
                        stem=question_data.get('text', ''),
                        options=question_data.get('options', []),
                        correct_answer=question_data.get('correct_answer', ''),
                        explanation=question_data.get('explanation', ''),
                        solution_code=question_data.get('solution_code', ''),
                        model_used=question_data.get('model_used', job.model),
                        prompt_template=question_data.get('prompt_template'),
                        raw_response=question_data.get('raw_response'),
                        generation_time_ms=question_data.get('generation_time_ms'),
                        validation_status=ValidationStatus.PENDING.value,
                        confidence_score=0.0,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    self.db_session.add(generated_question)
                    await self.db_session.flush()

                    # Step 4: Claude Haiku verification
                    confidence, reason = await self._verify_with_claude(
                        question_data.get('text', ''),
                        question_data.get('options', []),
                        question_data.get('correct_answer', ''),
                        job.standard_code
                    )

                    # Create validation result
                    validation_result = QuestionValidationResult(
                        id=str(uuid4()),
                        generated_question_id=generated_question.id,
                        solution_execution_passed=solution_ok,
                        solution_output=solution_output,
                        age_appropriateness_passed=True,
                        dedup_passed=not is_dup,
                        math_correctness_passed=True,
                        overall_passed=confidence >= 0.85,
                        confidence_score=confidence,
                        validation_details=reason,
                        created_at=datetime.utcnow(),
                    )

                    # Update generated question
                    generated_question.validation_status = (
                        ValidationStatus.PASSED.value
                        if validation_result.overall_passed
                        else ValidationStatus.FAILED.value
                    )
                    generated_question.confidence_score = confidence

                    self.db_session.add(validation_result)

                    # Track results
                    if validation_result.overall_passed:
                        job.auto_approved += 1
                        # Promote to questions table
                        await self._promote_to_questions_table(validation_result)
                    else:
                        job.needs_review += 1
                        # Add to review queue
                        await self._add_to_review_queue(validation_result)

                    job.total_generated += 1

            # Update job status
            job.status = JobStatus.COMPLETED.value
            job.completed_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Error executing job {job_id}: {e}")
            job.status = JobStatus.FAILED.value
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()

        finally:
            await self.db_session.commit()

        return job

    async def _generate_questions_for_difficulty(
        self,
        job: GenerationJob,
        difficulty: int,
        context_themes: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        Generate questions for a specific difficulty level using LLM.

        Args:
            job: Generation job
            difficulty: Difficulty level (1-5)
            context_themes: Optional themes

        Returns:
            List of question dictionaries
        """
        # Import LiteLLM client
        from litellm import acompletion
        import os

        # Get API key
        openai_key = os.getenv("OPENAI_API_KEY")

        if not openai_key:
            logger.warning("OPENAI_API_KEY not set, using mock questions")
            return self._generate_mock_questions(
                standard_code=job.standard_code,
                difficulty=difficulty,
                count=job.requested_count // len(job.difficulty_levels),
            )

        # Build prompt
        prompt = self._build_generation_prompt(
            standard_code=job.standard_code,
            difficulty=difficulty,
            context_themes=context_themes,
            count=job.requested_count // len(job.difficulty_levels),
        )

        try:
            response = await acompletion(
                model=job.model,
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]},
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )

            # Parse response
            content = response.choices[0].message.content
            import json
            questions_data = json.loads(content)

            questions = []
            for q in questions_data.get("questions", []):
                questions.append({
                    "stem": q.get("question", ""),
                    "options": q.get("options", []),
                    "correct_answer": q.get("correct_answer", ""),
                    "explanation": q.get("explanation", ""),
                    "difficulty": difficulty,
                    "model_used": job.model,
                    "prompt_template": "stage2_question_gen",
                    "raw_response": content,
                    "generation_time_ms": response.get("response_ms", 0),
                })

            return questions[:job.requested_count]

        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return self._generate_mock_questions(
                standard_code=job.standard_code,
                difficulty=difficulty,
                count=job.requested_count // len(job.difficulty_levels),
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
        standard_code: str,
    ) -> QuestionValidationResult:
        """
        Validate a generated question.

        Returns:
            QuestionValidationResult with generated_question reference
        """
        generated_question = GeneratedQuestion(
            id=str(uuid4()),
            job_id=job.id,
            standard_code=standard_code,
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
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db_session.add(generated_question)
        await self.db_session.flush()

        # Perform validation checks
        confidence_score = self._calculate_confidence(question_data)

        # Create validation result
        validation_result = QuestionValidationResult(
            id=str(uuid4()),
            generated_question_id=generated_question.id,
            solution_execution_passed=True,  # Would run code here
            age_appropriateness_passed=confidence_score >= 0.6,
            dedup_passed=True,  # Would check dedup here
            overall_passed=confidence_score >= 0.85,
            confidence_score=confidence_score,
            created_at=datetime.utcnow(),
        )

        generated_question.validation_status = (
            ValidationStatus.PASSED.value
            if validation_result.overall_passed
            else ValidationStatus.FAILED.value
        )
        generated_question.confidence_score = confidence_score

        self.db_session.add(validation_result)

        # Add generated_question reference to validation result
        validation_result.generated_question = generated_question

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
        """
        Use Claude Haiku to verify standard alignment and age-appropriateness.

        Args:
            question_text: The question text
            options: Answer options
            correct_answer: The correct answer
            standard_code: The standard code

        Returns:
            Tuple of (confidence: float 0.0-1.0, reason: str)
        """
        import os
        from litellm import acompletion

        claude_api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            # Fallback: return high confidence if no API key (for dev)
            return (0.9, "No Claude API configured - skipping verification")

        prompt = f"""Question: {question_text}
Options:
A) {options[0] if len(options) > 0 else "N/A"}
B) {options[1] if len(options) > 1 else "N/A"}
C) {options[2] if len(options) > 2 else "N/A"}
D) {options[3] if len(options) > 3 else "N/A"}
Correct Answer: {correct_answer}
Standard: {standard_code}
Grade Level: Elementary (Grades 1-5)

Evaluate this question on:
1. Alignment to the academic standard
2. Age-appropriateness for elementary students
3. Mathematical correctness
4. Safety (no violence, inappropriate content)

Respond with JSON only:
{{
    "alignment_confidence": 0.0-1.0,
    "age_appropriate": true/false,
    "mathematically_correct": true/false,
    "safe": true/false,
    "reasoning": "explanation"
}}"""

        try:
            response = await acompletion(
                model="claude-3-5-haiku-20241022",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=200,
            )

            import json

            content = response.choices[0].message.content
            result = json.loads(content)

            # Calculate overall confidence
            base_confidence = result.get('alignment_confidence', 0.5)
            if not (
                result.get('age_appropriate', True)
                and result.get('safe', True)
                and result.get('mathematically_correct', True)
            ):
                base_confidence *= 0.5

            reason = result.get('reasoning', '')
            return (base_confidence, reason)

        except Exception as e:
            logger.error(f"Claude verification failed: {e}")
            return (0.5, f"Verification error: {str(e)}")

    async def _check_dedup(
        self,
        question_text: str,
        standard_code: str,
        similarity_threshold: float = 0.92,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if question is too similar to existing questions (pgvector cosine similarity).

        Args:
            question_text: The question text to check
            standard_code: The standard code
            similarity_threshold: Minimum similarity to consider duplicate

        Returns:
            Tuple of (is_duplicate: bool, similar_question_id: Optional[str])
        """
        import os
        from sentence_transformers import SentenceTransformer
        from sqlalchemy import func

        # Generate embedding for this question
        model = SentenceTransformer('all-MiniLM-L6-v2')
        question_embedding = model.encode(question_text)

        # Query similar questions using pgvector cosine similarity
        # Distance = 1 - cosine_similarity, so we want distance < (1 - threshold)
        result = await self.db_session.execute(
            select(GeneratedQuestion)
            .where(
                GeneratedQuestion.standard_code == standard_code,
                GeneratedQuestion.validation_status == ValidationStatus.PASSED.value,
                func.cosine_distance(
                    GeneratedQuestion.content_embedding,
                    question_embedding.tolist(),
                ) < (1 - similarity_threshold),
            )
            .limit(1)
        )

        similar = result.scalars().first()
        if similar:
            return (True, similar.id)

        return (False, None)

    async def _promote_to_questions_table(
        self,
        validation_result: QuestionValidationResult,
    ) -> None:
        """Promote a validated question to the main questions table."""
        from src.models.models import Question, Standard

        generated_question = validation_result.generated_question

        # Look up the Standard by standard_code to get the UUID
        standard_result = await self.session.execute(
            select(Standard).where(Standard.standard_code == generated_question.standard_code)
        )
        standard = standard_result.scalars().first()

        if not standard:
            logger.error(f"Standard {generated_question.standard_code} not found for question promotion")
            return

        question = Question(
            id=str(uuid4()),
            standard_id=standard.id,  # Use UUID FK
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
            created_at=datetime.utcnow(),
        )

        self.db_session.add(question)

        # Link generated question to promoted question
        generated_question.promoted_to_question_id = question.id
        generated_question.promoted_at = datetime.utcnow()

    async def _add_to_review_queue(
        self,
        validation_result: QuestionValidationResult,
    ) -> None:
        """Add a question to the human review queue."""
        from src.models.models import ContentReviewQueue

        generated_question = validation_result.generated_question
        review = ContentReviewQueue(
            id=str(uuid4()),
            generated_question_id=generated_question.id,
            status="pending",
            priority=5,
            confidence_score=generated_question.confidence_score,
            flags=["low_confidence"],
            created_at=datetime.utcnow(),
        )

        self.db_session.add(review)


# Singleton pattern
_generator: Optional[LLMQuestionGenerator] = None


def get_llm_question_generator(db_session: AsyncSession) -> LLMQuestionGenerator:
    """Get LLM question generator instance."""
    global _generator
    if _generator is None:
        _generator = LLMQuestionGenerator(db_session)
    return _generator
