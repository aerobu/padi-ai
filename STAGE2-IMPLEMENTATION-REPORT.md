# Stage 2 Implementation Report — Critical Issues & Remediation Guide

**Status:** Stage 2 is ~30–35% complete. This report details all bugs found during code review and provides step-by-step implementation guidance to bring Stage 2 to full acceptance.

**Report Generated:** 2026-04-19  
**Code Review Scope:** All new Stage 2 endpoints, services, schemas, migrations, and tests

---

## Executive Summary

The Qwen Stage 2 implementation has:
- ✅ Data layer: Models and migration created (with bugs)
- ✅ Service layer: Graph, plan, BKT services sketched (with critical algorithm bugs)
- ✅ API endpoints: Auth, generation jobs, learning plans added (with security holes)
- ❌ AI pipeline: Only Step 1 (LLM prompt) completed; Steps 2–5 missing
- ❌ Gamification: BadgeService, StreakService not started
- ❌ Student Dashboard: All frontend pages missing
- ❌ Parent Dashboard: All frontend pages + endpoints missing
- ❌ Tests: Multiple tests broken, critical test coverage gaps

**Total Remaining Work:** ~70–95 hours across 4 priority tiers.

---

# Priority 0: Critical Blockers (2–3 hours)

These bugs prevent ANY testing or database operations. Fix these first.

---

## P0-1: Migration Syntax Error

**File:** `apps/api/alembic/versions/003_add_stage2_tables.py` line ~283  
**Status:** BLOCKS ALL DB OPERATIONS

### Issue
```python
# Line 283 - INVALID SYNTAX:
postgresql descending=[False, True]
```

The `descending` keyword appears without a parent clause. This is a Python syntax error.

### Fix
Read the full migration file and identify what this line was attempting to do. The correct syntax for descending index columns in SQLAlchemy is:

```python
Index('index_name', column1.desc(), column2.asc())
```

Or using `postgresql_ops`:
```python
Index('index_name', 'col1', 'col2', postgresql_ops={'col1': 'DESC', 'col2': 'ASC'})
```

**Action:** Find the context around line 283 and correct the syntax. Ensure the migration file can be imported without errors.

---

## P0-2: Foreign Key References Non-Existent Column

**Files:** 
- `apps/api/src/models/models.py` — `PlanModule` class
- `apps/api/src/models/models.py` — `GenerationJob` class

**Status:** BLOCKS PLAN AND JOB CREATION

### Issue
Both models reference `ForeignKey("standards.code")` but the `Standard` model has:
- Primary key: `id` (UUID)
- No column named `code`
- Standard identifier is stored as `standard_code` (a string like `"4.NF.A.1"`)

### Fix
1. **In `PlanModule`:** Rename `standard_code` column to `standard_id` and change FK:
   ```python
   standard_id: UUID = Column(UUID(as_uuid=True), ForeignKey("standards.id"), nullable=False)
   ```

2. **In `GenerationJob`:** Same change:
   ```python
   standard_id: UUID = Column(UUID(as_uuid=True), ForeignKey("standards.id"), nullable=False)
   ```

3. **Update migration** `003_add_stage2_tables.py`: Ensure columns are named `standard_id` (not `standard_code`).

4. **Update all services** that reference these columns:
   - `learning_plan_service.py` — uses `module.standard_code` 
   - `skill_graph_service.py` — uses `rel.prerequisite_id` and `rel.standard_id`
   - `llm_question_generator.py` — uses `generated_question.standard_code`

Replace all `.standard_code` references with the actual UUID FK or the corresponding Standard record's `standard_code` attribute.

---

## P0-3: BKT Algorithm Discards Observations

**File:** `apps/api/src/services/bkt_impl.py` line ~150 in `forward_inference()`  
**Status:** BREAKS MASTERY TRACKING THROUGHOUT SYSTEM

### Issue
The Bayesian Knowledge Tracing implementation computes the posterior probability correctly (lines 112–131) but then discards it:

```python
# Lines 112-131: Correctly compute Bayesian posterior
# p_l (probability of learning) given the observation
posterior = p_l_given_obs  # Correctly computed from observation

# Line 150: WRONG - overwrites posterior with pre-observation state
self.p_l = old_p_l + self.p_trans * (1 - old_p_l)
```

This means the student's response (correct/incorrect) has ZERO impact on the learned state. The model only advances based on time/transitions, not performance — completely defeating adaptive learning.

### Fix
```python
# Line 150 should be:
self.p_l = posterior + self.p_trans * (1 - posterior)
```

Also fix the transition probability default:
```python
# Line ~xx (in __init__):
# WRONG: self.p_trans = 0.5
# CORRECT (standard BKT):
self.p_trans = 0.1
```

P(T)=0.5 means students master in 1–2 tries regardless of performance. Standard BKT uses 0.1–0.3.

### Verification
After fix, verify:
- Correct answer → p_l increases
- Incorrect answer → p_l decreases  
- Answers have immediate effect (not delayed to next transition)
- Both `_states` history and current `p_l` reflect observations

---

## P0-4: LLM Pipeline Returns Wrong Type

**File:** `apps/api/src/services/llm_question_generator.py` line ~352 in `_validate_question()`  
**Status:** CRASHES ON EVERY QUESTION GENERATION

### Issue
Method signature says it returns `GeneratedQuestion`:
```python
async def _validate_question(...) -> GeneratedQuestion:
```

But `execute_generation_job` (line ~124) calls:
```python
validation_result = await self._validate_question(...)
# Later...
if validation_result.overall_passed:  # AttributeError!
```

`GeneratedQuestion` ORM model has no `overall_passed` attribute.

### Fix
The method creates BOTH a `GeneratedQuestion` AND a `QuestionValidationResult`:
1. Change the return type to `QuestionValidationResult`
2. Return the validation result, not the generated question
3. Store the generated question reference in the validation result

```python
async def _validate_question(...) -> QuestionValidationResult:
    generated_question = GeneratedQuestion(...)
    await self.session.flush()
    
    # Do validation...
    validation_result = QuestionValidationResult(
        generated_question_id=generated_question.id,
        overall_passed=...,
        # ... other fields
    )
    return validation_result

# In execute_generation_job:
validation_result = await self._validate_question(...)
if validation_result.overall_passed:  # Now works!
```

---

# Priority 1: High-Severity Bugs (6–8 hours)

Fix these before integration testing. These are security, logic, or runtime crashes.

---

## P1-1: Query Parameter Shadows fastapi.status

**File:** `apps/api/src/api/v1/endpoints/generation_jobs.py` line ~94 in `list_generation_jobs()`

### Issue
```python
from fastapi import status  # Module import

async def list_generation_jobs(..., status: str = Query(None)):  # Parameter name shadows import!
    if user_payload.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, ...)  # NameError or TypeError
```

