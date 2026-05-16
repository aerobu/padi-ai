"""Dump the FastAPI OpenAPI schema to stdout as JSON.

Usage:
    python -m scripts.export_openapi > openapi.json

Used by the root `pnpm gen:openapi` script (P2-T05) to drive
TypeScript type generation for `packages/types`.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Make `src` importable when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

# Provide safe defaults for env vars so importing `src.main` doesn't
# require a real DB / Auth0 secrets during type generation.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://localhost/openapi_dump")
os.environ.setdefault("AUTH0_SECRET", "openapi-dump")
os.environ.setdefault("AUTH0_BASE_URL", "http://localhost")
os.environ.setdefault("AUTH0_ISSUER_BASE_URL", "http://localhost")
os.environ.setdefault("AUTH0_CLIENT_ID", "openapi-dump")
os.environ.setdefault("AUTH0_CLIENT_SECRET", "openapi-dump")
os.environ.setdefault(
    "ENCRYPTION_KEY_PASSPHRASE", "openapi-dump-passphrase-32-chars-ok"
)

from src.main import app  # noqa: E402

if __name__ == "__main__":
    json.dump(app.openapi(), sys.stdout, indent=2)
    sys.stdout.write("\n")
