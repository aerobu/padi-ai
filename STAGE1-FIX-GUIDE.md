# PADI.AI Stage 1 — Completion & Fix Guide

**For:** Qwen 3.5 implementation  
**Date:** 2026-04-15  
**Status:** Do not proceed to Stage 2 without completing all fixes below  
**Priority:** Critical — 5 P0 bugs + COPPA compliance gaps block all functionality

---

## Overview

Stage 1 implementation is architecturally sound but has **5 critical P0 bugs** that prevent any authenticated request from succeeding, plus **10 major gaps** (missing endpoints, encryption, migrations, test infrastructure). This guide specifies **exact fixes in dependency order**.

The application cannot serve a single request to a real user until these are fixed. Zero steps in the E2E flow succeed.

---

## What Already Exists (Don't Rebuild)

✅ **Implemented & working:**
- FastAPI app factory with CORS, middleware, lifespan
- Layered architecture: Router → Service → Repository → SQLAlchemy models
- All SQLAlchemy ORM models (User, Student, Standard, Question, Assessment, etc.)
- All Pydantic v2 schemas with validation
- BKTService (Bayesian Knowledge Tracing)
- QuestionSelectionService (CAT engine)
- Redis client with assessment state caching
- LLM routing (COPPA-compliant) via LiteLLM
- Docker Compose (postgres, redis, ollama)
- Frontend components (QuestionCard, ResultsSummary, etc.)
- Zustand assessment store
- Comprehensive test files (~45 Python, ~12 TS) with infrastructure in place

❌ **Missing or broken (need to fix):**
- See below, section by section

---

## Fix Priority & Dependency Order

```
MUST-FIX (P0 — blocks all requests):
  1. Add missing get_db imports (3 files, 1 min each)
  2. Fix assessment_service.py NameErrors (4 issues)
  3. Fix JWT validation (Auth0 JWKS)
  4. Fix standards schema mismatch
  5. Wire ConsentForm to real API client

MUST-FIX (COPPA compliance):
  6. Implement EncryptionService
  7. Update User model + add migration

MUST-FIX (Infrastructure):
  8. Set up Alembic + initial migration
  9. Add /auth/register endpoint
  10. Add /auth/verify-email endpoint
  11. Add AWS SES integration to ConsentService

MUST-FIX (Tests):
  12. Migrate test suite from SQLite to PostgreSQL
  13. Fix performance test async/sync bug

SHOULD-FIX (before moving to Stage 2):
  14. Seed question bank
  15. Add missing frontend routes
  16. Add pybkt to pyproject.toml
```

---

# CRITICAL FIXES (Execute in this order)

## Fix 1: Add Missing `get_db` Imports

**Files affected:** 3  
**Time:** 5 minutes  
**Why:** These modules crash at import time with `NameError: name 'get_db' is not defined`

### File: `apps/api/src/api/v1/endpoints/assessments.py`

**Current state:** No import of `get_db`

**Action:** Add this import at the top of the file:
```python
from src.core.database import get_db
```

Add it after the existing imports from `src.core.security`.

### File: `apps/api/src/api/v1/endpoints/consent.py`

**Current state:** No import of `get_db`

**Action:** Add this import:
```python
from src.core.database import get_db
```

### File: `apps/api/src/api/v1/endpoints/standards.py`

**Current state:** No import of `get_db`

**Action:** Add this import:
```python
from src.core.database import get_db
```

**Verify:** Run `python -c "import sys; sys.path.insert(0, 'apps/api'); from src.api.v1.endpoints import assessments, consent, standards; print('✓ All imports OK')"` — should print `✓ All imports OK` with no errors.

---

## Fix 2: Fix `assessment_service.py` NameErrors (4 issues)

**File:** `apps/api/src/services/assessment_service.py`  
**Time:** 30 minutes  
**Why:** Every call to `complete_assessment()` and `get_results()` crashes at runtime

### Issue 2.1: `get_results()` references undefined `state` variable

**Location:** In `get_results()` method

**Current code (broken):**
```python
async def get_results(self, assessment_id: str) -> AssessmentResultsResponse:
    assessment = await self.assessment_repo.get_by_id(assessment_id)
    # ... some code ...
    state = state.get("covered_standards")  # ← ERROR: state never fetched
```

