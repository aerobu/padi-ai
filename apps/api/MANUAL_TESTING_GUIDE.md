# Manual Testing Guide for PADI.AI

This guide covers how to manually test the key implementations that have been completed.

## Prerequisites

1. **PostgreSQL is running** (already set up in Docker):
   ```bash
   docker ps | grep postgres
   # Should show: pgvector/pgvector:pg16 running on port 5433
   ```

2. **Database migrations applied**:
   ```bash
   cd apps/api
   DATABASE_URL="$(grep DATABASE_URL .env | cut -d= -f2)" alembic upgrade head
   ```

3. **Redis is running** (optional, for cache):
   ```bash
   docker ps | grep redis
   ```

## 1. API Server Testing

### Start the API Server
```bash
cd apps/api
uvicorn src.main:app --reload --port 8000
```

### Test Endpoints with curl

#### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{"status":"healthy","timestamp":"2026-04-15T..."}
```

#### List Standards
```bash
curl http://localhost:8000/api/v1/standards?grade=4&domain=OA
```

Expected: Returns Oregon Grade 4 OA (Operations & Algebraic Thinking) standards.

#### Create Student Profile
```bash
curl -X POST http://localhost:8000/api/v1/students \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Maria",
    "grade_level": 4,
    "avatar_id": "avatar_default",
    "birth_year": 2017
  }'
```

Expected: Returns created student with `student_id`.

## 2. Encryption Service Testing

### Test Email Encryption/Decryption

```python
# apps/api/tests/manual/test_encryption.py
from src.core.encryption import EncryptionService
from src.core.config import get_settings

settings = get_settings()
encryption = EncryptionService(settings.ENCRYPTION_KEY_PASSPHRASE)

# Test encryption
email = "parent@example.com"
encrypted = encryption.encrypt(email)
print(f"Encrypted: {encrypted}")

# Test decryption
decrypted = encryption.decrypt(encrypted)
print(f"Decrypted: {decrypted}")
assert decrypted == email

# Test hash for lookups
email_hash = encryption.hash_for_lookup(email)
print(f"Email hash: {email_hash}")

# Verify hash is consistent
assert encryption.hash_for_lookup(email) == email_hash
```

Run:
```bash
python apps/api/tests/manual/test_encryption.py
```

## 3. BKT (Bayesian Knowledge Tracing) Service Testing

### Test BKT State Updates

```python
# apps/api/tests/manual/test_bkt.py
import sys
sys.path.insert(0, 'src')

from src.services.bkt_impl import BKT

# Create BKT instance with default parameters
bkt = BKT(p_l0=0.1, p_trans=0.5, p_slip=0.2, p_guess=0.25)

print(f"Initial P(mastery): {bkt.p_l:.4f}")

# Simulate correct answer
bkt.forward_inference(is_correct=True)
print(f"After correct: P(mastery) = {bkt.p_l:.4f}")

# Simulate another correct answer
bkt.forward_inference(is_correct=True)
print(f"After 2nd correct: P(mastery) = {bkt.p_l:.4f}")

# Simulate incorrect answer
bkt.forward_inference(is_correct=False)
print(f"After incorrect: P(mastery) = {bkt.p_l:.4f}")

# Get current state
state = bkt.get_node("4.OA.A.1")
print(f"State: P(L)={state.p_l}, P(T)={state.p_trans}, P(S)={state.p_slip}, P(G)={state.p_guess}")
```

Run:
```bash
python apps/api/tests/manual/test_bkt.py
```

## 4. Assessment Flow Testing

### Complete Assessment Flow with HTTPie

Install HTTPie if not already installed:
```bash
pip install httpie
```

#### Step 1: Create Student
```bash
http POST http://localhost:8000/api/v1/students \
  display_name="Test Student" \
  grade_level=4 \
  birth_year=2017
```

#### Step 2: Initiate Consent
```bash
http POST http://localhost:8000/api/v1/consent/consent \
  parent_id="parent_id_here" \
  student_display_name="Test Student" \
  consent_type="coppa_verifiable"
