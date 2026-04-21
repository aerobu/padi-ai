"""
Quick verification script to ensure all major components are working.
Run this from the apps/api directory.
"""
import os
import sys

# Add src directory to path
src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_dir)

from src.core.encryption import EncryptionService
from src.core.config import get_settings
from src.services.bkt_impl import BKT
from sqlalchemy import text
from src.core.database import engine

print("=== PADI.AI Manual Verification ===\n")

# 1. Test encryption
print("1. Testing Encryption Service...")
email = "test@example.com"
encrypted = EncryptionService.encrypt(email)
decrypted = EncryptionService.decrypt(encrypted)
assert decrypted == email, "Encryption/decryption failed!"
email_hash = EncryptionService.hash_for_lookup(email)
print(f"   OK Encryption working")
print(f"   OK Email hash: {email_hash[:16]}...")

# 2. Test BKT
print("2. Testing BKT Service...")
bkt = BKT(p_l0=0.10, p_trans=0.50, p_slip=0.20, p_guess=0.25)
initial_mastery = bkt.p_l
bkt.forward_inference(is_correct=True)
bkt.forward_inference(is_correct=True)
assert bkt.p_l > initial_mastery, "BKT not updating correctly!"
print(f"   OK BKT working (P(mastery) increased from {initial_mastery:.4f} to {bkt.p_l:.4f})")

# 3. Test database connection
print("3. Testing Database Connection...")
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
    print("   OK Database connected")
except Exception as e:
    print(f"   FAIL Database connection failed: {e}")
    sys.exit(1)

# 4. Check tables exist
print("4. Checking Database Tables...")
with engine.connect() as conn:
    # Check users table
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'users' AND column_name IN ('email_encrypted', 'email_hash')
    """))
    columns = [row[0] for row in result]
    assert 'email_encrypted' in columns, "Missing email_encrypted column"
    assert 'email_hash' in columns, "Missing email_hash column"
    print(f"   OK Users table: has email_encrypted and email_hash columns")

    # Check students table
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'students'
    """))
    columns = [row[0] for row in result]
    assert 'display_name' in columns, "Missing display_name column"
    print(f"   OK Students table has {len(columns)} columns (including display_name)")

# 5. Test API import
print("5. Testing API Import...")
try:
    from src.main import app
    print(f"   OK FastAPI app loaded ({len(app.router.routes)} routes)")
except Exception as e:
    print(f"   FAIL API import failed: {e}")
    sys.exit(1)

print("\n=== All Checks Passed! ===\n")
print("Ready to start the API server with: uvicorn src.main:app --reload")
