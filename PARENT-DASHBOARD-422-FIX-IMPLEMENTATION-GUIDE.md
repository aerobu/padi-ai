# Implementation Guide: Fix Parent Dashboard 422 Errors

**For:** Implementation agent (Qwen)
**Scope:** `apps/api/` — surgical fix, no refactoring
**Estimated changes:** 1 source file, 2 test files, 1 doc file deletion

---

## 0. Read this first — guardrails

Before touching code, internalize these rules. They prevent the most likely ways this fix can go wrong:

1. **Do exactly what this guide says. Do not add features, refactor, or "improve" unrelated code.** A focused fix is the goal.
2. **Do not modify any endpoint file** (`apps/api/src/api/v1/endpoints/*.py`). The bug is not there.
3. **Do not change Pydantic schemas** (`apps/api/src/schemas/parent.py`). The `TEST_VALIDATION_ERRORS.md` file blames Pydantic defaults — **that analysis is wrong**. Ignore it.
4. **Do not widen the scope** to `generation_jobs.py` or `learning_plans.py`. They have related but separate issues that are explicitly out of scope.
5. **After the fix, tests must assert exact status codes (`== 200`, `== 403`), not `in [200, 422]`.** The `422` tolerance in current tests is a workaround that masked the real bug and must be removed.
6. **Never use `--no-verify` or skip hooks.** If something fails, fix the underlying cause.

---

## 1. Why this fix is needed (context)

### Symptom
Four parent dashboard endpoints return HTTP 422 in tests:
- `GET  /api/v1/parents/{user_id}/dashboard`
- `GET  /api/v1/parents/{user_id}/report`
- `GET  /api/v1/parents/{user_id}/preferences`
- `PUT  /api/v1/parents/{user_id}/preferences`

Every response body is:
```json
{"detail":[{"type":"missing","loc":["body"],"msg":"Field required","input":null}]}
```

### Why it's happening (root cause)

**File:** `apps/api/src/core/security.py`, lines 32-34:

```python
async def verify_jwt(
    credentials: HTTPAuthorizationCredentials,   # ← BUG: no Depends(security)
) -> dict:
```

`HTTPAuthorizationCredentials` is a Pydantic model (imported from `fastapi.security`). When FastAPI introspects a dependency function, any Pydantic-typed parameter **that is not explicitly wired to `Depends(...)`, `Security(...)`, `Query(...)`, `Path(...)`, etc.** is treated as a **required JSON body parameter**.

So every route that transitively depends on `verify_jwt` ends up declaring an implicit body param of shape `HTTPAuthorizationCredentials`. FastAPI then rejects every incoming request with `{"loc": ["body"], "type": "missing"}` because the request body doesn't contain the `{scheme, credentials}` fields it expects.

**Why only parent endpoints fail:** other endpoint files (`students.py`, `consent.py`, `assessments.py`) declare auth directly in the endpoint signature using `credentials: HTTPAuthorizationCredentials = Depends(security)`, so they bypass `verify_jwt`'s broken signature. Only `parent.py` routes through `get_user_from_credentials` → `Depends(verify_jwt)`, exercising the bug.

### Two secondary bugs (discovered while investigating)

These did not cause the 422, but they currently prevent tests from passing even after the primary fix:

- **JWT mocking is a no-op.** `tests/conftest.py` uses `patch("src.core.security.verify_jwt")`, but endpoint modules do `from src.core.security import verify_jwt` followed by `Depends(verify_jwt)`. `Depends` captures the *function object*, not the module attribute — so patching the module attribute after import has zero effect. FastAPI's `app.dependency_overrides[verify_jwt] = ...` is the correct mechanism.
- **DB mocking has the same no-op bug.** Same pattern on `get_db`. Same fix: `app.dependency_overrides[get_db] = ...`.
- **Missing `await`** on four `async_db_session.commit()` / `.flush()` calls in `test_parent_dashboard.py` — these produce `RuntimeWarning: coroutine … was never awaited`.