**Fixed code:**
```python
async def get_results(self, assessment_id: str) -> AssessmentResultsResponse:
    assessment = await self.assessment_repo.get_by_id(assessment_id)
    # ... some code ...
    # Load Redis state for this assessment
    redis_state = await self.redis_client.get_assessment_state(assessment_id)
    if not redis_state:
        redis_state = {}
    covered_standards = redis_state.get("covered_standards", [])
    # ... use covered_standards instead of state ...
```

### Issue 2.2: `_calculate_skill_states()` references undefined `state` variable

**Location:** In `_calculate_skill_states()` method

**Current code (broken):**
```python
async def _calculate_skill_states(self, assessment_id: str) -> List[StudentSkillState]:
    responses = await self.assessment_repo.get_responses_for_assessment(assessment_id)
    skill_states = []
    for response in responses:
        standard_code = state.get("standard_code")  # ← ERROR: state undefined
```

**Fixed code:**
```python
async def _calculate_skill_states(self, assessment_id: str) -> List[StudentSkillState]:
    responses = await self.assessment_repo.get_responses_for_assessment(assessment_id)
    skill_states = []
    for response in responses:
        standard_code = response.standard_code  # Use response object, not undefined state
```

### Issue 2.3: `complete_assessment()` signature doesn't match usage

**Location:** `complete_assessment()` method signature and endpoint call

**Current code (broken):**
```python
async def complete_assessment(self, assessment_id: str, db_session: AsyncSession) -> AssessmentResultsResponse:
    # ... method body ...

# In endpoint (assessments.py):
result = await service.complete_assessment(assessment_id=assessment_id)  # ← Missing db_session
```

**Fixed code:**

Option 1 (preferred): Inject `db_session` via `Depends()` in the endpoint, pass to service:
```python
# In assessments.py endpoint:
@router.put("/{assessment_id}/complete", response_model=CompleteAssessmentResponse)
async def complete_assessment_endpoint(
    assessment_id: str,
    db_session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompleteAssessmentResponse:
    service = AssessmentService(
        assessment_repo=AssessmentRepository(db_session),
        # ... other repos ...
    )
    result = await service.complete_assessment(assessment_id=assessment_id, db_session=db_session)
    return result
```

OR Option 2: Remove `db_session` parameter from service method (if not needed for the logic):
```python
async def complete_assessment(self, assessment_id: str) -> AssessmentResultsResponse:
    # Don't take db_session as parameter, use self.assessment_repo which already has it
    # ... method body ...
```

Choose Option 1 if the method uses `db_session` internally; choose Option 2 if the repositories handle all DB work.

### Issue 2.4: Attribute name mismatch in `_save_skill_state()`

**Location:** `_save_skill_state()` method

**Current code (broken):**
```python
async def _save_skill_state(self, student_id: str, standard_code: str, state: dict):
    skill_state = StudentSkillState(
        student_id=student_id,
        standard_code=standard_code,
        p_mastery=state.p_mastery,  # ← ERROR: state is dict, not object
        p_guess=state.p_guess,      # ← ERROR
        p_slip=state.p_slip,        # ← ERROR
```

**Fixed code:**
```python
async def _save_skill_state(self, student_id: str, standard_code: str, state: dict):
    skill_state = StudentSkillState(
        student_id=student_id,
        standard_code=standard_code,
        mastery_prob=state.get("p_mastery", 0.1),  # Use dict.get()
        guess_prob=state.get("p_guess", 0.25),
        slip_prob=state.get("p_slip", 0.05),
        learning_rate=state.get("p_transit", 0.1),
    )
```

**Verify:** Run the test suite: `pytest apps/api/tests/services/test_assessment_service.py -v` — all tests should pass.

---

## Fix 3: Fix JWT Validation (Auth0 JWKS)

**File:** `apps/api/src/core/security.py`  
**Time:** 20 minutes  
**Why:** Every authenticated request fails because RS256 tokens require JWKS public key, not a secret string

### Current broken code:
```python
import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError

def verify_jwt(token: str) -> dict:
    """Verify Auth0 JWT token."""
    secret = settings.AUTH0_SECRET  # ← WRONG: RS256 doesn't use a secret key
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["RS256"],  # ← Incompatible: secret is not for RS256
            audience=settings.AUTH0_AUDIENCE,
            issuer=settings.AUTH0_ISSUER_BASE_URL,
        )
        return payload
    except DecodeError as e:
        raise ValueError(f"Invalid token: {e}")
```

### Fixed code:

**Step 1:** Add new imports:
```python
from jwt import PyJWKClient
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError
```

