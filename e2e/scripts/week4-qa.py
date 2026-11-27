"""Run focused Week 4 API tests and existing regression without touching shared data.

Usage: <QA python> e2e/scripts/week4-qa.py [--postgres]
SQLite uses pytest-django's in-memory test database. --postgres requires an
explicit DATABASE_URL pointing at an isolated synthetic server with CREATEDB.
Raw logs/JUnit stay ignored; the summary contains names/statuses, not credentials.
"""

import argparse
import json
import os
import secrets
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--postgres", action="store_true")
args = parser.parse_args()
env = os.environ.copy()
if args.postgres and not env.get("DATABASE_URL", "").startswith(
    ("postgresql://", "postgres://")
):
    parser.error("--postgres requires an isolated PostgreSQL DATABASE_URL")
if not args.postgres:
    env["DATABASE_URL"] = ""
env.update(
    {
        "PYTHON_DOTENV_DISABLED": "1",
        "DEBUG": "False",
        "SECRET_KEY": secrets.token_urlsafe(48),
        "ALLOWED_HOSTS": "testserver,localhost,127.0.0.1",
    }
)
stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
evidence = ROOT / ".cache" / "qa-week4" / stamp
evidence.mkdir(parents=True, exist_ok=False)
command = [
    sys.executable,
    "-m",
    "pytest",
    "--ds=config.settings",
    "--tb=short",
    "-q",
    "-rs",
    "apps/accounts/tests",
    "apps/registry/tests",
    "../e2e/backend/test_controls.py",
    "../e2e/backend/test_week4_workflows.py",
    f"--junitxml={evidence / 'junit.xml'}",
]
result = subprocess.run(
    command, cwd=ROOT / "backend", env=env, text=True, capture_output=True, check=False
)
raw = (result.stdout + result.stderr).replace(env["SECRET_KEY"], "[REDACTED]")
(evidence / "pytest.txt").write_text(raw, encoding="utf-8")
cases = []
if (evidence / "junit.xml").exists():
    for case in ET.parse(evidence / "junit.xml").iter("testcase"):
        outcome = "passed"
        detail = ""
        for tag in ("failure", "error", "skipped"):
            node = case.find(tag)
            if node is not None:
                outcome = {"failure": "failed", "error": "error", "skipped": "blocked"}[
                    tag
                ]
                detail = node.attrib.get("message", "").replace(
                    env["SECRET_KEY"], "[REDACTED]"
                )
                break
        cases.append(
            {
                "suite": case.attrib.get("classname", ""),
                "test": case.attrib["name"],
                "outcome": outcome,
                "detail": detail,
            }
        )
summary = {
    "executed_utc": datetime.now(UTC).isoformat(),
    "base_sha": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip(),
    "branch": subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=ROOT, text=True
    ).strip(),
    "uncommitted_qa_changes": True,
    "database": "postgresql" if args.postgres else "sqlite in-memory",
    "python": sys.version.split()[0],
    "command": "python -m pytest --ds=config.settings --tb=short -q -rs apps/accounts/tests apps/registry/tests ../e2e/backend/test_controls.py ../e2e/backend/test_week4_workflows.py --junitxml=<ignored evidence>/junit.xml",
    "exit_code": result.returncode,
    "counts": {
        name: sum(c["outcome"] == name for c in cases)
        for name in ("passed", "failed", "blocked", "error")
    },
    "cases": cases,
}
(evidence / "summary.json").write_text(
    json.dumps(summary, indent=2) + "\n", encoding="utf-8"
)
print(raw)
print(
    json.dumps(
        {"evidence": str(evidence.relative_to(ROOT)), "counts": summary["counts"]}
    )
)
sys.exit(result.returncode)