### Desired end state

- `verify_jwt` correctly declares its credentials parameter as a `Depends(security)` injection.
- Tests use `app.dependency_overrides` (not `unittest.mock.patch`) to replace JWT and DB dependencies.
- All async session calls are properly awaited.
- All 7 tests in `test_parent_dashboard.py` pass with exact status-code assertions.
- No regressions in other test files (`students`, `consent`, `assessments`, `security`).

---

## 2. Step-by-step implementation

### Step 1 — Fix `verify_jwt` signature

**File:** `apps/api/src/core/security.py`

**What:** Wire `credentials` to `Depends(security)` via `Annotated`.

**Why:** This is the single line that causes all four 422 errors. With this change, FastAPI knows to extract `HTTPAuthorizationCredentials` from the `Authorization` header (using the `HTTPBearer` instance already declared at line 16) instead of treating it as a request body.

**How:**

**2.1** Update the imports at the top of the file. Find:

```python
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
```

Replace with:

```python
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
```

(Note: `Optional` was already imported from `typing` at line 8 — merge into the single `from typing import` line and remove the old `from typing import Optional` line.)

**2.2** Update the `verify_jwt` signature at lines 32-34. Find:

```python
async def verify_jwt(
    credentials: HTTPAuthorizationCredentials,
) -> dict:
```

Replace with:

```python
async def verify_jwt(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> dict:
```

Use `Optional[...]` because `security = HTTPBearer(auto_error=False)` (line 16) means FastAPI will pass `None` when no `Authorization` header is present. The existing `if not credentials:` branch at line 47 already handles this case by raising 401 — do not touch that branch.

**2.3** Do not change anything else in this file. The `_jwks_client`, `get_jwks_client`, `create_jwt_response`, `generate_nonce`, and `validate_email` functions stay as-is.

### Step 2 — Replace JWT patch fixtures with dependency overrides in conftest.py

**File:** `apps/api/tests/conftest.py`

**What:** Replace all six `patch("src.core.security.verify_jwt")` fixtures with fixtures that use `app.dependency_overrides[verify_jwt]`.

**Why:** `patch()` on the module attribute does not affect `Depends(verify_jwt)` references that were captured at import time. `app.dependency_overrides` is FastAPI's native override mechanism and is the only way that actually works. Without this change, tests will contact the real Auth0 JWKS endpoint and fail with 401.

**How:**

**2.1** Add these imports near the top of the file, immediately after the existing `from src.main import app` line (currently line 45):

```python
from src.core.security import verify_jwt
from src.core.database import get_db
```

**2.2** Immediately before the first JWT fixture (currently `mock_jwt_as_admin` at line 128), add this helper:

```python
def _override_verify_jwt(payload: dict):
    """Return an async callable suitable for app.dependency_overrides[verify_jwt]."""
    async def _mock_verify_jwt():
        return payload
    return _mock_verify_jwt
```

**2.3** Replace each of the six JWT mock fixtures. Current code at lines 127-162 looks like:

```python
@pytest.fixture
def mock_jwt_as_admin():
    """Mock JWT validation as admin user."""
    with patch("src.core.security.verify_jwt") as mock_validate:
        mock_validate.return_value = {
            "sub": "admin-user-id",
            "email": "admin@example.com",
            "email_verified": True,
            "role": "admin"
        }
        yield mock_validate


@pytest.fixture
def mock_jwt_as_user():
    ...


@pytest.fixture
def mock_jwt_validation():
    ...
```

Replace the whole block from line 127 through line 162 (inclusive) with:

