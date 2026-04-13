#!/usr/bin/env python3
"""
Seed Oregon math standards and sample questions for Grade 4.
Run this after creating the database:
    python -m scripts.seed_oregon_standards
"""

import sys
import uuid
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import asyncpg
from sqlalchemy import create_engine, text

# Oregon 4th grade math standards
OREGON_STANDARDS = [
    {
        "standard_code": "OR.Math.4.NBT.A.1",
        "grade_level": 4,
        "domain": "Number and Operations in Base Ten",
        "title": "Recognize place value relationships",
        "description": "Recognize that in a multi-digit whole number, a digit in one place represents ten times what it represents in the place to its right.",
    },
    {
        "standard_code": "OR.Math.4.NBT.A.2",
        "grade_level": 4,
        "domain": "Number and Operations in Base Ten",
        "title": "Read and write multi-digit numbers",
        "description": "Read and write multi-digit whole numbers using base-ten numerals, number names, and expanded form.",
    },
    {
        "standard_code": "OR.Math.4.NBT.A.3",
        "grade_level": 4,
        "domain": "Number and Operations in Base Ten",
        "title": "Round multi-digit numbers",
        "description": "Use place value understanding to round multi-digit whole numbers to any place.",
    },
    {
        "standard_code": "OR.Math.4.NBT.B.4",
        "grade_level": 4,
        "domain": "Number and Operations in Base Ten",
        "title": "Add and subtract multi-digit numbers",
        "description": "Fluently add and subtract multi-digit whole numbers using the standard algorithm.",
    },
    {
        "standard_code": "OR.Math.4.NBT.B.5",
        "grade_level": 4,
        "domain": "Number and Operations in Base Ten",
        "title": "Multiply multi-digit numbers",
        "description": "Multiply a whole number of up to four digits by a one-digit whole number, and multiply two two-digit numbers.",
    },
    {
        "standard_code": "OR.Math.4.NBT.B.6",
        "grade_level": 4,
        "domain": "Number and Operations in Base Ten",
        "title": "Divide with remainders",
        "description": "Find whole-number quotients and remainders with up to four-digit dividends and one-digit divisors.",
    },
    {
        "standard_code": "OR.Math.4.NF.A.1",
        "grade_level": 4,
        "domain": "Number and Operations - Fractions",
        "title": "Explain fraction equivalence",
        "description": "Explain why a fraction a/b is equivalent to a fraction (n × a)/(n × b) using visual fraction models.",
    },
    {
        "standard_code": "OR.Math.4.NF.A.2",
        "grade_level": 4,
        "domain": "Number and Operations - Fractions",
        "title": "Compare fractions",
        "description": "Compare two fractions with different numerators and different denominators.",
    },
    {
        "standard_code": "OR.Math.4.NF.B.3",
        "grade_level": 4,
        "domain": "Number and Operations - Fractions",
        "title": "Build fractions from unit fractions",
        "description": "Understand a fraction a/b with a > 1 as a sum of fractions 1/b.",
    },
    {
        "standard_code": "OR.Math.4.NF.B.4",
        "grade_level": 4,
        "domain": "Number and Operations - Fractions",
        "title": "Apply multiplication to fractions",
        "description": "Apply and extend previous understandings of multiplication to multiply a fraction by a whole number.",
    },
    {
        "standard_code": "OR.Math.4.MD.A.1",
        "grade_level": 4,
        "domain": "Measurement and Data",
        "title": "Know relative sizes of measurement units",
        "description": "Know the relative sizes of measurement units within one system of units including km, m, cm; kg, g; l, ml.",
    },
    {
        "standard_code": "OR.Math.4.MD.A.2",
        "grade_level": 4,
        "domain": "Measurement and Data",
        "title": "Solve word problems with measurements",
        "description": "Use the four operations with whole numbers to solve problems involving distances, time, volumes, masses, and money.",
    },
    {
        "standard_code": "OR.Math.4.MD.B.4",
        "grade_level": 4,
        "domain": "Measurement and Data",
        "title": "Make line plots",
        "description": "Make a line plot to display a data set of measurements in fractions of a unit.",
    },
    {
        "standard_code": "OR.Math.4.MD.C.5",
        "grade_level": 4,
        "domain": "Measurement and Data",
        "title": "Recognize angle concepts",
        "description": "Recognize angles as geometric shapes formed by two rays sharing a common endpoint.",
    },
    {
        "standard_code": "OR.Math.4.MD.C.6",
        "grade_level": 4,
        "domain": "Measurement and Data",
        "title": "Measure angles",
        "description": "Measure angles in whole-number degrees using a protractor. Sketch angles of specified measure.",
    },
    {
        "standard_code": "OR.Math.4.MD.C.7",
        "grade_level": 4,
        "domain": "Measurement and Data",
        "title": "Recognize angle measure as additive",
        "description": "Recognize angle measure as additive. Decomposed angles add up to the whole.",
    },
    {
        "standard_code": "OR.Math.4.G.A.1",
        "grade_level": 4,
        "domain": "Geometry",
        "title": "Draw and identify lines and angles",
        "description": "Draw points, lines, line segments, rays, angles (right, acute, obtuse), and perpendicular and parallel lines.",
    },
    {
        "standard_code": "OR.Math.4.G.A.2",
        "grade_level": 4,
        "domain": "Geometry",
        "title": "Classify two-dimensional figures",
        "description": "Classify two-dimensional figures based on parallel/perpendicular lines and angle sizes.",
    },
    {
        "standard_code": "OR.Math.4.G.A.3",
        "grade_level": 4,
        "domain": "Geometry",
        "title": "Recognize symmetry",
        "description": "Recognize a line of symmetry for a two-dimensional figure as a line across the figure such that the figure can be folded along the line into matching parts.",
    },
]