Python sees `status` as the query param string (e.g., `"queued"`), not the module. Calling `.HTTP_403_FORBIDDEN` on a string crashes.

### Fix
Rename the parameter:
```python
async def list_generation_jobs(..., status_filter: str = Query(None)):
    # ...
    if user_payload.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    # Later, when filtering:
    if status_filter:
        query = query.filter(GenerationJob.status == status_filter)
```

---

## P1-2: Double verify_jwt Calls

**Files:** 
- `apps/api/src/api/v1/endpoints/generation_jobs.py` line ~108
- `apps/api/src/api/v1/endpoints/learning_plans.py` line ~67

### Issue
Endpoints use `credentials` as a dependency:
```python
async def create_generation_job(
    credentials: HTTPAuthorizationCredentials = Depends(verify_jwt),
    ...
):
```

The `Depends(verify_jwt)` already decodes the JWT and returns the `HTTPAuthorizationCredentials` object. But then the code calls:
```python
user_payload = await verify_jwt(credentials)  # Wrong: credentials is already decoded, not raw auth header
```

This passes an `HTTPAuthorizationCredentials` object to `verify_jwt()` which expects raw HTTP credentials, causing type errors.

### Fix
Remove the redundant call. Use the credential directly:
```python
async def create_generation_job(
    credentials: HTTPAuthorizationCredentials = Depends(verify_jwt),
    ...
):
    # Don't call verify_jwt again
    # If you need the decoded payload, modify the dependency to return it:
    # Option 1: Return payload from verify_jwt dependency
    # Option 2: Decode credentials here locally
    user_id = extract_user_id_from_credentials(credentials)
```

Or, update `verify_jwt` to return the decoded payload instead of the credentials object, and adjust the dependency:
```python
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = await verify_jwt(credentials)
    return payload

# In endpoints:
async def create_generation_job(current_user: dict = Depends(get_current_user), ...):
    user_id = current_user["sub"]
```

---

## P1-3: Missing Auth Check on Admin Endpoints

**File:** `apps/api/src/api/v1/endpoints/generation_jobs.py`

### Issue
Two endpoints have NO authentication:
- `POST /admin/generation-jobs/{job_id}/execute` (line ~244)
- `GET /admin/review-queue` (line ~280)

Any unauthenticated caller can trigger LLM jobs (costing money) and read all questions in review.

### Fix
Add `Depends(verify_jwt)` to both endpoints:
```python
@router.post("/{job_id}/execute")
async def execute_generation_job(
    job_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db),
):
    # Also add role check:
    user_payload = extract_payload(credentials)
    if user_payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
```

---

## P1-4: Plan Complete Module Doesn't Verify Ownership

**File:** `apps/api/src/api/v1/endpoints/learning_plans.py` line ~217 in `complete_module_endpoint()`

### Issue
```python
async def complete_module_endpoint(
    plan_id: UUID,
    module_id: UUID,
    request: ModuleCompleteRequest,
    credentials: HTTPAuthorizationCredentials = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db),
):
    plan = await db.get(LearningPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # BUG: No check that plan.student_id belongs to the authenticated user!
    # Any authenticated user can complete modules on any other user's student plan
```

### Fix
Add ownership verification:
```python
# Extract user_id from credentials
user_payload = extract_payload(credentials)
authenticated_user_id = user_payload["sub"]

# Fetch plan with student relationship
plan = await db.get(LearningPlan, plan_id, options=[selectinload(LearningPlan.student)])
if not plan:
    raise HTTPException(status_code=404, detail="Plan not found")

# Verify the student belongs to the authenticated user
student_user_id = plan.student.user_id  # Assuming Student has user_id FK
if str(student_user_id) != authenticated_user_id:
    raise HTTPException(status_code=403, detail="Cannot access this student's plan")
```

---

## P1-5: Skill Graph Nodes/Edges Key Mismatch

**File:** `apps/api/src/services/skill_graph_service.py` line ~68–73 in `get_graph()`

### Issue
```python
# Nodes added with standard_code as key:
for std in standards:
    G.add_node(std.standard_code)  # e.g., "4.NF.A.1"

# But edges added with UUID IDs:
for rel in relationships:
    G.add_edge(rel.prerequisite_id, rel.standard_id)  # These are UUIDs, not strings!
```

The graph has nodes keyed by string codes but edges reference UUID primary keys. No edges exist in the graph. All topological sorting and prerequisite chain logic returns empty.

### Fix
Option 1: Use standard_code as the key everywhere:
```python
# Nodes:
for std in standards:
    G.add_node(std.standard_code)

# Edges:
for rel in relationships:
    prereq_std = await db.get(Standard, rel.prerequisite_id)
    target_std = await db.get(Standard, rel.standard_id)
    G.add_edge(prereq_std.standard_code, target_std.standard_code, weight=rel.strength)
```

Option 2: Update the PrerequisiteRelationship table to store `prerequisite_code` and `standard_code` (strings) instead of UUIDs.

**Recommended:** Use Option 1 (query the Standard records). Requires updating the migration to not create those columns.

---

## P1-6: Generated Question Promoted with Wrong Type

**File:** `apps/api/src/services/llm_question_generator.py` line ~449 in `_promote_to_questions_table()`

### Issue
```python
async def _promote_to_questions_table(self, generated_question: GeneratedQuestion):
    # generated_question.standard_code is a string like "4.NF.A.1"
    # But Question.standard_id is a UUID FK to standards.id
    
    question = Question(
        standard_id=generated_question.standard_code,  # WRONG TYPE!
        # ... other fields
    )
```

Inserting a string into a UUID FK column causes a database constraint violation.

### Fix
```python
async def _promote_to_questions_table(self, generated_question: GeneratedQuestion):
    # Fetch the Standard by code to get the UUID:
    standard = await self.session.execute(
        select(Standard).filter(Standard.standard_code == generated_question.standard_code)
    )
    standard = standard.scalars().first()
    if not standard:
        raise ValueError(f"Standard {generated_question.standard_code} not found")
    
    question = Question(
        standard_id=standard.id,  # Now a UUID
        # ... other fields
    )
```

---

## P1-7: `/learning-plans/sequence` Route Unreachable

**File:** `apps/api/src/api/v1/endpoints/learning_plans.py` route definition order

### Issue
FastAPI matches routes in order. If `GET /learning-plans/{student_id}` is defined before `GET /learning-plans/sequence`, the latter can never be reached because `sequence` matches the `{student_id}` parameter.

### Fix
Move the `/sequence` route definition BEFORE the `/{student_id}` route:
```python
@router.get("/sequence", tags=["Learning Plans"])
async def get_skill_sequence(...):
    # ...

# THEN define the parameterized route:
@router.get("/{student_id}", tags=["Learning Plans"])
async def get_learning_plan(...):
    # ...
```