```python
@pytest.fixture
def mock_jwt_as_admin():
    """Override verify_jwt dependency to return an admin user payload."""
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "admin-user-id",
        "email": "admin@example.com",
        "email_verified": True,
        "role": "admin",
    })
    yield
    app.dependency_overrides.pop(verify_jwt, None)


@pytest.fixture
def mock_jwt_as_user():
    """Override verify_jwt dependency to return a regular user payload."""
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "test-user-id",
        "email": "test@example.com",
        "email_verified": True,
        "role": "parent",
    })
    yield
    app.dependency_overrides.pop(verify_jwt, None)


@pytest.fixture
def mock_jwt_validation():
    """Override verify_jwt dependency for tests that need any authed user."""
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "test-user-id",
        "email": "test@example.com",
        "email_verified": True,
    })
    yield
    app.dependency_overrides.pop(verify_jwt, None)
```

**2.4** Replace the `mock_jwt_as_parent`, `mock_jwt_as_teacher`, and second `mock_jwt_as_admin` fixtures (currently lines 311-347). The block currently looks like:

```python
@pytest.fixture
def mock_jwt_as_parent():
    """Mock JWT validation as parent user."""
    with patch("src.core.security.verify_jwt") as mock:
        ...


@pytest.fixture
def mock_jwt_as_teacher():
    ...


@pytest.fixture
def mock_jwt_as_admin():
    ...
```

Replace lines 311-347 with:

```python
@pytest.fixture
def mock_jwt_as_parent():
    """Override verify_jwt dependency to return a parent user payload."""
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "parent-1",
        "email": "parent@example.com",
        "email_verified": True,
        "role": "parent",
    })
    yield
    app.dependency_overrides.pop(verify_jwt, None)


@pytest.fixture
def mock_jwt_as_teacher():
    """Override verify_jwt dependency to return a teacher user payload."""
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "teacher-1",
        "email": "teacher@example.com",
        "email_verified": True,
        "role": "teacher",
    })
    yield
    app.dependency_overrides.pop(verify_jwt, None)
```

**Note:** the original file defined `mock_jwt_as_admin` twice (once at line 128, once at line 337). The second definition shadowed the first. After this fix there should be exactly ONE `mock_jwt_as_admin` fixture (the one in step 2.3). Delete the duplicate — do not keep two.

### Step 3 — Replace DB patch fixture with dependency override in conftest.py

**File:** `apps/api/tests/conftest.py`, `test_api_client` fixture (currently lines 255-271)

**What:** Replace the `patch("src.core.database.get_db")` block with `app.dependency_overrides[get_db]`.

**Why:** Same rationale as Step 2 — `Depends(get_db)` captures the function reference at import time, so patching the module attribute doesn't work. Using `dependency_overrides` is the supported FastAPI mechanism.

**How:** Find the current `test_api_client` fixture:

```python
@pytest.fixture
def test_api_client(async_db_session):
    """
    Create TestClient with mocked database session for API tests.
    This allows testing endpoints without full database setup.
    """
    from starlette.testclient import TestClient
    from unittest.mock import AsyncMock

    # Mock the database dependency
    with patch("src.core.database.get_db") as mock_get_db:
        async def mock_db_generator():
            yield async_db_session

        mock_get_db.return_value = mock_db_generator()
        with TestClient(app) as client:
            yield client
```

Replace with:

```python
@pytest.fixture
def test_api_client(async_db_session):
    """Create TestClient with get_db overridden to yield the test session."""
    from starlette.testclient import TestClient

    async def _override_get_db():
        yield async_db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)
```

### Step 4 — Apply the same DB override pattern in test_parent_dashboard.py

**File:** `apps/api/tests/api/test_parent_dashboard.py`

**What:** Update the two per-class `test_client` fixtures to use `app.dependency_overrides[get_db]`.

**Why:** Both fixtures use the same broken `patch("src.core.database.get_db")` pattern. They must be fixed identically.

**How:**

**4.1** Update imports at the top of the file. Current imports (lines 1-6):

```python
"""
Tests for Parent Dashboard endpoints.
"""
import pytest
import pytest_asyncio
from unittest.mock import patch
```

Replace with:

```python
"""
Tests for Parent Dashboard endpoints.
"""
import pytest
import pytest_asyncio

from src.core.database import get_db
from src.main import app
```