# Sample questions for key standards
SAMPLE_QUESTIONS = [
    {
        "standard_code": "OR.Math.4.NBT.A.1",
        "question_text": "In the number 54,321, what is the value of the digit 4?",
        "question_type": "multiple_choice",
        "difficulty": 2,
        "points": 1,
        "options": ["4", "40", "400", "4000"],
        "correct_answer": "400",
    },
    {
        "standard_code": "OR.Math.4.NBT.A.2",
        "question_text": "Write 45,678 in expanded form.",
        "question_type": "numeric",
        "difficulty": 2,
        "points": 2,
    },
    {
        "standard_code": "OR.Math.4.NBT.A.3",
        "question_text": "Round 3,456 to the nearest hundred.",
        "question_type": "numeric",
        "difficulty": 2,
        "points": 1,
    },
    {
        "standard_code": "OR.Math.4.NBT.B.4",
        "question_text": "Calculate: 4,567 + 2,389",
        "question_type": "numeric",
        "difficulty": 3,
        "points": 2,
    },
    {
        "standard_code": "OR.Math.4.NBT.B.5",
        "question_text": "Calculate: 234 × 5",
        "question_type": "numeric",
        "difficulty": 3,
        "points": 2,
    },
    {
        "standard_code": "OR.Math.4.NBT.B.6",
        "question_text": "Calculate: 456 ÷ 4",
        "question_type": "numeric",
        "difficulty": 3,
        "points": 2,
    },
    {
        "standard_code": "OR.Math.4.NF.A.1",
        "question_text": "Which fraction is equivalent to 2/3?",
        "question_type": "multiple_choice",
        "difficulty": 2,
        "points": 1,
        "options": ["4/6", "3/4", "5/6", "6/8"],
        "correct_answer": "4/6",
    },
    {
        "standard_code": "OR.Math.4.MD.A.1",
        "question_text": "How many centimeters are in 1 meter?",
        "question_type": "numeric",
        "difficulty": 1,
        "points": 1,
    },
    {
        "standard_code": "OR.Math.4.G.A.1",
        "question_text": "What do you call an angle that measures exactly 90 degrees?",
        "question_type": "multiple_choice",
        "difficulty": 1,
        "points": 1,
        "options": ["Acute angle", "Obtuse angle", "Right angle", "Straight angle"],
        "correct_answer": "Right angle",
    },
]


def seed_database(db_url: str) -> None:
    """Seed the database with Oregon standards and sample questions."""

    print(f"Connecting to database at {db_url}")

    # Use SQLAlchemy engine
    engine = create_engine(db_url)

    with engine.connect() as conn:
        # Insert standards
        print("Inserting standards...")
        for standard in OREGON_STANDARDS:
            result = conn.execute(
                text("""
                    INSERT INTO standards (id, standard_code, grade_level, domain, title, description)
                    VALUES (:id, :code, :grade, :domain, :title, :desc)
                    ON CONFLICT (standard_code, grade_level) DO NOTHING
                """),
                {
                    "id": str(uuid.uuid4()),
                    "code": standard["standard_code"],
                    "grade": standard["grade_level"],
                    "domain": standard["domain"],
                    "title": standard["title"],
                    "desc": standard["description"],
                },
            )
        conn.commit()
        print(f"Inserted {len(OREGON_STANDARDS)} standards")

        # Insert questions
        print("Inserting sample questions...")
        for question in SAMPLE_QUESTIONS:
            # Find standard by code
            result = conn.execute(
                text("SELECT id FROM standards WHERE standard_code = :code"),
                {"code": question["standard_code"]},
            )
            standard = result.fetchone()

            if standard:
                conn.execute(
                    text("""
                        INSERT INTO questions (id, standard_id, question_text, question_type, difficulty, points)
                        VALUES (:id, :std, :text, :type, :diff, :pts)
                        ON CONFLICT (id) DO NOTHING
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "std": standard[0],
                        "text": question["question_text"],
                        "type": question["question_type"],
                        "diff": question["difficulty"],
                        "pts": question["points"],
                    },
                )
        conn.commit()
        print(f"Inserted {len(SAMPLE_QUESTIONS)} sample questions")

    print("Database seeding complete!")


def main() -> None:
    """Main entry point."""
    from src.core.config import get_settings

    settings = get_settings()
    seed_database(settings.DATABASE_URL)


if __name__ == "__main__":
    main()
