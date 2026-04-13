#!/usr/bin/env python3
"""
Database seeding script for PADI.AI Stage 1.
Seeds Oregon math standards and sample questions.

Usage:
    python -m scripts.seed_data
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any

import asyncpg
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import get_settings

settings = get_settings()


def create_test_data() -> tuple[list[dict], list[dict]]:
    """Create Oregon 4th grade math standards with prerequisites."""

    # Oregon Math Standards for Grade 4 (based on common core adapted for Oregon)
    standards = [
        # Number and Operations in Base Ten
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.NBT.A.1",
            "grade_level": 4,
            "domain": "Number and Operations in Base Ten",
            "title": "Recognize place value relationships",
            "description": "Recognize that in a multi-digit whole number, a digit in one place represents ten times what it represents in the place to its right.",
        },
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.NBT.A.2",
            "grade_level": 4,
            "domain": "Number and Operations in Base Ten",
            "title": "Read and write multi-digit numbers",
            "description": "Read and write multi-digit whole numbers using base-ten numerals, number names, and expanded form. Compare two multi-digit numbers based on meanings of the digits in each place.",
        },
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.NBT.A.3",
            "grade_level": 4,
            "domain": "Number and Operations in Base Ten",
            "title": "Round multi-digit numbers",
            "description": "Use place value understanding to round multi-digit whole numbers to any place.",
        },
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.NBT.B.4",
            "grade_level": 4,
            "domain": "Number and Operations in Base Ten",
            "title": "Add and subtract multi-digit numbers",
            "description": "Fluently add and subtract multi-digit whole numbers using the standard algorithm.",
        },
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.NBT.B.5",
            "grade_level": 4,
            "domain": "Number and Operations in Base Ten",
            "title": "Multiply multi-digit numbers",
            "description": "Multiply a whole number of up to four digits by a one-digit whole number, and multiply two two-digit numbers.",
        },
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.NBT.B.6",
            "grade_level": 4,
            "domain": "Number and Operations in Base Ten",
            "title": "Divide with remainders",
            "description": "Find whole-number quotients and remainders with up to four-digit dividends and one-digit divisors.",
        },
        # Number and Operations - Fractions
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.NF.A.1",
            "grade_level": 4,
            "domain": "Number and Operations - Fractions",
            "title": "Explain fraction equivalence",
            "description": "Explain why a fraction a/b is equivalent to a fraction (n × a)/(n × b) by using visual fraction models.",
        },
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.NF.A.2",
            "grade_level": 4,
            "domain": "Number and Operations - Fractions",
            "title": "Compare fractions",
            "description": "Compare two fractions with different numerators and different denominators.",
        },
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.NF.B.3",
            "grade_level": 4,
            "domain": "Number and Operations - Fractions",
            "title": "Build fractions from unit fractions",
            "description": "Understand a fraction a/b with a > 1 as a sum of fractions 1/b.",
        },
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.NF.B.4",
            "grade_level": 4,
            "domain": "Number and Operations - Fractions",
            "title": "Apply multiplication to fractions",
            "description": "Apply and extend previous understandings of multiplication to multiply a fraction by a whole number.",
        },
        # Measurement and Data
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.MD.A.1",
            "grade_level": 4,
            "domain": "Measurement and Data",
            "title": "Know relative sizes of measurement units",
            "description": "Know the relative sizes of measurement units within one system of units including km, m, cm; kg, g; lb, oz; l, ml; h, min, s.",
        },
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.MD.A.2",
            "grade_level": 4,
            "domain": "Measurement and Data",
            "title": "Use the four operations to solve word problems",
            "description": "Use the four operations with whole numbers to solve problems involving distances, intervals of time, liquid volumes, masses of objects, and money.",
        },
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.MD.B.4",
            "grade_level": 4,
            "domain": "Measurement and Data",
            "title": "Make line plots",
            "description": "Make a line plot to display a data set of measurements in fractions of a unit.",
        },
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.MD.C.5",
            "grade_level": 4,
            "domain": "Measurement and Data",
            "title": "Recognize angle concepts",
            "description": "Recognize angles as geometric shapes that are formed wherever two rays share a common endpoint.",
        },
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.MD.C.6",
            "grade_level": 4,
            "domain": "Measurement and Data",
            "title": "Measure angles",
            "description": "Measure angles in whole-number degrees using a protractor. Sketch angles of specified measure.",
        },
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.MD.C.7",
            "grade_level": 4,
            "domain": "Measurement and Data",
            "title": "Recognize angle measure as additive",
            "description": "Recognize angle measure as additive. When an angle is decomposed into non-overlapping angles, the measure of the whole angle is the sum of the measures of the parts.",
        },
        # Geometry
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.G.A.1",
            "grade_level": 4,
            "domain": "Geometry",
            "title": "Draw and identify lines and angles",
            "description": "Draw points, lines, line segments, rays, angles (right, acute, obtuse), and perpendicular and parallel lines.",
        },
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.G.A.2",
            "grade_level": 4,
            "domain": "Geometry",
            "title": "Classify two-dimensional figures",
            "description": "Classify two-dimensional figures based on the presence or absence of parallel or perpendicular lines, or the presence or absence of angles of a specified size.",
        },
        {
            "id": str(uuid.uuid4()),
            "standard_code": "OR.Math.4.G.A.3",
            "grade_level": 4,
            "domain": "Geometry",
            "title": "Recognize symmetry",
            "description": "Recognize a line of symmetry for a two-dimensional figure as a line across the figure such that the figure can be folded along the line into matching parts.",
        },
    ]

    # Sample questions for each standard
    questions = [
        # NBT.A.1 - Place value
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000001",
            "question_text": "In the number 54,321, what is the value of the digit 4?",
            "question_type": "multiple_choice",
            "difficulty": 2,
            "points": 1,
        },
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000001",
            "question_text": "Which number has a 7 in the hundreds place?",
            "question_type": "multiple_choice",
            "difficulty": 2,
            "points": 1,
        },
        # NBT.A.2 - Read/write numbers
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000002",
            "question_text": "Write 45,678 in expanded form.",
            "question_type": "numeric",
            "difficulty": 2,
            "points": 2,
        },
        # NBT.A.3 - Rounding
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000003",
            "question_text": "Round 3,456 to the nearest hundred.",
            "question_type": "numeric",
            "difficulty": 2,
            "points": 1,
        },
        # NBT.B.4 - Add/subtract
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000004",
            "question_text": "Calculate: 4,567 + 2,389",
            "question_type": "numeric",
            "difficulty": 3,
            "points": 2,
        },
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000004",
            "question_text": "Calculate: 8,432 - 3,567",
            "question_type": "numeric",
            "difficulty": 3,
            "points": 2,
        },
        # NBT.B.5 - Multiply
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000005",
            "question_text": "Calculate: 234 × 5",
            "question_type": "numeric",
            "difficulty": 3,
            "points": 2,
        },
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000005",
            "question_text": "Calculate: 45 × 23",
            "question_type": "numeric",
            "difficulty": 4,
            "points": 3,
        },
        # NBT.B.6 - Divide
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000006",
            "question_text": "Calculate: 456 ÷ 4",
            "question_type": "numeric",
            "difficulty": 3,
            "points": 2,
        },
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000006",
            "question_text": "What is the remainder when 127 is divided by 5?",
            "question_type": "numeric",
            "difficulty": 3,
            "points": 2,
        },
        # NF.A.1 - Fraction equivalence
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000007",
            "question_text": "Which fraction is equivalent to 2/3?",
            "question_type": "multiple_choice",
            "difficulty": 2,
            "points": 1,
        },
        # NF.A.2 - Compare fractions
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000008",
            "question_text": "Which is larger: 3/4 or 2/3?",
            "question_type": "multiple_choice",
            "difficulty": 3,
            "points": 2,
        },
        # MD.A.1 - Measurement units
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000011",
            "question_text": "How many centimeters are in 1 meter?",
            "question_type": "numeric",
            "difficulty": 1,
            "points": 1,
        },
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000011",
            "question_text": "Convert 2.5 kilometers to meters.",
            "question_type": "numeric",
            "difficulty": 2,
            "points": 2,
        },
        # MD.A.2 - Word problems
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000012",
            "question_text": "Sarah has 3 liters of juice. She drinks 750 milliliters. How much juice is left?",
            "question_type": "numeric",
            "difficulty": 3,
            "points": 3,
        },
        # MD.C.6 - Measure angles
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000015",
            "question_text": "What tool do you use to measure angles?",
            "question_type": "multiple_choice",
            "difficulty": 1,
            "points": 1,
        },
        # G.A.1 - Lines and angles
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000017",
            "question_text": "What do you call an angle that measures exactly 90 degrees?",
            "question_type": "multiple_choice",
            "difficulty": 1,
            "points": 1,
        },
        # G.A.2 - Classify figures
        {
            "id": str(uuid.uuid4()),
            "standard_id": "00000000-0000-0000-0000-000000000018",
            "question_text": "How many pairs of parallel sides does a rectangle have?",
            "question_type": "numeric",
            "difficulty": 2,
            "points": 1,
        },
    ]

    return standards, questions


async def seed_database() -> None:
    """Seed the database with Oregon standards and sample questions."""

    print(f"Connecting to database at {settings.DATABASE_URL}")

    # Create engine and session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as db:
        # Get all standards
        from src.models.base import Base
        from sqlalchemy import text

        # Insert standards
        print("Inserting standards...")
        for standard in settings.STANDARDS:
            db.execute(
                text("""
                    INSERT INTO standards (id, standard_code, grade_level, domain, title, description)
                    VALUES (:id, :code, :grade, :domain, :title, :desc)
                    ON CONFLICT (standard_code, grade_level) DO NOTHING
                """),
                {
                    "id": standard["id"],
                    "code": standard["standard_code"],
                    "grade": standard["grade_level"],
                    "domain": standard["domain"],
                    "title": standard["title"],
                    "desc": standard["description"],
                },
            )

        # Insert questions
        print("Inserting questions...")
        for question in settings.QUESTIONS:
            db.execute(
                text("""
                    INSERT INTO questions (id, standard_id, question_text, question_type, difficulty, points)
                    VALUES (:id, :std, :text, :type, :diff, :pts)
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": question["id"],
                    "std": question["standard_id"],
                    "text": question["question_text"],
                    "type": question["question_type"],
                    "diff": question["difficulty"],
                    "pts": question["points"],
                },
            )

        db.commit()
        print(f"Successfully seeded {len(settings.STANDARDS)} standards and {len(settings.QUESTIONS)} questions")


def main() -> None:
    """Main entry point."""
    asyncio.run(seed_database())


if __name__ == "__main__":
    main()