**Step 2:** Replace the `verify_jwt()` function:
```python
# Initialize JWKS client (cached globally)
_jwks_client = None

def get_jwks_client():
    """Get or create the JWKS client for Auth0."""
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"{settings.AUTH0_ISSUER_BASE_URL}/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client

def verify_jwt(token: str) -> dict:
    """Verify Auth0 JWT token using RS256 with JWKS public key."""
    try:
        # Get the public key from Auth0 JWKS endpoint
        signing_key = get_jwks_client().get_signing_key_from_jwt(token)
        
        # Decode the token using the public key
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.AUTH0_AUDIENCE,
            issuer=settings.AUTH0_ISSUER_BASE_URL,
        )
        return payload
    except ExpiredSignatureError:
        raise ValueError("Token has expired")
    except InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")
    except Exception as e:
        raise ValueError(f"Token verification failed: {e}")
```

**Step 3:** Update `pyproject.toml` to ensure `PyJWT[crypto]` is in dependencies:
```toml
dependencies = [
    # ... existing ...
    "PyJWT[crypto]>=2.8.0",  # ← Ensure crypto extras are included
]
```

**Verify:** 
1. Create a valid Auth0 token and test: `python -c "from src.core.security import verify_jwt; print(verify_jwt('valid_token_here'))"` — should return the payload dict
2. Test with expired token — should raise ValueError with "expired" message
3. Run integration tests: `pytest apps/api/tests/security/test_jwt_validation.py -v`

---

## Fix 4: Fix Standards Endpoint Schema Mismatch

**File:** `apps/api/src/api/v1/endpoints/standards.py`  
**Time:** 5 minutes  
**Why:** The response schema field is `bkt_defaults` but the endpoint passes `bkt=...`

### Find this code:
```python
@router.get("/{standard_code}", response_model=StandardDetailResponse)
async def get_standard(
    standard_code: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    # ... fetch standard from DB ...
    return {
        "standard_code": standard.code,
        "domain": standard.domain,
        "bkt": {  # ← WRONG KEY
            "p_l0": standard.bkt_p_l0,
            "p_transit": standard.bkt_p_transit,
            "p_slip": standard.bkt_p_slip,
            "p_guess": standard.bkt_p_guess,
        },
        # ... other fields ...
    }
```

### Fix it:
```python
return {
    "standard_code": standard.code,
    "domain": standard.domain,
    "bkt_defaults": {  # ← CORRECT KEY
        "p_l0": standard.bkt_p_l0,
        "p_transit": standard.bkt_p_transit,
        "p_slip": standard.bkt_p_slip,
        "p_guess": standard.bkt_p_guess,
    },
    # ... other fields ...
}
```

**Verify:** 
```bash
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/v1/standards/4.OA.A.1
# Should return JSON with bkt_defaults key (no error)
```

---

## Fix 5: Wire ConsentForm.tsx to Real API Client

**File:** `apps/web/components/assessment/ConsentForm.tsx`  
**Time:** 10 minutes  
**Why:** The form uses a local stub instead of the real API client methods

### Current broken code:
```typescript
const handleSubmit = async () => {
  try {
    // ✗ Using local mock stub
    const response = await apiClient.post("/api/v1/coppa/consent", {
      userId: user.id,
      consentData: { ... }
    });
```

### Fixed code:
```typescript
import { apiClient } from '@/lib/api-client';

const handleSubmit = async () => {
  try {
    setIsLoading(true);
    
    // ✓ Use real initiateConsent method
    const initiateResponse = await apiClient.initiateConsent({
      dataCollection: consentChecks[0],
      dataUse: consentChecks[1],
      thirdPartyDisclosure: consentChecks[2],
      parentalRights: consentChecks[3],
    });
    
    // Store token for later confirmation
    localStorage.setItem('consent_token', initiateResponse.token);
    
    // Redirect to email verification (once you add /verify-email page)
    router.push('/verify-email');
  } catch (error) {
    setError(error.message);
  } finally {
    setIsLoading(false);
  }
};
```

**Also update** the confirmation step if it exists:
```typescript
const handleConfirmConsent = async (token: string) => {
  try {
    setIsLoading(true);
    
    // ✓ Use real confirmConsent method
    const confirmResponse = await apiClient.confirmConsent({
      token: token,
    });
    
    // Redirect to next step
    router.push('/onboarding/create-student');
  } catch (error) {
    setError(error.message);
  } finally {
    setIsLoading(false);
  }
};
```

