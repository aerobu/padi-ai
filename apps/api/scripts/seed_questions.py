"""
Seed the question bank with Grade 4 math questions.
Minimum: 4 questions per Oregon standard.
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import select

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.models.models import Standard, Question, QuestionOption
from src.core.config import get_settings
from src.models import models


settings = get_settings()

# Sample questions for Grade 4 math standards
# These are minimal examples - production should have 100+ questions per standard
SAMPLE_QUESTIONS = [
    # 4.NBT.A.1 - Place Value
    {
        "standard_code": "4.NBT.A.1",
        "difficulty": 2,
        "question_type": "multiple_choice",
        "stem": "In the number 7,777, what is the value of the 7 in the hundreds place?",
        "options": [
            {"key": "A", "text": "100"},
            {"key": "B", "text": "700"},
            {"key": "C", "text": "1,000"},
            {"key": "D", "text": "7,000"},
        ],
        "correct_answer": "B",
        "explanation": "The 7 in the hundreds place has a value of 700.",
    },
    {
        "standard_code": "4.NBT.A.1",
        "difficulty": 3,
        "question_type": "multiple_choice",
        "stem": "Which number has a 5 in the tens place and a 5 in the thousands place?",
        "options": [
            {"key": "A", "text": "5,500"},
            {"key": "B", "text": "5,050"},
            {"key": "C", "text": "5,050"},
            {"key": "D", "text": "5,555"},
        ],
        "correct_answer": "A",
        "explanation": "5,500 has a 5 in the thousands place and a 5 in the hundreds place.",
    },
    {
        "standard_code": "4.NBT.A.1",
        "difficulty": 2,
        "question_type": "multiple_choice",
        "stem": "What is 10 times as much as 300?",
        "options": [
            {"key": "A", "text": "300"},
            {"key": "B", "text": "3,000"},
            {"key": "C", "text": "30,000"},
            {"key": "D", "text": "30"},
        ],
        "correct_answer": "B",
        "explanation": "10 times 300 is 3,000.",
    },
    {
        "standard_code": "4.NBT.A.1",
        "difficulty": 4,
        "question_type": "multiple_choice",
        "stem": "The digit 6 is in which place in the number 16,450?",
        "options": [
            {"key": "A", "text": "Thousands"},
            {"key": "B", "text": "Ten thousands"},
            {"key": "C", "text": "Hundreds"},
            {"key": "D", "text": "Tens"},
        ],
        "correct_answer": "A",
        "explanation": "In 16,450, the digit 6 is in the thousands place.",
    },
    # 4.NBT.A.2 - Read and Write Numbers
    {
        "standard_code": "4.NBT.A.2",
        "difficulty": 2,
        "question_type": "multiple_choice",
        "stem": "Which is the standard form of four hundred twenty-three?",
        "options": [
            {"key": "A", "text": "400 + 20 + 3"},
            {"key": "B", "text": "423"},
            {"key": "C", "text": "4,230"},
            {"key": "D", "text": "4023"},
        ],
        "correct_answer": "B",
        "explanation": "The standard form of four hundred twenty-three is 423.",
    },
    {
        "standard_code": "4.NBT.A.2",
        "difficulty": 3,
        "question_type": "multiple_choice",
        "stem": "Which number is greater: 4,567 or 4,576?",
        "options": [
            {"key": "A", "text": "4,567"},
            {"key": "B", "text": "4,576"},
            {"key": "C", "text": "They are equal"},
            {"key": "D", "text": "Cannot be determined"},
        ],
        "correct_answer": "B",
        "explanation": "4,576 is greater because 76 > 67 in the tens and ones places.",
    },
    {
        "standard_code": "4.NBT.A.2",
        "difficulty": 2,
        "question_type": "multiple_choice",
        "stem": "What is the expanded form of 8,205?",
        "options": [
            {"key": "A", "text": "8,000 + 20 + 5"},
            {"key": "B", "text": "8,000 + 200 + 5"},
            {"key": "C", "text": "800 + 20 + 5"},
            {"key": "D", "text": "8,000 + 2 + 5"},
        ],
        "correct_answer": "A",
        "explanation": "8,205 in expanded form is 8,000 + 20 + 5.",
    },
    {
        "standard_code": "4.NBT.A.2",
        "difficulty": 3,
        "question_type": "multiple_choice",
        "stem": "Which symbol makes this true: 3,456 ___ 3,465?",
        "options": [
            {"key": "A", "text": ">"},
            {"key": "B", "text": "<"},
            {"key": "C", "text": "="},
            {"key": "D", "text": "None of the above"},
        ],
        "correct_answer": "B",
        "explanation": "3,456 < 3,465 because 56 < 65.",
    },
    # 4.NBT.A.3 - Rounding
    {
        "standard_code": "4.NBT.A.3",
        "difficulty": 2,
        "question_type": "multiple_choice",
        "stem": "Round 456 to the nearest hundred.",
        "options": [
            {"key": "A", "text": "400"},
            {"key": "B", "text": "450"},
            {"key": "C", "text": "500"},
            {"key": "D", "text": "600"},
        ],
        "correct_answer": "C",
        "explanation": "456 rounds to 500 because the tens digit (5) is 5 or greater.",
    },
    {
        "standard_code": "4.NBT.A.3",
        "difficulty": 3,
        "question_type": "multiple_choice",
        "stem": "Round 2,847 to the nearest thousand.",
        "options": [
            {"key": "A", "text": "2,000"},
            {"key": "B", "text": "2,500"},
            {"key": "C", "text": "3,000"},
            {"key": "D", "text": "2,800"},
        ],
        "correct_answer": "C",
        "explanation": "2,847 rounds to 3,000 because the hundreds digit (8) is 5 or greater.",
    },
    # 4.OA.A.1 - Multiplication and Division Word Problems
    {
        "standard_code": "4.OA.A.1",
        "difficulty": 2,
        "question_type": "multiple_choice",
        "stem": "What is 3 × 4?",
        "options": [
            {"key": "A", "text": "7"},
            {"key": "B", "text": "12"},
            {"key": "C", "text": "34"},
            {"key": "D", "text": "43"},
        ],
        "correct_answer": "B",
        "explanation": "3 × 4 = 12",
    },
    {
        "standard_code": "4.OA.A.1",
        "difficulty": 3,
        "question_type": "multiple_choice",
        "stem": "A box holds 6 apples. How many apples are in 8 boxes?",
        "options": [
            {"key": "A", "text": "14"},
            {"key": "B", "text": "42"},
            {"key": "C", "text": "48"},
            {"key": "D", "text": "54"},
        ],
        "correct_answer": "C",
        "explanation": "6 × 8 = 48 apples.",
    },
    {
        "standard_code": "4.OA.A.1",
        "difficulty": 3,
        "question_type": "multiple_choice",
        "stem": "48 students are divided equally into 6 groups. How many students are in each group?",
        "options": [
            {"key": "A", "text": "6"},
            {"key": "B", "text": "7"},
            {"key": "C", "text": "8"},
            {"key": "D", "text": "9"},
        ],
        "correct_answer": "C",
        "explanation": "48 ÷ 6 = 8 students per group.",
    },
    {
        "standard_code": "4.OA.A.1",
        "difficulty": 4,
        "question_type": "multiple_choice",
        "stem": "Which equation represents: '7 times as many as 9'? ",
        "options": [
            {"key": "A", "text": "7 + 9 = ?"},
            {"key": "B", "text": "7 × 9 = ?"},
            {"key": "C", "text": "9 - 7 = ?"},
            {"key": "D", "text": "9 ÷ 7 = ?"},
        ],
        "correct_answer": "B",
        "explanation": "'Times as many' means multiplication: 7 × 9.",
    },
    # 4.OA.A.2 - Multiplicative Comparison
    {
        "standard_code": "4.OA.A.2",
        "difficulty": 3,
        "question_type": "multiple_choice",
        "stem": "The blue ribbon is 6 inches long. The red ribbon is 3 times as long. How long is the red ribbon?",
        "options": [
            {"key": "A", "text": "9 inches"},
            {"key": "B", "text": "12 inches"},
            {"key": "C", "text": "15 inches"},
            {"key": "D", "text": "18 inches"},
        ],
        "correct_answer": "D",
        "explanation": "3 times 6 inches is 18 inches (3 × 6 = 18).",
    },
    # 4.OA.B.4 - Factors and Multiples
    {
        "standard_code": "4.OA.B.4",
        "difficulty": 2,
        "question_type": "multiple_choice",
        "stem": "Which number is a factor of 12?",
        "options": [
            {"key": "A", "text": "3"},
            {"key": "B", "text": "5"},
            {"key": "C", "text": "7"},
            {"key": "D", "text": "10"},
        ],
        "correct_answer": "A",
        "explanation": "12 ÷ 3 = 4, so 3 is a factor of 12.",
    },
    {
        "standard_code": "4.OA.B.4",
        "difficulty": 3,
        "question_type": "multiple_choice",
        "stem": "Which number is a multiple of 7?",
        "options": [
            {"key": "A", "text": "12"},
            {"key": "B", "text": "14"},
            {"key": "C", "text": "18"},
            {"key": "D", "text": "20"},
        ],
        "correct_answer": "B",
        "explanation": "7 × 2 = 14, so 14 is a multiple of 7.",
    },
    {
        "standard_code": "4.OA.B.4",
        "difficulty": 4,
        "question_type": "multiple_choice",
        "stem": "How many factors does the number 10 have?",
        "options": [
            {"key": "A", "text": "2"},
            {"key": "B", "text": "3"},
            {"key": "C", "text": "4"},
            {"key": "D", "text": "5"},
        ],
        "correct_answer": "C",
        "explanation": "10 has 4 factors: 1, 2, 5, and 10.",
    },
]


async def seed():
    """Seed the question bank."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession)

    async with async_session_maker() as session:
        # First, get all Grade 4 standards
        result = await session.execute(
            select(models.Standard).where(models.Standard.grade_level == 4)
        )
        standards = result.scalars().all()
        standard_codes = [s.standard_code for s in standards]

        print(f"Found {len(standards)} Grade 4 standards")
        print(f"Standard codes: {standard_codes}")

        questions_created = 0
        questions_skipped = 0

        for q in SAMPLE_QUESTIONS:
            # Only seed questions for actual standards
            if q["standard_code"] not in standard_codes:
                print(f"Skipping {q['standard_code']} - not in Grade 4 standards")
                questions_skipped += 1
                continue

            # Check if question exists
            existing = await session.execute(
                select(Question).where(Question.stem == q["stem"])
            )
            if existing.scalar_one_or_none():
                print(f"Question already exists: {q['stem'][:50]}...")
                questions_skipped += 1
                continue

            # Create question
            question = Question(
                standard_id=q["standard_code"],
                question_text=q["stem"],
                question_type=q["question_type"],
                difficulty=q["difficulty"],
                points=1,
                is_active=True,
                metadata_json={
                    "correct_answer": q["correct_answer"],
                    "explanation": q["explanation"],
                },
            )
            session.add(question)
            await session.flush()  # Get the ID

            # Add options
            for opt in q["options"]:
                session.add(QuestionOption(
                    question_id=question.id,
                    option_text=opt["text"],
                    is_correct=(opt["key"] == q["correct_answer"]),
                    order=ord(opt["key"]) - ord("A"),
                    explanation=q["explanation"] if opt["is_correct"] else None,
                ))

            questions_created += 1

        await session.commit()

    print(f"✓ Seeded {questions_created} questions")
    print(f"✓ Skipped {questions_skipped} duplicate/invalid questions")

    # Query to verify
    async with async_session_maker() as session:
        result = await session.execute(select(Question))
        all_questions = result.scalars().all()
        print(f"✓ Total questions in database: {len(all_questions)}")


if __name__ == "__main__":
    asyncio.run(seed())