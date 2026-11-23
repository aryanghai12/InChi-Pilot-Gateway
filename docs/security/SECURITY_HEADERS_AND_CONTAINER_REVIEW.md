# Security Headers & Container Hardening Review — InChi Pilot Gateway v0.1

| Attribute | Specification |
|---|---|
| **Author** | **Ajendra Nath Tripathi** (Cybersecurity and DevSecOps Engineer) |
| **Reviewers** | Priyanka Singh (Frontend), Abhishek Kumar (Backend), Aryan Ghai (Coordination) |
| **Authority** | [`../../AGENTS.md`](../../AGENTS.md) §C2; [`../ARCHITECTURE.md`](../ARCHITECTURE.md) §7, §8; [`InChi_China_Readiness_Implementation_Baseline_v2.2.pdf`](../source-documents/InChi_China_Readiness_Implementation_Baseline_v2.2.pdf) §14.1 |
| **Status** | Approved Baseline Review — Week 2 Deliverable (Validated in Week 4 Audit) |

---

## 1. Executive Summary

This security review provides a comprehensive defense-in-depth assessment of:
1. **HTTP Security Headers** enforced at the client-facing Next.js edge (`frontend/next.config.ts`) and Django application tier (`backend/config/settings.py`).
2. **Edge Proxy Architecture & Trust Boundaries** governing the single-origin reverse proxy (`TD-09`, `TD-10`).
3. **Container Hardening Posture** evaluated against the **CIS Docker Community Edition Benchmark v1.6.0** across all four Docker Compose services (`frontend`, `backend`, `matching`, `db`).

The evaluation confirms that the single-origin architecture effectively protects session tokens from cross-origin exposure. However, critical gaps remain for production staging, including the lack of a Content Security Policy (CSP), missing Strict-Transport-Security (HSTS), and container runtime privilege dropping.

---

## 2. HTTP Security Headers Audit

### 2.1 Current Implementation Status (`frontend/next.config.ts`)

Inspection of `frontend/next.config.ts` (lines 49–74) reveals the baseline client headers currently served:

```typescript
// Client-side security headers (ARCHITECTURE.md §7)
async headers() {
  return [
    {
      source: "/:path*",
      headers: [
        { key: "X-Content-Type-Options", value: "nosniff" },
        { key: "X-Frame-Options", value: "DENY" },
        { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
      ],
    },
  ];
}
```

### 2.2 Header-by-Header Evaluation & Gap Analysis

| Header | Current Value | Target / Staging Recommendation | Assessment & Risk Analysis |
|---|---|---|---|
| **`X-Content-Type-Options`** | `nosniff` | `nosniff` | **Compliant.** Prevents MIME-confusion attacks and Drive-by-Download attacks in older browsers. |
| **`X-Frame-Options`** | `DENY` | `DENY` | **Compliant.** Prevents clickjacking by prohibiting rendering inside `<iframe>`, `<frame>`, `<embed>`, or `<object>`. |
| **`Referrer-Policy`** | `strict-origin-when-cross-origin` | `strict-origin-when-cross-origin` | **Compliant.** Sends full path only to same-origin requests; truncates to origin for cross-origin HTTPS requests; sends no referrer over insecure HTTP. Protects confidential URL parameters. |
| **`Permissions-Policy`** | `camera=(), microphone=(), geolocation=()` | `camera=(), microphone=(), geolocation=(), payment=(), usb=()` | **Adequate (Pilot).** Restricts browser hardware APIs not required by InChi Pilot. Expand to disable `payment` and `usb` APIs. |
| **`Content-Security-Policy` (CSP)** | *Missing* | `default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none';` | **High Gap (AUD-10).** Missing CSP allows arbitrary script execution if an XSS vulnerability occurs in React components or third-party packages. Must be staged before external demonstration. |
| **`Strict-Transport-Security` (HSTS)** | *Missing* | `max-age=31536000; includeSubDomains; preload` | **Omitted by Design in Local Dev; Mandatory for Staging (D-16).** Local dev runs on plain HTTP (`http://localhost:3000`). Enforcing HSTS locally breaks dev. Must be enabled conditionally via `NODE_ENV=production` when SSL termination is present. |
| **`Cross-Origin-Opener-Policy` (COOP)** | *Missing* | `same-origin` | **Recommended.** Isolates the browsing context to prevent Spectre-style cross-origin window reference attacks. |
| **`Cross-Origin-Resource-Policy` (CORP)** | *Missing* | `same-origin` | **Recommended.** Prevents other origins from reading static assets or authenticated JSON responses. |

---

## 3. Edge Proxy & Single-Origin Architecture Review (`TD-09`, `TD-10`)

### 3.1 Trust Boundary Analysis