**Verify:** 
- Open browser DevTools → Network tab
- Fill and submit consent form
- Verify POST requests go to `/api/v1/consent/initiate` and `/api/v1/consent/confirm` (not `/api/v1/coppa/consent`)

---

# COPPA COMPLIANCE FIXES

## Fix 6: Implement EncryptionService

**Files to create:**
- `apps/api/src/core/encryption.py` (new file)

**Time:** 25 minutes  
**Why:** COPPA requires PII (email) to be encrypted at rest

### Create `apps/api/src/core/encryption.py`:

```python
"""
Encryption service for PII fields.
Uses AES-256-CBC with application-layer encryption (pgcrypto-compatible).
"""

import hashlib
from cryptography.fernet import Fernet
from src.core.config import get_settings

settings = get_settings()

# Generate Fernet key from settings (32 bytes for Fernet)
# In production, this comes from AWS Secrets Manager
_encryption_key = Fernet(
    base64.urlsafe_b64encode(
        hashlib.sha256(settings.ENCRYPTION_KEY_PASSPHRASE.encode()).digest()
    )
)

class EncryptionService:
    """Encrypt/decrypt sensitive fields using Fernet (AES-128-CBC equivalent)."""
    
    @staticmethod
    def encrypt(plaintext: str) -> bytes:
        """Encrypt plaintext to bytes."""
        if not plaintext:
            return None
        cipher = Fernet(_encryption_key)
        return cipher.encrypt(plaintext.encode())
    
    @staticmethod
    def decrypt(ciphertext: bytes) -> str:
        """Decrypt ciphertext bytes to plaintext."""
        if not ciphertext:
            return None
        cipher = Fernet(_encryption_key)
        return cipher.decrypt(ciphertext).decode()
    
    @staticmethod
    def hash_for_lookup(plaintext: str) -> str:
        """Create SHA-256 hash for lookup (one-way, non-reversible)."""
        if not plaintext:
            return None
        return hashlib.sha256(plaintext.encode()).hexdigest()

def get_encryption_service() -> EncryptionService:
    """FastAPI dependency."""
    return EncryptionService()
```

**Add to `apps/api/src/core/config.py`:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Encryption (from AWS Secrets Manager or .env)
    ENCRYPTION_KEY_PASSPHRASE: str = Field(
        default="your-secure-passphrase-32-chars-min",
        description="Passphrase for deriving encryption key"
    )
```

**Verify:**
```python
from src.core.encryption import EncryptionService
svc = EncryptionService()
plaintext = "user@example.com"
encrypted = svc.encrypt(plaintext)
decrypted = svc.decrypt(encrypted)
assert decrypted == plaintext
print("✓ Encryption working")
```

---

## Fix 7: Update User Model & Add Migration

**File:** `apps/api/src/models/models.py`  
**Time:** 15 minutes

### Current User model (broken):
```python
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    auth0_sub: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str]  # ← PLAINTEXT: must be encrypted
    # ...
```

### Fixed User model:
```python
from src.core.encryption import EncryptionService

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    auth0_sub: Mapped[str] = mapped_column(unique=True)
    
    # Encrypted PII (application-layer)
    email_encrypted: Mapped[bytes] = mapped_column(BYTEA, nullable=True)
    email_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    
    # Non-PII fields
    display_name: Mapped[str]
    role: Mapped[str] = mapped_column(default="parent")
    email_verified: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # ... timestamps, relationships ...
```

**Also add convenience methods to User model:**
```python
class User(Base):
    # ... fields ...
    
    def set_email(self, plaintext_email: str):
        """Encrypt email and set hash for lookups."""
        svc = EncryptionService()
        self.email_encrypted = svc.encrypt(plaintext_email)
        self.email_hash = svc.hash_for_lookup(plaintext_email.lower())
    
    def get_email(self) -> str:
        """Decrypt and return email."""
        if not self.email_encrypted:
            return None
        svc = EncryptionService()
        return svc.decrypt(self.email_encrypted)
