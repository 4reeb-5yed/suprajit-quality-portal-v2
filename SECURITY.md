# Security Policy & Hardening

This document outlines the security architecture, threat model mitigations, and vulnerability reporting procedures for the Suprajit Quality Portal.

---

## 1. Threat Mitigation Matrix

| Threat Domain | Implementation in Application |
| :--- | :--- |
| **SQL Injection (SQLi)** | 100% Parameterized SQLite queries (`?` placeholders). No string concatenation in query construction. |
| **Password Hashing** | Salted password hashing via `werkzeug.security.generate_password_hash` (`scrypt` / PBKDF2). |
| **Credential Brute-Force** | IP-level rate limiting via `Flask-Limiter` (`10 per minute` on `/login`) and 15-minute account lockout after 5 consecutive failed attempts. |
| **Cross-Site Request Forgery (CSRF)**| `Flask-WTF` CSRF token validation on all state-changing `POST` requests. |
| **Session Security** | `HttpOnly`, `SameSite=Lax`, and `Secure` session cookies managed by `Flask-Login`. |
| **Data Integrity & Deduplication** | 64KB block SHA-256 cryptographic hashing to detect identical duplicate files and prevent spoofed uploads. |
| **Multi-Tenant Isolation** | Database query isolation via `app.helpers.customer_scope()`, restricting access by `customer_id` and recipe permissions. |
| **Path Traversal Defense** | Realpath directory boundary verification via `app.helpers.is_safe_path()` on all download and raw streaming routes. |
| **Secret Encryption at Rest** | Reversible credentials (SMTP passwords) stored in `system_settings` are encrypted using AES-256 Fernet (`cryptography.fernet.Fernet`). |
| **Audit Trails** | Immutable `audit_log` table recording user ID, action (`login`, `download`, `view_online`), client IP, and timestamps. |

---

## 2. Transport Layer & Deployment Requirements

While application code enforces authentication and tenant boundaries, transport encryption must be provided by the deployment environment:

- When deployed for internet or external client access, the server **must** be exposed via an encrypted HTTPS connection (either via the native Cloudflare Zero Trust tunnel or a reverse proxy like NGINX / IIS with a valid SSL/TLS certificate).

---

## 3. Reporting a Vulnerability

If you discover a security vulnerability in the Suprajit Quality Portal:

1. **Do not create a public GitHub issue.**
2. Report the vulnerability privately to the project maintainers with a detailed description and proof-of-concept steps.
3. Security reports will be acknowledged and reviewed within 48 business hours.