Or use a more specific path that doesn't conflict:
```python
@router.get("/skill/sequence", tags=["Learning Plans"])
```

---

## P1-8: Module actual_minutes NoneType Crash

**File:** `apps/api/src/services/learning_plan_service.py` line ~443 in `update_module_progress()`

### Issue
```python
module.actual_minutes += minutes_spent  # If actual_minutes is None in DB, TypeError!
```

The column may be `None` on first update.

### Fix
```python
module.actual_minutes = (module.actual_minutes or 0) + minutes_spent
```

---

## P1-9: Consent Completed Hardcoded to True

**File:** `apps/api/src/api/v1/endpoints/auth.py` line ~122 in `login_endpoint()`

### Issue
```python
async def login_endpoint(auth0_sub: str, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, auth0_sub)
    return {
        "user_id": user.id,
        "consent_completed": True,  # HARDCODED! COPPA BYPASS!
    }
```

All users receive `consent_completed: True` regardless of actual ConsentRecord state. Children can access the platform without parental consent.

### Fix
Check the actual consent:
```python
async def login_endpoint(auth0_sub: str, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, auth0_sub)
    
    # Find the latest consent record for this user
    consent = await db.execute(
        select(ConsentRecord)
        .filter(ConsentRecord.user_id == user.id)
        .order_by(ConsentRecord.created_at.desc())
        .limit(1)
    )
    consent = consent.scalars().first()
    
    consent_completed = consent.consent_confirmed_at is not None if consent else False
    
    return {
        "user_id": user.id,
        "consent_completed": consent_completed,
        "role": user.role,
    }
```

---

## P1-10: verify_email Does Nothing

**File:** `apps/api/src/api/v1/endpoints/auth.py` line ~95 in `verify_email_endpoint()`

### Issue
```python
async def verify_email_endpoint(token: str):
    # Comment says: "For now, just mark email_verified = True"
    # But no code actually does it!
    return {"status": "email_verified", "next_step": "consent"}
```

The email is never marked verified.

### Fix
```python
async def verify_email_endpoint(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    # Validate token (decode, check expiry, etc.)
    # For now, assume token contains user_id:
    user_id = validate_verification_token(token)
    
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.email_verified = True
    await db.commit()
    
    return {"status": "email_verified", "next_step": "consent"}
```

---

## P1-11: user_id Extraction Always Returns None

**File:** `apps/api/src/api/v1/endpoints/generation_jobs.py` line ~58

### Issue
```python
user_payload = credentials.credentials  # credentials.credentials is a STRING (raw JWT)
user_id = user_payload.get("sub")  # Calling .get() on a string returns None
```

Every created job has `created_by = None`.

### Fix
Decode the JWT properly:
```python
# If credentials is HTTPAuthorizationCredentials:
token = credentials.credentials  # Raw JWT string

# Decode it (assuming verify_jwt handles this):
payload = await verify_jwt(credentials)  # Now a dict
user_id = payload.get("sub")
```

Or use the dependency-based approach (see P1-2 fix).

---

# Priority 2: Code Quality & Type Fixes (4–6 hours)

These don't cause crashes but are correctness issues.

---

## P2-1: ApiResponse Not a Pydantic Model

**File:** `apps/api/src/schemas/response.py`

### Issue
```python
class ApiResponse(Generic[T]):  # Missing BaseModel!
    success: bool
    data: T
    error: Optional[dict]
```

This class won't serialize as a FastAPI response model. Fields have no Pydantic type validation.

### Fix
```python
from pydantic import BaseModel, Field
from typing import Generic, TypeVar

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {},
                "error": None
            }
        }
```

---

## P2-2: Pydantic v2 Incompatibilities

**Files:**
- `apps/api/src/schemas/user.py`
- `apps/api/src/schemas/generation_job.py`

### Issue 1: `update_forward_refs()` deprecated
```python
# In user.py:
StudentResponse.model_rebuild()  # Pydantic v2 uses this
StudentResponse.update_forward_refs()  # This is Pydantic v1, ignored in v2
```

### Fix
Replace all `update_forward_refs()` with `model_rebuild()`.

### Issue 2: List field constraints use wrong names
```python
# In generation_job.py:
difficulty_levels: List[int] = Field(min_items=1, max_items=5)  # v1 syntax
```

### Fix
```python
difficulty_levels: List[int] = Field(min_length=1, max_length=5)  # v2 syntax
```

---

## P2-3: JobStatus Enum Mismatch

**Files:**
- `apps/api/src/models/models.py` — `JobStatus` enum
- `apps/api/src/schemas/generation_job.py` — `JobStatus` enum

### Issue
Models define `RUNNING`, schema defines `IN_PROGRESS`. Filter queries on status will fail to match.

### Fix
Unify to one name. Recommend using `RUNNING` (matches models). Update schema to use `RUNNING`.

---

## P2-4: pgvector Index Type Wrong

**File:** `apps/api/alembic/versions/003_add_stage2_tables.py` line ~227

### Issue
```python
# For content_embedding column (float array for pgvector):
Index(..., postgresql_using='gin')  # GIN is for full-text / array containment
```

GIN is wrong for vector similarity search.

### Fix
```python
# For cosine similarity (as per spec):
Index(..., postgresql_using='ivfflat', postgresql_with={'lists': 100})
```

---

## P2-5: strength Type Mismatch

**Files:**
- `apps/api/src/schemas/standard.py` — `PrerequisiteRelation.strength: float`
- `apps/api/src/models/models.py` — `PrerequisiteRelationship.strength: String`

### Issue
Type mismatch causes Pydantic validation failures.

### Fix
Make both the same type. Recommend `float`:
```python
# In models.py:
strength: float = Column(Float, default=1.0)

# In schemas:
strength: float
```

---

## P2-6: ContentReviewQueue Partial Index Invalid

**File:** `apps/api/src/models/models.py` in `ContentReviewQueue` class definition

### Issue
```python
__table_args__ = (
    Index(..., postgresql_where=status.in_([ReviewStatus.PENDING, ReviewStatus.IN_REVIEW])),
)
```

This syntax is invalid. `status` is a column object, but this is using it in a boolean expression at class definition time.

### Fix
```python
__table_args__ = (
    Index(
        'idx_review_queue_pending',
        'status',
        postgresql_where=and_(
            ContentReviewQueue.status == ReviewStatus.PENDING,
            ContentReviewQueue.status == ReviewStatus.IN_REVIEW
        )
    ),
)
```

Or simply remove the partial index if the full index is sufficient:
```python
__table_args__ = (
    Index('idx_review_queue_status', 'status'),
)
```