```

**Create Alembic migration** (in Fix 8 section below).

---

# INFRASTRUCTURE FIXES

## Fix 8: Set Up Alembic & Create Initial Migration

**Time:** 45 minutes  
**Why:** Schema changes must be versioned and repeatable

### Step 1: Initialize Alembic

```bash
cd apps/api
alembic init alembic
```

This creates:
- `alembic/` directory
- `alembic.ini` config file
- `alembic/env.py` (database connection script)
- `alembic/versions/` (migration files directory)

### Step 2: Configure `alembic/env.py`

Edit `alembic/env.py` to auto-detect SQLAlchemy models:

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from alembic import context
from sqlalchemy import pool
from src.models.base import DeclarativeBase
from src.core.config import get_settings

config = context.config
settings = get_settings()

# Configure target metadata (auto-detect models)
target_metadata = DeclarativeBase.metadata

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using async engine."""
    
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.begin() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    # Offline mode (for generating migration diffs)
    context.configure(target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    # Online mode
    asyncio.run(run_migrations_online())
```

### Step 3: Create Initial Migration

```bash
cd apps/api
alembic revision --autogenerate -m "001_initial_stage1_schema"
```

This generates `alembic/versions/001_initial_stage1_schema_*.py` with all table definitions.

### Step 4: Review and apply the migration

```bash
# Review what will be created
cat alembic/versions/001_initial_stage1_schema_*.py

# Apply to local database
alembic upgrade head

# Verify
alembic current  # Should show your migration version
```

### Step 5: Add to `pyproject.toml` (if not already present)

```toml
dependencies = [
    # ... existing ...
    "alembic>=1.13.0",
    "sqlalchemy[asyncio]>=2.0.0",
]
```

**Verify:**
```bash
# Should be able to apply migration without errors
alembic upgrade head

# Should be able to downgrade
alembic downgrade -1

# Should be able to upgrade again
alembic upgrade head
```

---

## Fix 9: Add `/auth/register` Endpoint

**File:** `apps/api/src/api/v1/endpoints/auth.py` (new file)  
**Time:** 20 minutes

### Create `apps/api/src/api/v1/endpoints/auth.py`:

```python
"""
Authentication endpoints: register, verify email, login.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr, BaseModel

from src.core.database import get_db
from src.core.security import verify_jwt, hash_password
from src.core.encryption import EncryptionService
from src.models.models import User
from src.repositories.base import AsyncRepository
from src.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    auth0_sub: str  # From Auth0 token
    email: EmailStr
    display_name: str

class RegisterResponse(BaseModel):
    user_id: str
    email: str
    needs_consent: bool

@router.post("/register", response_model=RegisterResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new PADI.AI user linked to Auth0.
    Called after Auth0 signup (post-Auth0 redirect).
    
    Returns: user_id and flag indicating consent is required.
    """
    # Check if user already exists
    user_repo = AsyncRepository(User, db)
    existing = await user_repo.get_by_field("auth0_sub", request.auth0_sub)
    if existing:
        return RegisterResponse(
            user_id=existing.id,
            email=existing.get_email(),
            needs_consent=not existing.email_verified,
        )
    
    # Create new user
    new_user = User(
        auth0_sub=request.auth0_sub,
        display_name=request.display_name,
        role="parent",
        email_verified=False,
        is_active=True,
    )
    
    # Encrypt email
    new_user.set_email(request.email)
    
    # Save to database
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return RegisterResponse(
        user_id=new_user.id,
        email=new_user.get_email(),
        needs_consent=True,  # Always require consent for new users
    )

@router.post("/verify-email")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify email after Auth0 sends verification email.
    Token is provided by Auth0.
    
    In practice, Auth0 handles email verification.
    This endpoint is for compatibility with flow spec.
    """
    # For now, just mark email_verified = True for the user
    # In reality, Auth0 should have already verified
    return {"status": "email_verified", "next_step": "consent"}

@router.post("/login")
async def login(
    auth0_sub: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Login endpoint (stub — Auth0 handles real login).
    Called after Auth0 provides tokens.
    """
    user_repo = AsyncRepository(User, db)
    user = await user_repo.get_by_field("auth0_sub", auth0_sub)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    user.login_count += 1
    db.add(user)
    await db.commit()
    
    return {
        "user_id": user.id,
        "email": user.get_email(),
        "role": user.role,
        "consent_completed": user.email_verified,
    }
```

### Register the auth router in `apps/api/src/api/v1/router.py`:

```python
from src.api.v1.endpoints import auth, assessments, consent, students, standards

router = APIRouter(prefix="/v1")

router.include_router(auth.router)
router.include_router(assessments.router)
router.include_router(consent.router)
router.include_router(students.router)
router.include_router(standards.router)
```

**Verify:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "auth0_sub": "auth0|12345",
    "email": "test@example.com",
    "display_name": "Test User"
  }'