The `unittest.mock.patch` import is no longer needed — delete it.

**4.2** Replace the first `test_client` fixture (currently lines 13-25):

```python
    @pytest_asyncio.fixture
    async def test_client(self, async_db_session):
        """Create TestClient with mocked database session."""
        from starlette.testclient import TestClient
        from src.main import app

        with patch("src.core.database.get_db") as mock_get_db:
            async def mock_db_generator():
                yield async_db_session

            mock_get_db.return_value = mock_db_generator()
            with TestClient(app, base_url="http://test") as client:
                yield client
```

With:

```python
    @pytest_asyncio.fixture
    async def test_client(self, async_db_session):
        """Create TestClient with get_db overridden to yield the test session."""
        from starlette.testclient import TestClient

        async def _override_get_db():
            yield async_db_session

        app.dependency_overrides[get_db] = _override_get_db
        try:
            with TestClient(app, base_url="http://test") as client:
                yield client
        finally:
            app.dependency_overrides.pop(get_db, None)
```

**4.3** Replace the second `test_client` fixture at lines 133-145 with the exact same block (it belongs to `TestParentDashboardWithChildren` — the body is identical).

### Step 5 — Add missing `await` on async session calls

**File:** `apps/api/tests/api/test_parent_dashboard.py`

**What:** Add `await` to four calls that return coroutines.

**Why:** `AsyncSession.commit()` and `AsyncSession.flush()` are coroutines. Calling them without `await` schedules nothing, produces `RuntimeWarning: coroutine was never awaited`, and means DB changes are not actually persisted before the endpoint call.

**How:** Make these four edits. Each edit is a single-word addition of `await` on the indicated line.

| Line | Before | After |
|------|--------|-------|
| 92 | `        async_db_session.commit()` | `        await async_db_session.commit()` |
| 117 | `        async_db_session.commit()` | `        await async_db_session.commit()` |
| 216 | `        async_db_session.flush()` | `        await async_db_session.flush()` |
| 229 | `        async_db_session.commit()` | `        await async_db_session.commit()` |

Do **not** modify lines 162, 174, or 186 — those already have `await` and are correct.

### Step 6 — Tighten status-code assertions and remove wrong-theory comments

**File:** `apps/api/tests/api/test_parent_dashboard.py`

**What:** Change `assert response.status_code in [200, 422]` to `assert response.status_code == 200` in two places, and delete the misleading comments above them.

**Why:** The `422` tolerance was a workaround that masked this bug from CI. After the fix, 422 should never occur on a happy-path test. Keeping the tolerance would mask future regressions of the same class of bug.

**How:**

**6.1** Replace lines 34-37:

```python
        # 422 - FastAPI schema validation issue with parent endpoints
        # The GET endpoint works but returns 422 due to how Pydantic v2 handles defaults
        # This is a known issue with FastAPI + Pydantic v2 when schema has defaults
        assert response.status_code in [200, 422]
```

With:

```python
        assert response.status_code == 200
```

**6.2** Replace lines 60-61:

```python
        # TODO: Fix 422 validation issue
        assert response.status_code in [200, 422]
```

With:

```python
        assert response.status_code == 200
```

**6.3** Also remove the two debug `print` statements at lines 57-58 — they were scaffolding for investigating the 422 and are no longer needed:

```python
        print(f"PUT Response status: {response.status_code}")
        print(f"PUT Response body: {response.text}")
```

Delete both lines.

### Step 7 — Delete the misleading analysis doc

**File:** `apps/api/TEST_VALIDATION_ERRORS.md`

**What:** Delete the file.

**Why:** It documents a wrong root cause (Pydantic v2 defaults). Leaving it in the repo will mislead future readers who search for "422" or "NotificationPreferences". The fix is now encoded in code; there is no ongoing value in keeping the wrong analysis.

**How:**

```bash
cd /Users/aerobu/claude_code_projects/padi_ai
rm apps/api/TEST_VALIDATION_ERRORS.md
```