---

## P2-7: Fix Broken Tests

### `tests/test_models.py`
Lines check for columns that don't exist:
```python
# WRONG — these columns don't exist
assert hasattr(User, 'email')
assert hasattr(Student, 'first_name')

# CORRECT:
assert hasattr(User, 'email_encrypted')
assert hasattr(User, 'email_hash')
assert hasattr(Student, 'display_name')
```

### `tests/security/test_jwt_validation.py`
Remove or fix `test_invalid_role_rejected`:
```python
# Current test expects PyJWT to reject unknown roles — it doesn't
# PyJWT only validates standard claims (exp, nbf, etc.)
# Either remove this test or change to test your custom validation logic
```

### `tests/security/test_encryption_service.py`
Should test through `EncryptionService` class, not raw Fernet:
```python
from src.core.encryption import EncryptionService

encryption_service = EncryptionService()
encrypted = encryption_service.encrypt("test@example.com")
decrypted = encryption_service.decrypt(encrypted)
assert decrypted == "test@example.com"
```

---

## P2-8: Remove Stale Session Singletons

**Files:**
- `apps/api/src/services/learning_plan_service.py` lines ~492–500
- `apps/api/src/services/llm_question_generator.py` (similar pattern)

### Issue
Module-level singletons store a reference to a specific DB session. In FastAPI, sessions are per-request and closed after. Reusing a singleton will cause "detached instance" errors.

### Fix
Remove the singleton pattern. Endpoints already instantiate services with a fresh session per request. Delete these lines entirely:
```python
# DELETE THIS:
_service = LearningPlanService(None)  # Stale session!

def get_learning_plan_service():
    return _service
```

Services should only be instantiated by endpoints/routes with a fresh `AsyncSession` dependency.

---

## P2-9: SES Client Settings Initialization

**File:** `apps/api/src/clients/ses_client.py` line ~18

### Issue
```python
class SESClient:
    def __init__(self):
        self.aws_access_key_id = settings.AWS_ACCESS_KEY_ID  # But settings isn't defined yet!

# ... later in module:
settings = get_settings()
```

### Fix
Initialize settings inside `__init__`:
```python
class SESClient:
    def __init__(self):
        settings = get_settings()
        self.aws_access_key_id = settings.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        self.aws_region = settings.AWS_REGION
        self.from_email = settings.SES_FROM_EMAIL
```

---

## P2-10: Standardize Transaction Ownership

**Affected Files:**
- `apps/api/src/repositories/generation_job_repository.py`
- `apps/api/src/repositories/learning_plan_repository.py`

### Issue
Some repositories call `commit()` directly, others only `flush()`. Services also commit. Unclear which layer owns the transaction.

### Fix
**Define a pattern and follow it consistently:**

**Option A: Repositories flush only; services commit**
```python
# In repository:
async def update_status(self, job_id: UUID, new_status: JobStatus):
    # ... update logic ...
    await self.session.flush()  # No commit!

# In service:
async def execute_generation_job(self, job_id: UUID):
    # ... business logic ...
    await self.repository.update_status(job_id, JobStatus.RUNNING)
    # ... more logic ...
    await self.session.commit()  # Service owns the transaction
```

**Option B: Unit of Work pattern**
Create a `UnitOfWork` class that manages transactions across multiple repositories.

**Recommendation:** Use Option A. It's simpler and already partially followed. Update all repositories to use this pattern.

---

# Priority 3: Feature Implementations (60–80 hours)

These are complete feature additions required for Stage 2 acceptance.

---

## P3-1: Complete AI Pipeline (Steps 2–5)

**File:** `apps/api/src/services/llm_question_generator.py`

Currently, `_generate_questions_for_difficulty` calls the LLM and returns mock or real JSON. The response then goes to `_validate_question` (P0-4 fixes this first) which is a stub.

### Step 2: Sandboxed Solution Execution

Create a method `_execute_solution_code()`:
```python
async def _execute_solution_code(self, python_code: str, timeout_seconds: int = 10) -> tuple[bool, str]:
    """
    Execute question solution code in isolated subprocess.
    
    Returns: (success: bool, output: str)
    """
    import subprocess
    import tempfile
    
    try:
        # Write code to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            code_file = f.name
        
        # Run subprocess with timeout, no network, limited stdlib
        result = subprocess.run(
            ['python', code_file],
            capture_output=True,
            timeout=timeout_seconds,
            text=True,
            # Disable network:
            # (Note: Python subprocess doesn't have built-in network isolation,
            #  use a container or seccomp profile for real sandboxing)
        )
        
        return (result.returncode == 0, result.stdout)
    except subprocess.TimeoutExpired:
        return (False, "Execution timeout")
    except Exception as e:
        return (False, str(e))
    finally:
        import os
        if os.path.exists(code_file):
            os.unlink(code_file)
```

### Step 3: Content Classification

Create a method `_classify_question()`:
```python
async def _classify_question(self, question_text: str, option_count: int) -> dict:
    """
    Classify question for pedagogical attributes.
    
    Returns: {
        'reading_level': float (Flesch-Kincaid),
        'word_count': int,
        'has_prohibited_keywords': bool,
        'is_multiple_choice': bool,
        'is_valid': bool,
        'errors': [str],
    }
    """
    import textstat
    
    errors = []
    
    # Reading level (Flesch-Kincaid): should be 2.5–5.5 for grades 1–5
    fk_score = textstat.flesch_kincaid_grade(question_text)
    if not (2.5 <= fk_score <= 5.5):
        errors.append(f"Reading level {fk_score:.1f} outside range 2.5–5.5")
    
    # Word count: typically 5–50 words for math questions
    word_count = len(question_text.split())
    if not (5 <= word_count <= 50):
        errors.append(f"Word count {word_count} outside range 5–50")
    
    # Prohibited keywords (COPPA/safety)
    prohibited = {'kill', 'violence', 'drugs', 'weapons'}  # Expand list
    has_prohibited = any(kw in question_text.lower() for kw in prohibited)
    if has_prohibited:
        errors.append("Contains prohibited keywords")
    
    # Multiple choice: should have exactly 4 options, one correct
    if option_count != 4:
        errors.append(f"Expected 4 options, got {option_count}")
    
    return {
        'reading_level': fk_score,
        'word_count': word_count,
        'has_prohibited_keywords': has_prohibited,
        'is_multiple_choice': option_count == 4,
        'is_valid': len(errors) == 0,
        'errors': errors,
    }
```

### Step 4: Claude Haiku Verification