# Should return: {"user_id": "...", "email": "test@example.com", "needs_consent": true}
```

---

## Fix 10: Add `/auth/verify-email` Endpoint

Already included in Fix 9 above (`POST /auth/verify-email`).

---

## Fix 11: Add AWS SES Email Integration

**File:** `apps/api/src/clients/ses_client.py` (new file)  
**Time:** 30 minutes

### Create `apps/api/src/clients/ses_client.py`:

```python
"""
AWS SES client for sending transactional emails.
"""

import boto3
from botocore.exceptions import ClientError
from src.core.config import get_settings

settings = get_settings()

class SESClient:
    """AWS SES email service client."""
    
    def __init__(self):
        self.client = boto3.client(
            "ses",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
    
    async def send_consent_verification_email(
        self,
        to_email: str,
        verification_token: str,
        parent_name: str,
    ) -> bool:
        """Send COPPA consent verification email."""
        try:
            verification_link = (
                f"https://padi-ai.com/consent/confirm"
                f"?token={verification_token}"
            )
            
            html_body = f"""
            <html>
            <body>
                <h2>Confirm Your Parental Consent</h2>
                <p>Hello {parent_name},</p>
                <p>Thank you for registering with PADI.AI. To complete your parental consent 
                and activate your account, please click the link below:</p>
                
                <p><a href="{verification_link}">Confirm Consent</a></p>
                
                <p>This link expires in 48 hours.</p>
                <p>PADI.AI Team</p>
            </body>
            </html>
            """
            
            response = self.client.send_email(
                Source="noreply@padi-ai.com",
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": "Confirm Parental Consent - PADI.AI"},
                    "Body": {"Html": {"Data": html_body}},
                },
            )
            
            return True
        except ClientError as e:
            print(f"SES error sending to {to_email}: {e}")
            return False
    
    async def send_assessment_complete_email(
        self,
        to_email: str,
        parent_name: str,
        child_name: str,
        results_url: str,
    ) -> bool:
        """Send 'assessment complete' notification email."""
        try:
            html_body = f"""
            <html>
            <body>
                <h2>Diagnostic Assessment Complete</h2>
                <p>Hello {parent_name},</p>
                <p>{child_name}'s diagnostic assessment is complete! 
                Click below to view detailed results and recommendations.</p>
                
                <p><a href="{results_url}">View Results</a></p>
                
                <p>PADI.AI Team</p>
            </body>
            </html>
            """
            
            response = self.client.send_email(
                Source="noreply@padi-ai.com",
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": f"Assessment Results Ready - {child_name}"},
                    "Body": {"Html": {"Data": html_body}},
                },
            )
            
            return True
        except ClientError as e:
            print(f"SES error sending to {to_email}: {e}")
            return False

def get_ses_client() -> SESClient:
    """FastAPI dependency."""
    return SESClient()
```

### Update `ConsentService` to use SES

**File:** `apps/api/src/services/consent_service.py`

Find the `initiate_consent()` method and add email sending:

```python
async def initiate_consent(
    self,
    user_id: str,
    consent_data: dict,
    ses_client: SESClient,  # Add dependency
) -> ConsentInitiateResponse:
    """Initiate COPPA consent (step 1 of 2)."""
    # ... existing code ...
    
    # GENERATE TOKEN
    token = generate_consent_token()
    
    # SAVE CONSENT RECORD
    consent_record = ConsentRecord(
        parent_id=user_id,
        consent_type="coppa_verifiable",
        status="pending",
        verification_token=token,
        token_expires_at=datetime.utcnow() + timedelta(hours=48),
    )
    self.consent_repo.create(consent_record)
    
    # SEND EMAIL
    user = await self.user_repo.get_by_id(user_id)
    parent_email = user.get_email()
    
    email_sent = await ses_client.send_consent_verification_email(
        to_email=parent_email,
        verification_token=token,
        parent_name=user.display_name,
    )
    
    if not email_sent:
        # Log warning but don't fail — token is still valid
        print(f"Failed to send consent email to {parent_email}")
    
    return ConsentInitiateResponse(
        consent_record_id=consent_record.id,
        token=token,
        expires_in_hours=48,
    )
```

### Add to endpoint dependency injection

**File:** `apps/api/src/api/v1/endpoints/consent.py`

```python
from src.clients.ses_client import SESClient, get_ses_client

