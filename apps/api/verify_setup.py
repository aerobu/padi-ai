"""
Verify PADI.AI API setup.
Run this to check if all components are properly configured.
"""

import sys
import asyncio
from typing import Tuple


def check_import(module_name: str) -> Tuple[bool, str]:
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        return True, f"✓ {module_name}"
    except ImportError as e:
        return False, f"✗ {module_name}: {e}"


def main():
    """Run all verification checks."""
    print("PADI.AI API Setup Verification")
    print("=" * 40)

    checks = [
        ("fastapi", "FastAPI framework"),
        ("uvicorn", "ASGI server"),
        ("sqlalchemy", "SQLAlchemy ORM"),
        ("asyncpg", "PostgreSQL async driver"),
        ("pydantic", "Pydantic validation"),
        ("pydantic_settings", "Settings management"),
        ("redis", "Redis client"),
        ("litellm", "LLM routing"),
        ("alembic", "Database migrations"),
        ("pybkt", "Bayesian Knowledge Tracing"),
    ]

    results = []
    for module, description in checks:
        success, message = check_import(module)
        results.append((success, message))

    print()
    for success, message in results:
        print(message)

    print()
    print("=" * 40)

    # Check if all passed
    all_passed = all(r[0] for r in results)
    if all_passed:
        print("All checks passed! ✓")
        return 0
    else:
        print("Some checks failed. Please install missing dependencies.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
