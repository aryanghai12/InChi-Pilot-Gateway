# Secure Staging Checklist — InChi Pilot Gateway v0.1

| Attribute | Specification |
|---|---|
| **Author** | **Ajendra Nath Tripathi** (Cybersecurity and DevSecOps Engineer) |
| **Status** | Prepared Baseline — **Execution Pending BNCS Host Provision (D-16)** |
| **Authority** | [`../MVP_FEATURES.md`](../MVP_FEATURES.md) §4 (M11-AC9); [`../ARCHITECTURE.md`](../ARCHITECTURE.md) §8, §9 (D-16) |

---

## 1. Scope & Preconditions

Per **Decision D-16**, the containerized Docker Compose stack is the authoritative reference environment for demonstrations, UAT, and evaluation. **Hosted staging is optional.** 

If BNCS provides a hosted non-production server, this checklist **must be executed and signed off by the DevSecOps Engineer (Ajendra)** prior to loading any data or admitting users.

---

## 2. Pre-Staging Security Verification Checklist

### 2.1 Transport Layer & TLS Security
- [ ] **HTTPS Enforcement**: HTTP requests strictly redirect to HTTPS (301 Permanent Redirect).
- [ ] **TLS Version**: TLS 1.3 enforced (minimum TLS 1.2 permitted; TLS 1.0/1.1 disabled).
- [ ] **Valid Certificate**: Valid TLS certificate issued by an approved CA (no self-signed certificates in staging).
- [ ] **Security Headers**: Verified in `next.config.ts`:
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - Content Security Policy (CSP) tailored for Next.js App Router without unsafe inline scripts.

### 2.2 Django Application & Environment Hardening
- [ ] **`DEBUG = False`**: Formally verified that Django `DEBUG` is set to `False`.
- [ ] **Host Restriction**: `ALLOWED_HOSTS` configured with exact staging domain; no wildcard `*`.
- [ ] **CSRF Protection**: `CSRF_TRUSTED_ORIGINS` explicitly matches the staging HTTPS origin.
- [ ] **Proxy SSL Header**: `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` active *only* behind the verified staging reverse proxy.
- [ ] **Admin URL Obfuscation**: `ADMIN_URL_PATH` set to a non-standard secret path from environment variables; standard `/admin/` path returns 404.

### 2.3 Session & Cookie Attributes
- [ ] **Secure Session Cookie**: `SESSION_COOKIE_SECURE = True`.
- [ ] **Secure CSRF Cookie**: `CSRF_COOKIE_SECURE = True`.
- [ ] **HttpOnly Protection**: `SESSION_COOKIE_HTTPONLY = True`.
- [ ] **SameSite Policy**: `SESSION_COOKIE_SAMESITE = 'Lax'`.
- [ ] **Session Expiry**: Maximum timeout set to 28,800 seconds (8 hours).

### 2.4 Database & Storage Isolation
- [ ] **Dedicated DB User**: PostgreSQL connection uses a non-superuser application role with restricted privileges.
- [ ] **Database Network Isolation**: PostgreSQL port `5432` is bound only to the internal Docker network or `localhost`, not publicly exposed to the internet.
- [ ] **Encrypted Communication**: Inter-service traffic between Django and PostgreSQL enforces SSL where supported.
- [ ] **Audit Trigger Active**: PostgreSQL trigger on `AuditEvent` actively verified to block `UPDATE` and `DELETE`.

### 2.5 Synthetic Data & Secrets Hygiene
- [ ] **Zero Real Data**: Verified that database contains *only* synthetic data generated via `manage.py seed_demo`.
- [ ] **Secrets from Environment**: All secrets (database password, Django `SECRET_KEY`, initial admin password) injected exclusively via secure environment variables.
- [ ] **Log Redaction**: Verified that application stdout logs contain no plaintext passwords, session IDs, or CSRF tokens.

---

## 3. Sign-Off Record

| Role | Name | Decision | Date |
|---|---|---|---|
| **DevSecOps Engineer** | Ajendra Nath Tripathi | *Pending Staging Provision* | — |
| **Technical Mentor / BNCS** | — | *Pending Staging Provision* | — |