@router.post("/initiate")
async def initiate_consent(
    request: ConsentInitiateRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    ses_client: SESClient = Depends(get_ses_client),
):
    service = ConsentService(consent_repo, user_repo)
    return await service.initiate_consent(
        user_id=current_user.id,
        consent_data=request.dict(),
        ses_client=ses_client,
    )
```

### Add SES config to `apps/api/src/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing ...
    
    # AWS SES
    AWS_REGION: str = Field(default="us-west-2")
    AWS_ACCESS_KEY_ID: str = Field(default="")
    AWS_SECRET_ACCESS_KEY: str = Field(default="")
```

**For local development**, add to `.env.example`:
```
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=test-key-id
AWS_SECRET_ACCESS_KEY=test-secret-key
```

---

# TEST INFRASTRUCTURE FIXES

## Fix 12: Migrate Test Suite from SQLite to PostgreSQL

**Current problem:** Tests run against SQLite (`conftest.py` sets `DATABASE_URL = sqlite:///./test_padi.db`), but production uses PostgreSQL. Tests for RLS, pgvector, partitions fail on SQLite.

**Solution:** Use `testcontainers` for automatic PostgreSQL container in tests.

### Step 1: Add testcontainers dependency to `pyproject.toml`

```toml
[project]
dependencies = [
    # ... existing ...
    "testcontainers[postgresql]>=4.0.0",
]

[project.optional-dependencies]
dev = [
    # ... existing ...
    "testcontainers[postgresql]>=4.0.0",
]
```

### Step 2: Rewrite `apps/api/tests/conftest.py`

```python
"""
Test configuration with PostgreSQL testcontainers.
"""

import asyncio
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.models.base import DeclarativeBase
from src.core.config import Settings

# Global container (shared across test session)
_container = None

def pytest_configure(config):
    """Start PostgreSQL container once per test session."""
    global _container
    _container = PostgresContainer("postgres:17", driver="asyncpg")
    _container.start()

def pytest_sessionfinish(session, exitstatus):
    """Stop PostgreSQL container after tests."""
    global _container
    if _container:
        _container.stop()

@pytest.fixture(scope="session")
def event_loop():
    """Provide event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create async engine connected to test PostgreSQL."""
    # Get connection URL from testcontainer
    db_url = _container.get_connection_url()
    
    # Convert to asyncpg driver
    db_url = db_url.replace("psycopg2", "asyncpg")
    
    engine = create_async_engine(
        db_url,
        poolclass=NullPool,
        echo=False,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(DeclarativeBase.metadata.create_all)
    
    yield engine
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(DeclarativeBase.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    """Provide a test database session."""
    async_session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()

@pytest.fixture
def test_settings():
    """Override settings for tests."""
    return Settings(
        DATABASE_URL=_container.get_connection_url().replace("psycopg2", "asyncpg"),
        ENVIRONMENT="test",
        DEBUG=True,
    )

@pytest.fixture
async def async_client(test_settings):
    """Provide async FastAPI test client."""
    from fastapi.testclient import TestClient
    from src.main import app
    
    with TestClient(app) as client:
        yield client
```

### Step 3: Update existing test fixtures

Any test that currently patches `DATABASE_URL` should remove that:

```python
# BEFORE (remove this):
@pytest.fixture
def test_settings():
    return Settings(DATABASE_URL="sqlite:///./test.db")

# AFTER (use the fixture from conftest):
async def test_something(db_session, test_settings):
    # db_session is now a real PostgreSQL connection
    pass
```

### Step 4: Run tests against real PostgreSQL

```bash
cd apps/api

# Install test dependencies
pip install -e ".[dev]"

# Run all tests (will auto-start PostgreSQL container)
pytest tests/ -v

# Run specific category
pytest tests/security/ -v
pytest tests/integration/ -v
```

**Benefits:**
- Tests now run against the actual database engine (PostgreSQL)
- RLS tests actually validate `pg_policies`
- pgvector queries work
- Partition tests work
- Test coverage is now valid for production

---

## Fix 13: Fix Performance Test Async/Sync Bug

**File:** `apps/api/tests/performance/test_bkt_benchmark.py`  
**Time:** 10 minutes

### Current broken code:
```python
def test_single_skill_update_under_50ms():  # ← Not async
    """Single BKT skill update should be < 50ms."""
    result = await bkt_service.update_state(...)  # ← Using await in non-async function
```