---

## 3. Verification

Run every step from the `apps/api/` directory. Do not skip any.

### 3.1 Parent dashboard tests pass with exact status codes

```bash
cd apps/api
pytest tests/api/test_parent_dashboard.py -v
```

**Expected:** All 7 tests pass (PDT-001 through PDT-007). No `422` anywhere in the output.

### 3.2 No "coroutine was never awaited" warnings

```bash
pytest tests/api/test_parent_dashboard.py -W error::RuntimeWarning
```

**Expected:** 0 warnings, all tests still pass. If any `RuntimeWarning` fires, you missed an `await` — check Step 5 again.

### 3.3 Regression check — other endpoint tests still pass

```bash
pytest tests/api/ -v
```

**Expected:** No test that was previously passing now fails. The `verify_jwt` signature change should be transparent to `students`, `consent`, and `assessments` tests because they use `Depends(security)` directly, not `Depends(verify_jwt)`.

### 3.4 Security contract still holds

```bash
pytest tests/test_security.py -v
```

**Expected:** All security tests pass. If any fail, inspect whether they mock `verify_jwt`'s signature — they may also need migration to `dependency_overrides`. Report this rather than guessing.

### 3.5 Manual smoke — unauthenticated request returns 401, not 422

In one terminal:

```bash
cd apps/api
uvicorn src.main:app --reload
```

In another:

```bash
curl -i http://localhost:8000/api/v1/parents/parent-1/dashboard
```

**Expected:**
```
HTTP/1.1 401 Unauthorized
...
{"detail":"Authentication credentials not provided"}
```

If you see `HTTP/1.1 422 Unprocessable Entity`, Step 1 was not applied correctly — re-check `verify_jwt`'s signature.

Stop the uvicorn process when done (`Ctrl+C`).

### 3.6 Final success checklist

All five must be true before declaring done:

- [ ] Step 3.1: all 7 `test_parent_dashboard.py` tests pass.
- [ ] Step 3.2: no `RuntimeWarning` emitted.
- [ ] Step 3.3: no regressions in `tests/api/`.
- [ ] Step 3.4: `tests/test_security.py` passes.
- [ ] Step 3.5: unauthenticated request returns 401, not 422.

---

## 4. What is deliberately out of scope

Do **not** fix these as part of this work — they are separate concerns:

- `apps/api/src/api/v1/endpoints/generation_jobs.py:41` and `apps/api/src/api/v1/endpoints/learning_plans.py:21` both declare `credentials: HTTPAuthorizationCredentials = Depends(verify_jwt)`, passing `verify_jwt` (which returns `dict`) where a `HTTPAuthorizationCredentials` is typed. These have a type mismatch that's independent of the 422 bug. Flag them in your final summary but do not touch them.
- The duplicate `mock_jwt_as_admin` fixture at the bottom of conftest.py: Step 2 already handles this as a side effect (you're replacing the second one outright, and keeping the first one from Step 2.3).
- Other `STAGE*` markdown docs in the repo root: leave them alone.

---

## 5. Files touched — summary

| File | Action | Lines affected |
|------|--------|----------------|
| `apps/api/src/core/security.py` | Edit imports + `verify_jwt` signature | ~4 lines |
| `apps/api/tests/conftest.py` | Add 2 imports + 1 helper; replace 6 JWT fixtures + 1 DB fixture | ~100 lines |
| `apps/api/tests/api/test_parent_dashboard.py` | Replace imports; replace 2 fixtures; add 4 `await`s; tighten 2 asserts; remove 2 print lines and ~5 comment lines | ~50 lines |
| `apps/api/TEST_VALIDATION_ERRORS.md` | Delete | — |

---

## 6. When you're done

Report back with:
1. Output of `pytest tests/api/test_parent_dashboard.py -v` (the whole thing).
2. Confirmation that Section 3.6 checklist is all checked.
3. A note if you hit anything unexpected — do not silently adapt the plan.
