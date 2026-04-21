"""
Quick inline test of all major components.
Run from apps/api directory: python tests/manual/quick_test.py
"""
import sys
sys.path.insert(0, 'src')

print("=== PADI.AI Quick Test ===\n")

# 1. Encryption
print("1. Encryption Service")
from src.core.encryption import EncryptionService
test_email = "test@example.com"
encrypted = EncryptionService.encrypt(test_email)
decrypted = EncryptionService.decrypt(encrypted)
assert decrypted == test_email
print(f"   PASS: Encrypt/decrypt works")
print(f"   Hash: {EncryptionService.hash_for_lookup(test_email)[:32]}...")

# 2. BKT
print("2. BKT Service")
from src.services.bkt_impl import BKT
bkt = BKT(p_l0=0.1, p_trans=0.5, p_slip=0.2, p_guess=0.25)
initial = bkt.p_l
for _ in range(3):
    bkt.forward_inference(is_correct=True)
assert bkt.p_l > initial
print(f"   PASS: BKT updates (mastery {initial:.2f} -> {bkt.p_l:.2f})")

# 3. API
print("3. FastAPI Application")
from src.main import app
print(f"   PASS: {len(app.router.routes)} routes registered")

# 4. Database (using settings directly)
print("4. Database")
from src.core.config import get_settings
from sqlalchemy import create_engine, text

settings = get_settings()
print(f"   DB URL: {settings.DATABASE_URL.split(':')[0]}://...")

# Create sync engine for schema check
sync_url = settings.DATABASE_URL.replace('asyncpg', 'psycopg2').replace('postgresql+asyncpg://', 'postgresql://')
sync_engine = create_engine(sync_url)
with sync_engine.connect() as conn:
    # Check users table
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'users' AND column_name IN ('email_encrypted', 'email_hash')
        ORDER BY column_name
    """))
    columns = [row[0] for row in result]
    assert 'email_encrypted' in columns and 'email_hash' in columns
    print(f"   PASS: Users table has encrypted columns")

    # Check students table
    result = conn.execute(text("""
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_name = 'students'
    """))
    col_count = result.scalar()
    print(f"   PASS: Students table has {col_count} columns")

print("\n=== ALL TESTS PASSED ===")
print("\nYou can now:")
print("  1. Start API: uvicorn src.main:app --reload")
print("  2. Run tests: pytest tests/ --ignore=tests/performance")
print("  3. Check schema: psql $(grep DATABASE_URL .env | cut -d= -f2) -c '\\d users'")
