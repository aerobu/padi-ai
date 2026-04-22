# CLAUDE.md - PADI.AI Backend Guidance

## 🏗️ Architectural Guardrails (Strict)
1. **Repository Pattern:** DO NOT access DB models directly in routers. Use `src/repositories/`.
2. **Async Everything:** All DB and LLM calls must be `async/await`.
3. **Pydantic Schemas:** Use schemas for ALL inputs and outputs. Never return SQLAlchemy models directly.
4. **Error Handling:** Use custom exceptions from `src/core/exceptions.py` (if exist) or standard FastAPI exceptions.

## 🛡️ COPPA Compliance
- **Student Data:** MUST use `LLMPurpose.STUDENT_TUTORING`.
- **Local LLM:** Routed through Ollama via LiteLLM.

## 📁 Structure
```
apps/api/src/
├── api/v1/         # Routers (Keep thin!)
├── services/       # Business Logic
├── repositories/   # Data Access (All DB logic here)
├── models/         # SQLAlchemy Models
├── schemas/        # Pydantic Models
└── core/           # Config, Security
```

## 📋 Common Commands
```bash
pytest tests/ -v           # Run tests
ruff check src/            # Lint
black src/                 # Format
mypy src/                  # Type check
```

## 📖 Pattern: Repository Use
```python
# GOOD: Using repository
@router.get("/{id}")
async def get_student(id: str, repo: StudentRepository = Depends()):
    return await repo.get_by_id(id)

# BAD: Direct DB access
# @router.get("/{id}")
# async def get_student(id: str, db: Session = Depends(get_db)):
#     return db.query(Student).filter(Student.id == id).first()
```