```
  [ Browser Client ]
          │
          │ HTTP Request (Single Origin: http://localhost:3000)
          ▼
┌─────────────────────────────────────────────────────────────┐
│ Next.js Standalone Edge Server (Port 3000)                  │
│   • Serves static assets & React Server/Client Components    │
│   • Injects Security Headers (Section 2)                    │
│   • Rewrites /api/:path* -> http://backend:8000/api/:path*  │
│   • Rewrites /{ADMIN_URL_PATH}/* -> http://backend:8000/... │
│   • NO Node.js Server Actions, NO Auth logic, NO Secrets    │
└─────────────────────────────────────────────────────────────┘
          │ Internal Docker Network (172.x.x.x)
          ▼
┌─────────────────────────────────────────────────────────────┐
│ Django 5.2 Application Layer (Port 8000)                    │
│   • Validates Session Cookie (`sessionid`)                  │
│   • Validates CSRF Token (`csrftoken` & `X-CSRFToken`)      │
│   • Enforces RBAC Policy (`policy.py`)                      │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Security Invariants & Verification Checklist

1. **Cookie Boundary Preservation**: Because browser requests originate from `http://localhost:3000` and are reverse-proxied internally, session cookies (`sessionid`) and CSRF tokens (`csrftoken`) are stored as **first-party cookies** on port 3000. This eliminates the need for permissive CORS (`CORS_ALLOWED_ORIGINS=""`) and prevents third-party cookie blocking.
2. **Zero-Trust Rendering Boundary (`TD-10`)**:
   - Next.js acts strictly as a reverse proxy for data operations.
   - All authorization checks are executed exclusively in Django (`apps.accounts.permissions.RolePermission`).
   - Frontend route protection (`src/middleware.ts`) provides user-experience redirection only and is never treated as a security boundary.
3. **Host & Origin Validation**:
   - `ALLOWED_HOSTS` in Django strictly includes `localhost,127.0.0.1,backend`.
   - `CSRF_TRUSTED_ORIGINS` in Django is configured to `http://localhost:3000,http://127.0.0.1:3000`.
   - Header spoofing via `X-Forwarded-Host` is rejected because `USE_X_FORWARDED_HOST = False` by default.

---

## 4. Container Hardening & CIS Docker Benchmarks Audit

Evaluation of container images and orchestrations against **CIS Docker Community Edition Benchmark v1.6.0**:

### 4.1 Image & Runtime Configuration Matrix

| CIS Benchmark Control | Evaluation Target | Implementation Status | Findings & Remediation |
|---|---|---|---|
| **CIS 4.1**: Create a user for the container | `backend/Dockerfile` | **PASS** | `RUN groupadd --system --gid 1001 inchi && useradd --system --uid 1001 --gid inchi inchi`<br>Switches to `USER inchi` before entrypoint. |
| **CIS 4.1**: Create a user for the container | `backend/Dockerfile` (matching) | **PASS** | `USER inchi` specified on line 34. |
| **CIS 4.1**: Create a user for the container | `frontend/Dockerfile` | **PASS** | `RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs`<br>`USER nextjs` specified on line 47. |
| **CIS 4.2**: Use trusted base images | All Dockerfiles | **PASS** | Uses official minimal upstream images: `python:3.12.16-slim-bookworm`, `node:20-alpine`, `pgvector/pgvector:0.8.6-pg17-bookworm`. |
| **CIS 4.3**: Do not install unnecessary packages | All Dockerfiles | **PASS** | Minimal slim/alpine bases; multi-stage builds prune devDependencies in `frontend/Dockerfile` (`standalone` output). |
| **CIS 4.6**: Add HEALTHCHECK instruction | All Dockerfiles | **PASS** | `backend`: Native Python HTTP check on `/api/v1/health/`<br>`matching`: Native Python HTTP check on `/health`<br>`db`: `pg_isready` check via Compose. |
| **CIS 5.1**: Do not disable AppArmor / Seccomp | `docker-compose.yml` | **PASS** | Default seccomp profiles retained; no `--privileged` flags used. |
| **CIS 5.4**: Do not expose host namespaces | `docker-compose.yml` | **PASS** | Containers use isolated bridge network namespaces; no `network_mode: host`. |
| **CIS 5.7**: Do not map privileged ports (<1024) | `docker-compose.yml` | **PASS** | Only non-privileged host ports mapped: 3000 (frontend) and 5432 bound strictly to `127.0.0.1`. |
| **CIS 5.10**: Limit memory & CPU usage | `docker-compose.yml` | **GAP (Medium)** | Resource limits (`deploy.resources.limits`) not set in `docker-compose.yml`. AI vector processing could cause host resource contention. |
| **CIS 5.12**: Mount container's root filesystem as read-only | All services | **GAP (Low - Pilot)** | Writable root filesystems in use. `backend` requires writable `/app/staticfiles` and `/app` for gunicorn socket. Recommend ephemeral `tmpfs` mounts for `/tmp` in production. |
| **CIS 5.13**: Restrict incoming traffic (Least Privilege) | `docker-compose.yml` | **PASS** | `backend` and `matching` ports (8000, 8001) use Compose `expose` (internal network only), preventing direct host or external network bypass. |

---

## 5. Security Action Plan & Remediation Tasks

1. **Task SEC-ACT-01 (Priyanka - Frontend)**:
   - Add Content Security Policy (CSP) header to `frontend/next.config.ts`.
   - Add `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Resource-Policy: same-origin`.
2. **Task SEC-ACT-02 (Abhishek - Backend)**:
   - Verify `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = 'Lax'`, and `CSRF_COOKIE_HTTPONLY = False` (required for JS reader).
   - In production/staging environment, enforce `SESSION_COOKIE_SECURE = True` and `CSRF_COOKIE_SECURE = True`.
3. **Task SEC-ACT-03 (Vishal / DevSecOps - Infrastructure)**:
   - Add explicit resource constraints (CPU / Memory limits) in `docker-compose.yml` for the `matching` service to prevent DoS via unconstrained vector calculations.