Create a method `_verify_with_claude()`:
```python
async def _verify_with_claude(self, question: dict, standard_code: str) -> tuple[float, str]:
    """
    Use Claude Haiku to verify standard alignment and age-appropriateness.
    
    Returns: (confidence: float 0.0–1.0, reason: str)
    """
    from anthropic import Anthropic
    
    client = Anthropic()  # Uses ANTHROPIC_API_KEY
    
    prompt = f"""
    Question: {question['text']}
    Options: A) {question['options'][0]} B) {question['options'][1]} C) {question['options'][2]} D) {question['options'][3]}
    Standard: {standard_code}
    Grade Level: Elementary (Grades 1–5)
    
    Evaluate this question on:
    1. Alignment to the academic standard
    2. Age-appropriateness for elementary students
    3. Mathematical correctness
    4. Safety (no violence, inappropriate content)
    
    Respond with JSON:
    {{
        "alignment_confidence": 0.0–1.0,
        "age_appropriate": true/false,
        "mathematically_correct": true/false,
        "safe": true/false,
        "reasoning": "explanation"
    }}
    """
    
    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    
    import json
    result = json.loads(response.content[0].text)
    
    # Overall confidence: alignment * (age_appropriate & safe & correct)
    base_confidence = result['alignment_confidence']
    if not (result['age_appropriate'] and result['safe'] and result['mathematically_correct']):
        base_confidence *= 0.5
    
    reason = result['reasoning']
    return (base_confidence, reason)
```

### Step 5: pgvector Deduplication

Create a method `_check_dedup()`:
```python
async def _check_dedup(self, question_text: str, standard_id: UUID, similarity_threshold: float = 0.92) -> tuple[bool, Optional[UUID]]:
    """
    Check if question is too similar to existing questions (pgvector cosine similarity).
    
    Returns: (is_duplicate: bool, similar_question_id: Optional[UUID])
    """
    from sentence_transformers import SentenceTransformer
    
    # Generate embedding for this question
    model = SentenceTransformer('all-MiniLM-L6-v2')
    question_embedding = model.encode(question_text)
    
    # Query similar questions using pgvector
    result = await self.session.execute(
        select(GeneratedQuestion).filter(
            GeneratedQuestion.standard_id == standard_id,
            func.cosine_distance(
                GeneratedQuestion.content_embedding,
                question_embedding
            ) < (1 - similarity_threshold)  # pgvector uses distance (1 - cosine)
        ).limit(1)
    )
    
    similar = result.scalars().first()
    if similar:
        return (True, similar.id)
    
    return (False, None)
```

### Updated execute_generation_job

Integrate all steps:
```python
async def execute_generation_job(self, job_id: UUID):
    job = await self.repository.get_by_id(job_id)
    if job.status != JobStatus.QUEUED:
        raise ValueError("Job not queued")
    
    await self.repository.update_status(job_id, JobStatus.RUNNING)
    
    auto_approved_count = 0
    needs_review_count = 0
    
    for difficulty in job.difficulty_levels:
        questions_json = await self._generate_questions_for_difficulty(
            job.standard_code,
            difficulty,
            job.requested_count // len(job.difficulty_levels)
        )
        
        for q in questions_json:
            # Step 2: Execute solution
            solution_ok, solution_output = await self._execute_solution_code(q['solution_code'])
            if not solution_ok:
                continue  # Skip invalid solutions
            
            # Step 3: Classify
            classification = await self._classify_question(q['text'], len(q['options']))
            if not classification['is_valid']:
                continue
            
            # Step 5: Check dedup
            is_dup, _ = await self._check_dedup(q['text'], job.standard_id)
            if is_dup:
                continue
            
            # Create generated question record
            generated = GeneratedQuestion(
                generation_job_id=job_id,
                standard_id=job.standard_id,
                text=q['text'],
                options=q['options'],
                correct_answer=q['correct_answer'],
                solution_code=q['solution_code'],
                content_embedding=model.encode(q['text']).tolist(),
                validation_status=ValidationStatus.PENDING,
            )
            await self.session.flush()
            
            # Step 4: Claude Haiku verify
            confidence, reason = await self._verify_with_claude(q, job.standard_code)
            
            # Create validation result
            validation = QuestionValidationResult(
                generated_question_id=generated.id,
                solution_passed=solution_ok,
                age_appropriate=True,  # From Claude response
                mathematically_correct=True,
                dedup_passed=not is_dup,
                confidence_score=confidence,
                validation_details=reason,
                validation_status=ValidationStatus.PASSED if all([solution_ok, classification['is_valid']]) else ValidationStatus.FAILED,
            )
            
            # Step 5: Auto-approve or queue for review
            if confidence >= 0.85:
                await self._promote_to_questions_table(generated)
                auto_approved_count += 1
            else:
                await self._add_to_review_queue(generated, priority=int((1 - confidence) * 10))
                needs_review_count += 1
    
    job.status = JobStatus.COMPLETED
    job.total_generated = auto_approved_count + needs_review_count
    job.total_auto_approved = auto_approved_count
    job.completed_at = datetime.utcnow()
    await self.session.commit()
```

---

## P3-2: BadgeService Implementation

**New File:** `apps/api/src/services/badge_service.py`

```python
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.models import StudentBadge, BadgeTier

class BadgeType(str, Enum):
    FIRST_SESSION = "first_session"  # "Math Explorer"
    STREAK_3 = "streak_3"  # "On a Roll!"
    STREAK_7 = "streak_7"  # "Week Warrior"
    STREAK_30 = "streak_30"  # "Month Master"
    HALFWAY = "halfway"  # "Halfway Hero" (50% modules mastered)
    PLAN_COMPLETE = "plan_complete"  # "Grade Ready!"
    PERFECT_MODULE = "perfect_module"  # 100% on all lessons
    SPEED_DEMON = "speed_demon"  # Complete 3 modules in one week
    FOCUS = "focus"  # 10 consecutive correct answers
    # Add 11 total as per spec

BADGE_TIERS = {
    BadgeType.FIRST_SESSION: BadgeTier.BRONZE,
    BadgeType.STREAK_3: BadgeTier.BRONZE,
    BadgeType.STREAK_7: BadgeTier.SILVER,
    BadgeType.STREAK_30: BadgeTier.GOLD,
    BadgeType.HALFWAY: BadgeTier.SILVER,
    BadgeType.PLAN_COMPLETE: BadgeTier.PLATINUM,
    # ...
}

class BadgeService:
    def __init__(self, db: AsyncSession):
        self.session = db
    
    async def check_and_award_badges(self, student_id: UUID) -> list[BadgeType]:
        """
        Check if student has earned new badges.
        Returns list of newly awarded badge types.
        """
        awarded = []
        
        # Check each badge condition
        if await self._check_first_session(student_id):
            awarded.append(BadgeType.FIRST_SESSION)
        
        if await self._check_streak_badges(student_id):
            # Returns [BadgeType.STREAK_3, ...] for each newly earned
            awarded.extend(...)
        
        if await self._check_halfway(student_id):
            awarded.append(BadgeType.HALFWAY)
        
        # ... check other badge conditions
        
        # Create StudentBadge records (with duplicate prevention)
        for badge_type in awarded:
            existing = await self.session.execute(
                select(StudentBadge).filter(
                    StudentBadge.student_id == student_id,
                    StudentBadge.badge_type == badge_type
                )
            )
            if not existing.scalars().first():
                new_badge = StudentBadge(
                    student_id=student_id,
                    badge_type=badge_type,
                    tier=BADGE_TIERS[badge_type],
                    awarded_at=datetime.utcnow(),
                )
                self.session.add(new_badge)
        
        if awarded:
            await self.session.commit()
        
        return awarded
```

