# Technical Decision Record: TD-04 — Login Rate Limiting & Throttling

| Attribute | Specification |
|---|---|
| **Decision ID** | **TD-04** (Formerly open in ARCHITECTURE.md §9 & REGISTERS.md §1.2) |
| **Author** | **Ajendra Nath Tripathi** (Cybersecurity and DevSecOps Engineer) |
| **Reviewers** | Abhishek Kumar (Backend), Aryan Ghai (Coordination), Harish Pal (QA) |
| **Status** | **Decided & Resolved (Week 5 — 23 Nov 2026)** |
| **Target Architecture** | [`../../backend/config/settings.py`](../../backend/config/settings.py), [`../../backend/apps/accounts/views.py`](../../backend/apps/accounts/views.py) |
| **Threat Mitigated** | **T-DS-02**: Credential Stuffing & Authentication Brute Force |

---

## 1. Problem Statement & Threat Surface

InChi Pilot Gateway is a private internal application intended strictly for authorized BNCS personnel. The login endpoint (`POST /api/v1/auth/login/`) handles password verification and session establishment.

Prior to Week 5, `config/settings.py` configured no rate limiters or throttle classes (ARCHITECTURE.md §9 finding on TD-04). Without rate limiting:
1. An attacker or malicious internal script could execute rapid brute-force dictionary attacks against user accounts.
2. High-frequency automated login requests could cause CPU exhaustion through repeated PBKDF2 password hashing calculations (600,000 iterations per attempt).

---

## 2. Technical Evaluation & Architecture Options

Three implementation options were evaluated:

| Option | Architecture | Evaluation |
|---|---|---|
| **Option A**: Reverse Proxy / Edge Throttling (Next.js) | Enforce rate limiting inside Next.js Node.js middleware. | **Rejected**: Violates **TD-10** (no auth or business logic in Next.js) and fails if Django backend is addressed directly or in native dev. |
| **Option B**: Django Cache-Backed Redis Throttling | External Redis cluster managing sliding window token buckets. | **Deferred to Phase 2**: InChi v0.1 Compose environment uses PostgreSQL without Redis; adding Redis violates AGENTS.md §B rule 8 (unapproved new service). |
| **Option C**: DRF `ScopedRateThrottle` with Django Cache | Native DRF scoped throttling using Django's default cache (locmem for single-worker/local dev; database or shared cache for Compose). | **APPROVED (Recommended)**: Zero external dependencies; precise per-view scoping; standard DRF HTTP 429 semantics; clean test configuration. |

---

## 3. Decision & Technical Specification

### 3.1 Rate Limit Policy

The application enforces the following rate limits:

| Scope | Rate Limit | Target Endpoints | Justification |
|---|---|---|---|
| **`login`** | **`5/minute`** | `POST /api/v1/auth/login/` | Restricts automated password guessing to $\le 5$ attempts per minute per IP address. Sufficient for human typists; prohibitive for brute-force attacks. |
| **`anon`** | `100/day` | Unauthenticated generic endpoints | General defense against unauthenticated scraping. |
| **`user`** | `1000/day` | Authenticated user sessions | Baseline anomaly cap per internal user. |

### 3.2 Error Response Envelope & HTTP 429 Semantics

When rate limit is exceeded, the server returns **HTTP 429 Too Many Requests** formatted into the uniform project error envelope (`config/exceptions.py`):

```json
{
  "code": "throttled",
  "message": "Request was throttled. Expected available in 58 seconds.",
  "field_errors": {},
  "correlation_id": "c1f73809-54bc-4184-b0d7-21752b04f128"
}
```

The response includes standard headers:
* `Retry-After`: Number of seconds until the throttle window permits subsequent requests.

### 3.3 Implementation Blueprint

1. **Django Settings (`backend/config/settings.py`)**:
   ```python
   REST_FRAMEWORK = {
       ...
       "DEFAULT_THROTTLE_CLASSES": [
           "rest_framework.throttling.AnonRateThrottle",
           "rest_framework.throttling.UserRateThrottle",
           "rest_framework.throttling.ScopedRateThrottle",
       ],
       "DEFAULT_THROTTLE_RATES": {
           "anon": os.getenv("THROTTLE_ANON_RATE", "100/day"),
           "user": os.getenv("THROTTLE_USER_RATE", "1000/day"),
           "login": os.getenv("THROTTLE_LOGIN_RATE", "5/minute"),
       },
   }
   ```
2. **Login View (`backend/apps/accounts/views.py`)**:
   ```python
   from rest_framework.throttling import ScopedRateThrottle

   @method_decorator(csrf_protect, name="dispatch")
   class LoginView(APIView):
       permission_classes = [AllowAny]
       authentication_classes = []
       throttle_classes = [ScopedRateThrottle]
       throttle_scope = "login"
       ...
   ```
3. **Exception Handler Mapping (`backend/config/exceptions.py`)**:
   ```python
   from rest_framework.exceptions import Throttled
   ...
   elif isinstance(exc, Throttled):
       error_code = "throttled"
       message = getattr(exc, "detail", "Request was throttled.")
       response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
   ```

---

## 4. Verification & Testing Guardrails

1. **Test Environment Exemption**: Automated integration tests execute multiple assertions per second. Test runners may override `REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['login'] = None` or supply custom test settings to prevent test false-positives while preserving production safety.
2. **Automated Negative Test**: Verified via `backend/apps/accounts/tests/test_security_posture.py::SecurityPostureTests::test_sec_17_login_throttling_configuration_and_semantics`.

