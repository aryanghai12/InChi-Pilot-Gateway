"""Run the existing suites on disposable PostgreSQL 17 and loopback-only services.

Usage: .venv/Scripts/python.exe e2e/scripts/local-qa.py
Requires installed project dependencies, Docker Compose and Playwright Chromium.
Credentials exist only in process environments; no .env or product settings are edited.
"""
import json
import argparse
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--phase", choices=["full", "e2e", "browser-retest"], default="full")
parser.add_argument("--evidence-dir", type=Path)
parser.add_argument("--docker-context", help="Optional Docker context (otherwise uses the active context)")
options = parser.parse_args()
EVIDENCE = options.evidence_dir or ROOT / ".cache/qa-evidence" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
if (EVIDENCE / "summary.json").exists():
    raise SystemExit("Evidence already exists; select a new --evidence-dir to preserve prior results")
RUNTIME = ROOT / ".cache/qa-local-stack"
EVIDENCE.mkdir(parents=True, exist_ok=True)
RUNTIME.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env.update({
    "PYTHON_DOTENV_DISABLED": "1", "DEBUG": "False", "ALLOWED_HOSTS": "127.0.0.1,localhost,testserver",
    "CSRF_TRUSTED_ORIGINS": "http://127.0.0.1:53001", "CORS_ALLOWED_ORIGINS": "http://127.0.0.1:53001",
    "SESSION_COOKIE_SECURE": "False", "CSRF_COOKIE_SECURE": "False",
    "QA_DB_PASSWORD": secrets.token_urlsafe(32), "SECRET_KEY": secrets.token_urlsafe(48),
    "E2E_BASE_URL": "http://127.0.0.1:53001", "E2E_BACKEND": "1",
    "BACKEND_ORIGIN": "http://127.0.0.1:58001", "NEXT_TELEMETRY_DISABLED": "1",
    "PLAYWRIGHT_BROWSERS_PATH": os.environ.get("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".cache/qa-browsers")),
})
env.pop("E2E_API_ONLY", None)
for role in ["ANALYST", "REVIEWER", "ADMIN"]:
    env[f"E2E_{role}_EMAIL"] = f"qa-{role.lower()}@example.test"
    env[f"E2E_{role}_PASSWORD"] = secrets.token_urlsafe(32)
env["DATABASE_URL"] = f"postgresql://qa_runner:{env['QA_DB_PASSWORD']}@127.0.0.1:55439/qa_backend"
secret_values = [value for key, value in env.items() if key.startswith("E2E_") and key.endswith("PASSWORD")]
secret_values += [env["QA_DB_PASSWORD"], env["SECRET_KEY"]]
summary = {"qa_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
           "started_utc": datetime.now(timezone.utc).isoformat(), "checks": []}
compose = ["docker"]
if options.docker_context:
    compose += ["--context", options.docker_context]
compose += ["compose", "-p", "inchi-qa-verification", "-f", str(ROOT / "e2e/docker-compose.qa.yml")]
npm = "npm.cmd" if os.name == "nt" else "npm"
processes = []
handles = []


def redact(text):
    for value in secret_values:
        text = text.replace(value, "[REDACTED]")
    return text


def run(name, args, cwd=ROOT, extra=None, code=None):
    child_env = env | (extra or {})
    result = subprocess.run(args, cwd=cwd, env=child_env, input=code, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = "Command: " + " ".join(str(arg) for arg in args) + "\n" + result.stdout + result.stderr + f"\nExit code: {result.returncode}\n"
    (EVIDENCE / f"{name}.txt").write_text(redact(log), encoding="utf-8")
    summary["checks"].append({"name": name, "exit_code": result.returncode})
    print(f"{name}: exit {result.returncode}", flush=True)
    return result.returncode


def start(name, args, cwd):
    handle = (RUNTIME / f"{name}.log").open("w", encoding="utf-8")
    handles.append(handle)
    process = subprocess.Popen(args, cwd=cwd, env=env, stdout=handle, stderr=subprocess.STDOUT)
    processes.append(process)
    return process


def wait_url(url, process):
    for _ in range(90):
        if process.poll() is not None:
            raise RuntimeError("Local service exited; inspect ignored runtime log")
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(1)
    raise RuntimeError("Local service did not become ready")


try:
    for port in [55439, 58001, 53001]:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", port))
    # Refuse to reuse a previous QA database; never touch other projects/containers.
    existing = subprocess.check_output(compose + ["ps", "-a", "-q"], cwd=ROOT, env=env, text=True).strip()
    if existing:
        raise RuntimeError("QA compose project already exists; inspect it before rerunning")
    if run("postgres-start", compose + ["up", "-d", "--wait"]):
        raise RuntimeError("Disposable PostgreSQL 17 startup failed")
    import psycopg
    with psycopg.connect(env["DATABASE_URL"], autocommit=True) as db:
        db.execute("CREATE EXTENSION IF NOT EXISTS vector")
        db.execute("CREATE DATABASE qa_data")
    with psycopg.connect(env["DATABASE_URL"].rsplit("/", 1)[0] + "/template1", autocommit=True) as db:
        db.execute("CREATE EXTENSION IF NOT EXISTS vector")
    run("database-version", compose + ["exec", "-T", "db", "psql", "-U", "qa_runner", "-d", "qa_backend", "-c", "SELECT version(); SELECT extversion FROM pg_extension WHERE extname='vector';"])
    python = sys.executable
    backend_env = {"DJANGO_SETTINGS_MODULE": "config.settings", "PYTHONPATH": str(ROOT / "backend")}
    env.update(backend_env)
    if options.phase == "full":
        run("backend-check", [python, "manage.py", "check"], ROOT / "backend")
        run("backend-migration-drift", [python, "manage.py", "makemigrations", "--check", "--dry-run"], ROOT / "backend")
        run("backend-tests", [python, "-m", "pytest", "--ds=config.settings", "apps/accounts/tests", "apps/registry/tests", "--tb=short", "-q"], ROOT / "backend")
        run("qa-backend-controls", [python, "-m", "pytest", "--ds=config.settings", str(ROOT / "e2e/backend/test_controls.py"), "--tb=short", "-q"], ROOT / "backend")
        run("database-tests", [python, "-m", "pytest", "--ds=config.settings", "apps/demand/tests", "--tb=short", "-q"], ROOT / "database",
            {"PYTHONPATH": str(ROOT / "database"), "DATABASE_URL": env["DATABASE_URL"].rsplit("/", 1)[0] + "/qa_data"})
    if run("backend-migrate", [python, "manage.py", "migrate", "--noinput"], ROOT / "backend"):
        raise RuntimeError("Application migrations failed")
    seed = '''import django, os
django.setup()
from apps.accounts.models import User, Role
for label, role in [("ANALYST", Role.COMMERCIAL_ANALYST), ("REVIEWER", Role.REVIEWER), ("ADMIN", Role.PLATFORM_ADMIN)]:
    User.objects.create_user(email=os.environ[f"E2E_{label}_EMAIL"], password=os.environ[f"E2E_{label}_PASSWORD"], role=role, is_verified=True)
print("Created three synthetic role accounts in the disposable QA database; credentials omitted")
'''
    if run("seed-roles", [python, "-"], ROOT / "backend", code=seed):
        raise RuntimeError("Synthetic role setup failed")
    if options.phase == "full":
        run("frontend-lint", [npm, "run", "lint"], ROOT / "frontend")
        run("frontend-typecheck", [npm, "run", "typecheck"], ROOT / "frontend")
        run("frontend-tests", [npm, "test"], ROOT / "frontend")
        run("qa-config", [npm, "run", "test:config"], ROOT / "e2e")
    run("qa-typecheck", ["node", str(ROOT / "frontend/node_modules/typescript/bin/tsc"), "--project", "tsconfig.json"], ROOT / "e2e")
    run("qa-discovery", [npm, "run", "test:list"], ROOT / "e2e")
    if options.phase != "browser-retest" and run("frontend-build", [npm, "run", "build"], ROOT / "frontend"):
        raise RuntimeError("Production frontend build failed; browser/API execution blocked")
    backend = start("backend", [python, "manage.py", "runserver", "127.0.0.1:58001", "--noreload"], ROOT / "backend")
    wait_url("http://127.0.0.1:58001/api/v1/health/", backend)
    frontend = start("frontend", ["node", "node_modules/next/dist/bin/next", "start", "--hostname", "127.0.0.1", "--port", "53001"], ROOT / "frontend")
    wait_url(env["E2E_BASE_URL"] + "/login", frontend)
    # Check Django through the built Next.js proxy before any browser assertions.
    wait_url(env["E2E_BASE_URL"] + "/api/v1/health/", frontend)
    if run("qa-preflight", [npm, "run", "preflight"], ROOT / "e2e"):
        raise RuntimeError("Full-stack E2E configuration failed preflight")
    selection = ["auth.spec.ts", "workspace.spec.ts"] if options.phase == "browser-retest" else []
    run("playwright-regression", [npm, "test", "--", *selection, "--workers=2", "--retries=0"], ROOT / "e2e")
    for source, destination in [("results.json", "playwright-results.json"), ("junit.xml", "playwright-junit.xml")]:
        path = ROOT / "e2e/test-results" / source
        if path.exists():
            (EVIDENCE / destination).write_text(redact(path.read_text(encoding="utf-8")), encoding="utf-8")
except Exception as error:
    summary["blocker"] = redact(str(error))
    print(summary["blocker"], flush=True)
finally:
    for process in reversed(processes):
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
    for handle in handles:
        handle.close()
    # Only remove the compose project started by this invocation.
    if any(item["name"] == "postgres-start" for item in summary["checks"]):
        run("postgres-stop", compose + ["down"])
    summary["finished_utc"] = datetime.now(timezone.utc).isoformat()
    (EVIDENCE / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if summary.get("blocker") or any(item["exit_code"] for item in summary["checks"]):
        sys.exit(1)