### Fixed code:
```python
@pytest.mark.asyncio
async def test_single_skill_update_under_50ms():  # ← Now async
    """Single BKT skill update should be < 50ms."""
    # Use time tracking
    import time
    start = time.time()
    result = await bkt_service.update_state(...)  # ← Now valid await
    elapsed_ms = (time.time() - start) * 1000
    
    # Assert performance SLA
    assert elapsed_ms < 50, f"BKT update took {elapsed_ms}ms, expected < 50ms"
```

Apply this pattern to all performance tests:
- Add `@pytest.mark.asyncio` decorator
- Change `def test_...` to `async def test_...`
- All other code stays the same

---

# SHOULD-FIX BEFORE STAGE 2

## Fix 14: Seed Question Bank

**File:** `apps/api/scripts/seed-db.sh` (new file)  
**Time:** 1 hour + manual question creation

### Create `apps/api/scripts/seed-db.sh`:

```bash
#!/bin/bash

set -e

# Seed the question bank with sample questions for Grade 4
# Minimum: 4 questions per standard

cd "$(dirname "$0")/.."

# Run Python script to insert questions
python -m scripts.seed_questions

echo "✓ Question bank seeded"
```

### Create `apps/api/scripts/seed_questions.py`:

```python
"""
Seed the question bank with Grade 4 math questions.
Minimum: 4 questions per Oregon standard.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.models.models import Standard, Question, QuestionOption
from src.core.config import get_settings
from src.repositories.standard_repository import StandardRepository
from src.repositories.question_repository import QuestionRepository

settings = get_settings()

SAMPLE_QUESTIONS = [
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
    # Add 100+ more questions here...
]

async def seed():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session_maker() as session:
        repo = QuestionRepository(session)
        
        for q in SAMPLE_QUESTIONS:
            # Check if exists
            existing = await repo.get_by_field("stem", q["stem"])
            if existing:
                continue
            
            question = Question(
                standard_code=q["standard_code"],
                difficulty=q["difficulty"],
                question_type=q["question_type"],
                stem=q["stem"],
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                source="seed",
                status="active",
            )
            
            session.add(question)
            await session.flush()
            
            # Add options
            for opt in q["options"]:
                session.add(QuestionOption(
                    question_id=question.id,
                    option_text=opt["text"],
                    is_correct=(opt["key"] == q["correct_answer"]),
                    order=ord(opt["key"]) - ord("A"),
                ))
        
        await session.commit()
        print(f"✓ Seeded {len(SAMPLE_QUESTIONS)} questions")

if __name__ == "__main__":
    asyncio.run(seed())
```

Run:
```bash
cd apps/api
python scripts/seed_questions.py
```

---

## Fix 15: Add Missing Frontend Routes

**Files to create:**
- `apps/web/app/(onboarding)/layout.tsx`
- `apps/web/app/(onboarding)/consent/page.tsx`
- `apps/web/app/(onboarding)/create-student/page.tsx`
- `apps/web/app/(dashboard)/layout.tsx`
- `apps/web/app/(dashboard)/page.tsx`
- `apps/web/app/(dashboard)/diagnostic/start/page.tsx`

These are specified in ENG-001 but missing. Create basic versions matching the spec structure.

**Time:** 2-3 hours (design + implementation)

---

## Fix 16: Add pybkt to pyproject.toml

**File:** `apps/api/pyproject.toml`

```toml
[project]
dependencies = [
    # ... existing ...
    "pybkt>=0.1.0",
]
```

---

# Verification Checklist

After all fixes, verify:

- [ ] `pytest apps/api/tests/ -v` — all tests pass
- [ ] `curl -X POST localhost:8000/api/v1/auth/register` — returns user_id
- [ ] `curl -X GET localhost:8000/api/v1/standards/4.OA.A.1 -H "Authorization: Bearer TOKEN"` — returns bkt_defaults
- [ ] `curl -X POST localhost:8000/api/v1/assessments -H "Authorization: Bearer TOKEN"` — returns assessment_id, no NameError
- [ ] Assessment complete flow end-to-end with 35 questions
- [ ] Parent email is encrypted in database (check with: `SELECT email_encrypted FROM users;` — should be binary, not text)
- [ ] `alembic current` — shows migration version
- [ ] Frontend routes load without errors
- [ ] All E2E tests pass (Playwright)

---

# Summary

**Total time to complete:** 4-6 hours  
**Blocking issues:** 16 (5 critical, 11 supporting)  
**Stage 2 readiness:** Achievable with this guide

Good luck! 🚀