```

#### Step 3: Start Assessment
```bash
http POST http://localhost:8000/api/v1/assessments/start \
  parent_id="parent_id_here" \
  student_id="student_id_here" \
  assessment_type=diagnostic
```

## 5. Frontend Testing

### Start the Web Application
```bash
cd apps/web
pnpm dev
```

### Access the Application

1. **Dashboard**: http://localhost:3000/dashboard
2. **Onboarding Consent**: http://localhost:3000/onboarding/consent
3. **Create Student**: http://localhost:3000/onboarding/create-student
4. **Diagnostic Start**: http://localhost:3000/diagnostic/start

### Test Scenarios

#### Scenario 1: New User Flow
1. Navigate to http://localhost:3000/dashboard
2. Click "Create Student Profile"
3. Enter student details (e.g., "Maria", Grade 4, Birth Year 2017)
4. Submit form
5. Should redirect to dashboard with student listed

#### Scenario 2: Assessment Flow
1. After creating a student, click "Start Assessment"
2. Review assessment details (35-45 questions, 45-60 minutes)
3. Click "Start Assessment"
4. Should navigate to assessment session page

## 6. Database Verification

### Check Users Table Schema
```bash
docker exec -it eip_postgres psql -U postgres -d padi -c "\d users"
```

Expected columns:
- `id` (varchar)
- `auth0_id` (varchar, unique)
- `email_encrypted` (bytea)
- `email_hash` (varchar(64), unique)
- `first_name`, `last_name`, etc.

### Check Students Table
```bash
docker exec -it eip_postgres psql -U postgres -d padi -c "\d students"
```

Expected columns:
- `id` (varchar)
- `parent_id` (varchar, foreign key)
- `display_name` (varchar)
- `grade_level` (integer)
- `birth_year` (integer)

## 7. Quick Sanity Check Script

Create a test script to verify all components:

```python
# apps/api/tests/manual/verify_setup.py
import sys
sys.path.insert(0, 'src')

from src.core.encryption import EncryptionService
from src.core.config import get_settings
from src.services.bkt_impl import BKT

print("=== PADI.AI Manual Verification ===\n")

# 1. Test encryption
print("1. Testing Encryption Service...")
settings = get_settings()
encryption = EncryptionService(settings.ENCRYPTION_KEY_PASSPHRASE)
email = "test@example.com"
encrypted = encryption.encrypt(email)
decrypted = encryption.decrypt(encrypted)
assert decrypted == email, "Encryption/decryption failed!"
print("   ✓ Encryption working")

# 2. Test BKT
print("2. Testing BKT Service...")
bkt = BKT()
bkt.forward_inference(True)
assert bkt.p_l > 0.1, "BKT not updating!"
print(f"   ✓ BKT working (P(mastery) = {bkt.p_l:.4f})")

# 3. Test database connection
print("3. Testing Database Connection...")
from src.core.database import get_db
import asyncio

async def test_db():
    async for db in get_db():
        from src.models.models import User
        result = await db.execute(__import__('sqlalchemy').select(User).limit(1))
        print("   ✓ Database connected")
        return

asyncio.run(test_db())

print("\n=== All Checks Passed! ===")
```

Run:
```bash
python apps/api/tests/manual/verify_setup.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Database connection failed` | Check PostgreSQL is running: `docker ps \| grep postgres` |
| `Port 8000 already in use` | Stop other processes or use different port: `--port 8001` |
| `Alembic migration error` | Check migration: `alembic current` and upgrade: `alembic upgrade head` |
| `Import errors` | Install dependencies: `pip install -e ".[dev]"` |

## Next Steps

After verifying manual testing works, you can:
1. Integrate Auth0 for production authentication
2. Set up AWS SES for email verification
3. Seed questions using `scripts/seed_questions.py`
4. Run the full test suite: `pytest tests/ --ignore=tests/performance`