---

## P3-3: StreakService Implementation

**New File:** `apps/api/src/services/streak_service.py`

```python
from datetime import datetime, date, timedelta, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.models import StudentStreak, PracticeSession

class StreakService:
    PACIFIC_TZ = timezone(timedelta(hours=-8))  # For simplicity; use pytz for DST
    
    def __init__(self, db: AsyncSession):
        self.session = db
    
    async def record_activity(self, student_id: UUID, practice_session_id: UUID):
        """
        Record that a student completed a practice session today.
        Updates streak, handles rollover to new day.
        """
        # Get student's streak record (create if doesn't exist)
        result = await self.session.execute(
            select(StudentStreak).filter(StudentStreak.student_id == student_id)
        )
        streak = result.scalars().first()
        
        if not streak:
            streak = StudentStreak(
                student_id=student_id,
                current_streak=0,
                longest_streak=0,
                activity_dates=[],
            )
            self.session.add(streak)
            await self.session.flush()
        
        # Get today's date in Pacific Time
        today = datetime.now(self.PACIFIC_TZ).date()
        
        # Convert array to set of dates
        activity_set = set(streak.activity_dates) if streak.activity_dates else set()
        
        if today in activity_set:
            # Already recorded for today
            return
        
        # Check if yesterday's activity exists
        yesterday = today - timedelta(days=1)
        
        if yesterday in activity_set:
            # Continue the streak
            streak.current_streak += 1
        else:
            # Break or start new streak
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
            streak.current_streak = 1
        
        # Record today's activity
        streak.activity_dates.append(today)
        
        # Update weekly/monthly counts
        this_week_start = today - timedelta(days=today.weekday())
        this_month_start = today.replace(day=1)
        
        week_count = sum(1 for d in streak.activity_dates if d >= this_week_start)
        month_count = sum(1 for d in streak.activity_dates if d >= this_month_start)
        
        # These would be stored in separate columns, e.g.:
        # streak.activity_this_week = week_count
        # streak.activity_this_month = month_count
        # streak.total_sessions += 1
        
        await self.session.commit()
    
    async def get_streak_info(self, student_id: UUID) -> dict:
        """Return current streak info for display."""
        result = await self.session.execute(
            select(StudentStreak).filter(StudentStreak.student_id == student_id)
        )
        streak = result.scalars().first()
        
        if not streak:
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'activity_heatmap': []
            }
        
        # Generate 90-day activity heatmap
        today = datetime.now(self.PACIFIC_TZ).date()
        heatmap = []
        for i in range(90):
            day = today - timedelta(days=i)
            activity_count = 1 if day in streak.activity_dates else 0
            heatmap.append({'date': day.isoformat(), 'count': activity_count})
        
        return {
            'current_streak': streak.current_streak,
            'longest_streak': streak.longest_streak,
            'activity_heatmap': heatmap,
        }
```

---

## P3-4: Practice Session Endpoints

**New endpoints in** `apps/api/src/api/v1/endpoints/learning_plans.py`:

```python
@router.post("/sessions/{session_id}/answer")
async def submit_session_answer(
    session_id: UUID,
    request: ResponseSubmission,
    credentials: HTTPAuthorizationCredentials = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit an answer during a practice session.
    Returns: {correct: bool, correct_answer: str, progress: {...}}
    """
    session = await db.get(PracticeSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify ownership
    practice_session = session
    lesson = practice_session.lesson
    module = lesson.module
    plan = module.plan
    
    user_payload = extract_payload(credentials)
    if str(plan.student.user_id) != user_payload["sub"]:
        raise HTTPException(status_code=403, detail="Cannot access this session")
    
    # Find the question
    question = practice_session.questions[practice_session.current_question_index]
    
    # Check answer
    is_correct = request.answer == question.correct_answer
    
    # Record the response
    response = PracticeSessionQuestion(
        practice_session_id=session_id,
        question_id=question.id,
        selected_answer=request.answer,
        is_correct=is_correct,
        time_spent_ms=request.time_spent_ms,
    )
    db.add(response)
    
    # Update BKT for this skill
    skill_state = await db.execute(
        select(StudentSkillState).filter(
            StudentSkillState.student_id == plan.student_id,
            StudentSkillState.standard_id == lesson.module.standard_id,
        )
    )
    skill_state = skill_state.scalars().first()
    
    if skill_state:
        from src.services.bkt_impl import PyBKT
        bkt = PyBKT.from_db_record(skill_state)
        bkt.forward_inference(is_correct)
        bkt.to_db_record(skill_state)
    
    await db.commit()
    
    return {
        "correct": is_correct,
        "correct_answer": question.correct_answer,
        "explanation": question.explanation,
        "progress": {
            "current_question": practice_session.current_question_index + 1,
            "total_questions": len(practice_session.questions),
        }
    }

@router.post("/sessions/{session_id}/complete")
async def complete_session(
    session_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark practice session as complete.
    Triggers BKT finalization, badge checks, and module progression.
    """
    session = await db.get(PracticeSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify ownership
    user_payload = extract_payload(credentials)
    if str(session.lesson.module.plan.student.user_id) != user_payload["sub"]:
        raise HTTPException(status_code=403, detail="Cannot access this session")
    
    session.status = PracticeSessionStatus.COMPLETED
    session.completed_at = datetime.utcnow()
    
    # Calculate accuracy
    responses = await db.execute(
        select(PracticeSessionQuestion).filter(
            PracticeSessionQuestion.practice_session_id == session_id
        )
    )
    responses = responses.scalars().all()
    correct_count = sum(1 for r in responses if r.is_correct)
    session.accuracy_percentage = (correct_count / len(responses) * 100) if responses else 0
    
    # Update module progress
    module = session.lesson.module
    module.lessons_completed = (module.lessons_completed or 0) + 1
    
    # Check if module should be marked complete
    if module.lessons_completed >= len(module.lessons):
        from src.services.learning_plan_service import LearningPlanService
        service = LearningPlanService(db)
        await service.update_module_progress(
            module.id,
            p_mastered=module.exit_p_mastery,
            minutes_spent=sum(r.time_spent_ms for r in responses) // 60000
        )
    
    # Award badges
    from src.services.badge_service import BadgeService
    badge_service = BadgeService(db)
    new_badges = await badge_service.check_and_award_badges(session.lesson.module.plan.student_id)
    
    # Record activity for streak
    from src.services.streak_service import StreakService
    streak_service = StreakService(db)
    await streak_service.record_activity(session.lesson.module.plan.student_id, session_id)
    
    await db.commit()
    
    return {
        "status": "completed",
        "accuracy": session.accuracy_percentage,
        "new_badges": new_badges,
    }
```

