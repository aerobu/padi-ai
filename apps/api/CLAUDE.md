# CLAUDE.md - PADI.AI Backend Guidance

## Tech Stack

- **Python:** 3.12+
- **Framework:** FastAPI
- **ORM:** SQLAlchemy 2.0 (async)
- **Validation:** Pydantic v2
- **Auth:** Auth0 JWT
- **LLM:** LiteLLM (COPPA-compliant routing)

## Project Structure

```
apps/api/
├── src/
│   ├── core/           # Core utilities
│   │   ├── __init__.py
│   │   ├── config.py   # Pydantic settings (57+ env vars)
│   │   └── security.py # Auth0 JWT validation
│   ├── api/            # API endpoints
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py  # API router
│   │       └── health.py  # Health check endpoints
│   ├── clients/        # External clients
│   │   └── llm_client.py  # LiteLLM wrapper (COPPA-compliant)
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   └── main.py         # App factory
└── tests/
```

## COPPA Compliance (Critical!)

### ALWAYS USE LOCAL MODELS FOR STUDENT DATA

```python
from src.clients.llm_client import get_llm_client, LLMPurpose

llm = get_llm_client()

# CORRECT: Student tutoring uses local Ollama
response = await llm.acomplete(
    messages=student_messages,
    purpose=LLMPurpose.STUDENT_TUTORING  # -> ollama/qwen2.5:72b
)

# INCORRECT: Never send student data to cloud
# response = await llm.acomplete(
#     messages=student_messages,
#     purpose=LLMPurpose.QUESTION_GENERATION  # -> anthropic/claude-3-5-sonnet
# )
```

### Allowed Cloud LLM Usage

Cloud LLMs (Claude, OpenAI) can ONLY be used for:
- Admin features
- Question generation (by teachers, not students)
- Analytics aggregation (no PII)
- Dashboard reporting (summarized data)

## Database Models

See `ENG-001-stage1.md` for complete schema.

Example model pattern:
```python
from sqlalchemy import Column, String, DateTime, Float
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.sql import func
from src.models.base import Base


class Student(AsyncAttrs, Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True)
    parent_id = Column(String, nullable=False)
    grade_level = Column(Integer, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

## API Patterns

### Async Endpoint Pattern
```python
from fastapi import APIRouter, Depends
from src.core.security import verify_jwt
from src.schemas.response import ApiResponse

router = APIRouter()


@router.get("/students/{student_id}", tags=["Students"])
async def get_student(
    student_id: str,
    credentials = Depends(verify_jwt),
) -> ApiResponse[Student]:
    """Get student by ID."""
    # Validate JWT user has access to this student
    user_payload = credentials
    if user_payload["sub"] != student_id:
        raise HTTPException(status_code=403)

    student = await get_student_by_id(student_id)
    return ApiResponse(data=student)
```

### Pydantic Schema Pattern
```python
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


class StudentCreate(BaseModel):
    parent_id: str
    grade_level: int = Field(ge=1, le=5)
    first_name: str
    last_name: str
    date_of_birth: Optional[datetime] = None


class StudentResponse(BaseModel):
    id: str
    parent_id: str
    grade_level: int
    first_name: str
    last_name: str
    created_at: datetime
```

## Configuration

All config loaded from `src.core.config.Settings`:
```python
from src.core.config import get_settings

settings = get_settings()
db_url = settings.DATABASE_URL
redis_url = settings.REDIS_URL
```

## Testing

```bash
cd apps/api
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

## Common Commands

```bash
# Run dev server
uvicorn src.main:app --reload

# Run tests
pytest tests/ -v

# Type check
mypy src --ignore-missing-imports

# Lint
ruff check src/
black src/ --check
```

## References

- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy 2.0: https://docs.sqlalchemy.org/
- Pydantic v2: https://docs.pydantic.dev/latest/
- LiteLLM: https://docs.litellm.ai/
