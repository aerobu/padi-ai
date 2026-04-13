#!/usr/bin/env python3
"""
Simple seed script for PADI.AI Stage 1.
Seeds Oregon math standards and sample questions using SQLAlchemy ORM.

Usage:
    python -m scripts.seed_simple
"""

import sys
import uuid
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.orm import Session
from src.core.config import get_settings
from src.models import Base, Standard, Question
from sqlalchemy import create_engine

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
        "standard_code": "OR.Math.4.MD.A.1",
        "grade_level": 4,
        "domain": "Measurement and Data",
        "title": "Know relative sizes of measurement units",
        "description": "Know the relative sizes of measurement units within one system of units.",
    },
    {
        "standard_code": "OR.Math.4.MD.C.5",
        "grade_level": 4,
        "domain": "Measurement and Data",
        "title": "Recognize angle concepts",
        "description": "Recognize angles as geometric shapes formed by two rays sharing a common endpoint.",
    },
    {
        "standard_code": "OR.Math.4.G.A.1",
        "grade_level": 4,
        "domain": "Geometry",
        "title": "Draw and identify lines and angles",
        "description": "Draw points, lines, line segments, rays, angles, and perpendicular and parallel lines.",
    },
    {
        "standard_code": "OR.Math.4.G.A.2",
        "grade_level": 4,
        "domain": "Geometry",
        "title": "Classify two-dimensional figures",
        "description": "Classify two-dimensional figures based on parallel/perpendicular lines and angle sizes.",
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
    },
]


def seed_database() -> None:
    """Seed the database with Oregon standards and sample questions."""

    print("Creating database connection...")
    settings = get_settings()

    # Create engine
    engine = create_engine(settings.DATABASE_URL)

    # Create all tables
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    # Create session
    with Session(engine) as session:
        # Insert standards
        print("Inserting standards...")
        standards = []
        for std_data in OREGON_STANDARDS:
            # Check if standard already exists
            existing = session.query(Standard).filter_by(
                standard_code=std_data["standard_code"],
                grade_level=std_data["grade_level"]
            ).first()

            if existing:
                continue

            standard = Standard(
                id=str(uuid.uuid4()),
                standard_code=std_data["standard_code"],
                grade_level=std_data["grade_level"],
                domain=std_data["domain"],
                title=std_data["title"],
                description=std_data["description"],
            )
            standards.append((std_data["standard_code"], standard))
            session.add(standard)

        session.commit()
        print(f"Inserted {len(standards)} standards")

        # Insert questions
        print("Inserting sample questions...")
        for q_data in SAMPLE_QUESTIONS:
            # Find standard by code
            standard = session.query(Standard).filter_by(
                standard_code=q_data["standard_code"]
            ).first()

            if not standard:
                print(f"  Warning: Standard {q_data['standard_code']} not found")
                continue

            # Check if question already exists
            existing = session.query(Question).filter_by(
                standard_id=standard.id,
                question_text=q_data["question_text"]
            ).first()

            if existing:
                continue

            question = Question(
                id=str(uuid.uuid4()),
                standard_id=standard.id,
                question_text=q_data["question_text"],
                question_type=q_data["question_type"],
                difficulty=q_data["difficulty"],
                points=q_data["points"],
            )
            session.add(question)

        session.commit()
        print(f"Inserted {len(SAMPLE_QUESTIONS)} sample questions")

    print("Database seeding complete!")


def main() -> None:
    """Main entry point."""
    seed_database()


if __name__ == "__main__":
    main()
