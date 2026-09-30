"""Create a monitoring-only local agent configuration from the seeded branch."""
import json
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
from app.db import SessionLocal
from app.models import Branch
from sqlalchemy import select
from app.config import settings

target = root / "agent" / "appsettings.local.json"
if target.exists():
    print("Agent configuration already exists; kept unchanged")
else:
    with SessionLocal() as db:
        branch = db.scalar(select(Branch).where(Branch.name == "Tunis Gaming House"))
        if not branch:
            raise RuntimeError("Run the database seed first")
        config = json.loads((root / "agent" / "appsettings.example.json").read_text())
        config.update(EnrollmentKey=settings.agent_enrollment_key, BranchId=branch.id, AllowedGames={})
        target.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print("Configured PC-01 for local monitoring. Remote commands and shutdown are disabled.")
