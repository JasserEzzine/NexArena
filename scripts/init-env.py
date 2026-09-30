"""Generate local-only secrets. Never overwrites an existing environment."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
target = root / ".env"
if target.exists():
    print(".env already exists; kept unchanged")
else:
    password = secrets.token_hex(20)
    target.write_text(f"POSTGRES_USER=nexarena\nPOSTGRES_PASSWORD={password}\nPOSTGRES_DB=nexarena\nDATABASE_URL=postgresql+psycopg://nexarena:{password}@127.0.0.1:5432/nexarena\nJWT_SECRET={secrets.token_hex(32)}\nAGENT_ENROLLMENT_KEY={secrets.token_hex(32)}\nDEMO_PASSWORD={secrets.token_urlsafe(15)}\nCORS_ORIGINS=http://localhost:5173,http://localhost:8080\nHEARTBEAT_TIMEOUT=30\n", encoding="utf-8")
    print("Created .env with random local credentials. Read DEMO_PASSWORD there to sign in.")