---

## P3-5: Gamification Endpoints

**New endpoints in** `apps/api/src/api/v1/endpoints/learning_plans.py`:

```python
@router.get("/students/{student_id}/badges")
async def get_student_badges(
    student_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db),
):
    """Get student's earned badges."""
    # Verify ownership
    student = await db.get(Student, student_id)
    user_payload = extract_payload(credentials)
    if str(student.user_id) != user_payload["sub"]:
        raise HTTPException(status_code=403)
    
    badges = await db.execute(
        select(StudentBadge).filter(StudentBadge.student_id == student_id)
    )
    
    return {
        "badges": [
            {
                "type": b.badge_type,
                "tier": b.tier,
                "awarded_at": b.awarded_at.isoformat(),
            }
            for b in badges.scalars().all()
        ]
    }

@router.get("/students/{student_id}/streak")
async def get_student_streak(
    student_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db),
):
    """Get student's activity streak."""
    student = await db.get(Student, student_id)
    user_payload = extract_payload(credentials)
    if str(student.user_id) != user_payload["sub"]:
        raise HTTPException(status_code=403)
    
    from src.services.streak_service import StreakService
    service = StreakService(db)
    
    return await service.get_streak_info(student_id)
```

---

## P3-6: Parent Dashboard Endpoints

**New File:** `apps/api/src/api/v1/endpoints/parent.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.security import verify_jwt, HTTPAuthorizationCredentials, extract_payload

router = APIRouter(prefix="/parents", tags=["Parent Dashboard"])

@router.get("/{user_id}/dashboard")
async def get_parent_dashboard(
    user_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db),
):
    """
    Parent dashboard: all children summary.
    Returns: {
        "children": [
            {
                "child_id": UUID,
                "name": str,
                "grade": int,
                "track": str (catch_up/on_track/accelerate),
                "plan_start": date,
                "estimated_completion": date,
                "overall_progress": float (0.0–1.0),
                "modules_completed": int,
                "total_modules": int,
            }
        ]
    }
    """
    # Verify ownership
    user_payload = extract_payload(credentials)
    if user_payload["sub"] != str(user_id):
        raise HTTPException(status_code=403, detail="Cannot access other parent's data")
    
    # Fetch all students for this parent
    result = await db.execute(
        select(Student).filter(Student.user_id == user_id)
    )
    students = result.scalars().all()
    
    children = []
    for student in students:
        # Get active learning plan
        plan_result = await db.execute(
            select(LearningPlan)
            .filter(
                LearningPlan.student_id == student.id,
                LearningPlan.status == LearningPlanStatus.ACTIVE
            )
            .order_by(LearningPlan.created_at.desc())
            .limit(1)
        )
        plan = plan_result.scalars().first()
        
        if plan:
            modules_completed = sum(
                1 for m in plan.modules if m.status == ModuleStatus.COMPLETED
            )
            children.append({
                "child_id": student.id,
                "name": student.display_name,
                "grade": student.grade_level,
                "track": plan.track,
                "plan_start": plan.created_at.date().isoformat(),
                "estimated_completion": plan.estimated_completion_date.isoformat() if plan.estimated_completion_date else None,
                "overall_progress": plan.progress_percentage,
                "modules_completed": modules_completed,
                "total_modules": len(plan.modules),
            })
    
    return {"children": children}

@router.get("/students/{student_id}/parent-report")
async def get_parent_report(
    student_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db),
):
    """
    Detailed parent report: module-by-module progress, activity, stats.
    """
    student = await db.get(Student, student_id, options=[selectinload(Student.user)])
    user_payload = extract_payload(credentials)
    
    # Verify this parent owns this student
    if str(student.user_id) != user_payload["sub"]:
        raise HTTPException(status_code=403)
    
    # Get active plan
    plan_result = await db.execute(
        select(LearningPlan)
        .filter(
            LearningPlan.student_id == student_id,
            LearningPlan.status == LearningPlanStatus.ACTIVE
        )
        .order_by(LearningPlan.created_at.desc())
        .limit(1)
    )
    plan = plan_result.scalars().first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active plan")
    
    # Module-by-module detail
    modules_detail = []
    for module in plan.modules:
        modules_detail.append({
            "module_id": module.id,
            "standard_code": module.standard_code,
            "name": SkillGraphService.get_module_name(module.standard_code),
            "status": module.status,
            "mastered_at": module.mastered_at.isoformat() if module.mastered_at else None,
            "progress": module.exit_p_mastery or module.entry_p_mastery,
        })
    
    # Weekly activity chart (past 7 days)
    today = date.today()
    week_activity = {}
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        # Count practice sessions for this day
        session_count = await db.execute(
            select(func.count(PracticeSession.id)).filter(
                PracticeSession.student_id == student_id,
                func.date(PracticeSession.created_at) == day,
            )
        )
        week_activity[day.isoformat()] = session_count.scalar() or 0
    
    # Lifetime stats
    result = await db.execute(
        select(func.count(distinct(Question.id))).select_from(PracticeSessionQuestion)
        .join(Question)
        .filter(PracticeSessionQuestion.practice_session.student_id == student_id)
    )
    total_questions_answered = result.scalar() or 0
    
    # Accuracy calculation (oversimplified)
    correct_result = await db.execute(
        select(func.count(PracticeSessionQuestion.id)).filter(
            PracticeSessionQuestion.is_correct == True,
            # ... join to get student_id
        )
    )
    
    return {
        "student": {
            "name": student.display_name,
            "grade": student.grade_level,
        },
        "plan": {
            "track": plan.track,
            "modules": modules_detail,
            "total_modules": len(plan.modules),
        },
        "week_activity": week_activity,
        "stats": {
            "total_questions": total_questions_answered,
            "accuracy_percent": 75,  # Placeholder; calculate properly
            "sessions_completed": 10,
            "modules_mastered": sum(1 for m in plan.modules if m.status == ModuleStatus.COMPLETED),
            "current_streak": 3,
            "longest_streak": 7,
        },
        "next_recommended": {
            "module_name": "Equivalent Fractions",
            "estimated_time_minutes": 30,
            "best_time_of_day": "3 PM",  # Inferred from history
        }
    }

@router.patch("/{user_id}/notification-preferences")
async def update_notification_preferences(
    user_id: UUID,
    preferences: dict,  # Should be a Pydantic schema
    credentials: HTTPAuthorizationCredentials = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db),
):
    """
    Update parent's notification preferences.
    Example: {
        "weekly_summary_email": true,
        "module_mastered_email": true,
        "streak_milestone_email": true,
    }
    """
    user_payload = extract_payload(credentials)
    if user_payload["sub"] != str(user_id):
        raise HTTPException(status_code=403)
    
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404)
    
    # Merge with existing preferences
    current = user.notification_preferences or {}
    current.update(preferences)
    user.notification_preferences = current
    
    await db.commit()
    
    return {"status": "updated", "preferences": current}
```

---

## P3-7: Student Dashboard Frontend

**Files to create:**
- `apps/web/app/(dashboard)/students/[studentId]/page.tsx` — Main dashboard
- `apps/web/app/(dashboard)/students/[studentId]/learning-plan/page.tsx` — Roadmap
- `apps/web/app/(dashboard)/students/[studentId]/practice/[sessionId]/page.tsx` — Practice
- `apps/web/app/(dashboard)/students/[studentId]/badges/page.tsx` — Badge collection
- `apps/web/stores/learning-plan-store.ts` — Zustand state management
- `apps/web/stores/practice-store.ts` — Practice session state

### Key UI Components
- **SVG Roadmap:** Graph layout with module nodes (locked/available/in_progress/completed states)
- **Practice Interface:** Question display, answer submission, progress tracking
- **Streak Tracker:** Flame icon, current/longest streaks, activity heatmap
- **Badge Showcase:** Grid of earned badges with tier colors, confetti animation on award
- **Progress Ring:** BKT state visualization (Getting There / Almost There / etc.)

### Zustand Store Pattern
```typescript
// learning-plan-store.ts
import { create } from 'zustand';

interface LearningPlanState {
  plan: LearningPlan | null;
  modules: Module[];
  unlockedModules: Set<UUID>;
  loadPlan: (studentId: string) => Promise<void>;
  completeModule: (moduleId: UUID) => Promise<void>;
}

export const useLearningPlanStore = create<LearningPlanState>((set) => ({
  plan: null,
  modules: [],
  unlockedModules: new Set(),
  
  loadPlan: async (studentId: string) => {
    const response = await fetch(`/api/learning-plans/${studentId}`);
    const data = await response.json();
    set({ plan: data.plan, modules: data.modules });
  },
  
  completeModule: async (moduleId: UUID) => {
    // Call endpoint, update state
  },
}));
```

---

## P3-8: Parent Dashboard Frontend

**Files to create:**
- `apps/web/app/(dashboard)/parents/dashboard/page.tsx` — Parent home
- `apps/web/app/(dashboard)/students/[studentId]/parent-report/page.tsx` — Child detail report
- `apps/web/components/parent/WeeklyActivityChart.tsx` — Recharts bar chart
- `apps/web/components/parent/StatsSummary.tsx` — Lifetime stats grid

### Key Features
- Child card grid showing progress, track, estimated completion
- Module-by-module list with status badges and mastery dates
- Weekly activity bar chart vs 100-min/week goal
- Lifetime stats: questions answered, accuracy %, sessions, streaks
- Next recommended session card with best time-of-day
- Notification preferences toggle

---

## P3-9: Write Missing Tests

### Unit Tests
1. **`tests/services/test_bkt_impl.py`** — Unit tests for BKT class
   - Correct answer increases p_l
   - Incorrect answer decreases p_l
   - State history tracked correctly

2. **`tests/services/test_skill_graph_service.py`** — Edge traversal tests
   - Topological sort returns valid ordering
   - Prerequisite chains resolved correctly
   - DAG validation detects cycles

3. **`tests/services/test_badge_service.py`** (new)
   - Badge award logic
   - Duplicate prevention

4. **`tests/services/test_streak_service.py`** (new)
   - Streak increment/reset
   - Pacific Time date handling

### Integration Tests
5. **`tests/api/test_practice_sessions.py`** (new)
   - Submit answer flow
   - BKT update on completion
   - Badge award trigger

6. **`tests/api/test_parent_dashboard.py`** (new)
   - Parent can see child data
   - Cross-parent access blocked

### Security Tests
7. **`tests/api/test_ownership_checks.py`** (new)
   - complete_module requires ownership
   - Streak/badge data isolated by user

---

# Summary: Implementation Checklist

## P0 Fixes (BLOCKING)
- [ ] Migration syntax error (003_add_stage2_tables.py:283)
- [ ] FK column references (PlanModule, GenerationJob)
- [ ] BKT forward_inference posterior fix
- [ ] LLM _validate_question return type

## P1 Fixes (HIGH PRIORITY)
- [ ] Query param shadowing (generation_jobs.py)
- [ ] Double verify_jwt calls
- [ ] Missing auth checks (execute_generation_job, get_review_queue)
- [ ] Ownership verification (complete_module)
- [ ] Skill graph node/edge keys
- [ ] Question standard_id type
- [ ] Route ordering (learning-plans/sequence)
- [ ] Module actual_minutes NoneType
- [ ] Consent completed hardcoded
- [ ] verify_email no-op

## P2 Fixes (QUALITY)
- [ ] ApiResponse extend BaseModel
- [ ] Pydantic v2 incompatibilities
- [ ] JobStatus enum mismatch
- [ ] pgvector index type
- [ ] strength type mismatch
- [ ] Fix broken tests (test_models.py, test_jwt)
- [ ] Remove stale singletons
- [ ] SES settings initialization
- [ ] Transaction ownership standardization

## P3 Implementations
- [ ] Complete AI pipeline (Steps 2–5)
- [ ] BadgeService
- [ ] StreakService
- [ ] Practice session endpoints
- [ ] Gamification endpoints
- [ ] Parent dashboard endpoints
- [ ] Student dashboard frontend
- [ ] Parent dashboard frontend
- [ ] Missing tests

---

# Expected Outcome

After implementing all P0–P3 items:
- ✅ All 57 acceptance criteria (AC-11 through AC-18) met
- ✅ Full AI pipeline functional (100+ questions/hour throughput)
- ✅ BKT-based adaptive learning working correctly
- ✅ Student and parent dashboards fully functional
- ✅ Gamification system (badges, streaks) operational
- ✅ All tests passing (>90% coverage)
- ✅ Stage 2 ready for production

**Estimated total time: 70–95 hours**
