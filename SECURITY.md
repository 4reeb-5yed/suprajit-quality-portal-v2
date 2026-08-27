# 🔐 Security Policy

The Suprajit Quality Portal (V2) is strictly designed to pass global Enterprise AppSec audits (OWASP Top 10) for safe exposure to the public internet via a Reverse Proxy.

## Implemented Defenses

| Threat Domain | Implementation |
|---|---|
| **SQL Injection (SQLi)** | 100% Parameterized SQLite Queries (`?`). No raw string concatenation. |
| **Password Cryptography** | `Scrypt` memory-hard hashing. Mathematically resistant to GPU brute-forcing. |
| **Brute-Force Attacks** | Automated Account Lockout (15-minute ban after 5 failed attempts). |
| **Cross-Site Request Forgery (CSRF)** | `Flask-WTF` cryptographic tokens injected into all state-changing HTML forms. |
| **Session Hijacking** | `HttpOnly` and `SameSite` session cookies managed by `Flask-Login`. |
| **File / Data Integrity** | `SHA-256` cryptographic hashing to strictly prevent duplicate/spoofed file injections. |
| **Data Leakage (Tenant Isolation)** | Cryptographic Session-to-CustomerID verification on all routes. |
| **MIME Sniffing & Clickjacking** | Strict HTTP Response Headers (`X-Frame-Options`, `X-Content-Type-Options`). |
| **Audit Trails** | Immutable `audit_logs` table tracking exactly which IP address downloaded which file. |

## Network Deployment Requirements
**CRITICAL:** While the application code is 100% secure, the physical transport layer is the responsibility of the deployment IT team. 
When hosting this software for external clients (e.g., `portal.suprajit.com`), it **must** be placed behind a Reverse Proxy (NGINX, IIS, Cloudflare) with a valid **SSL/TLS Certificate (HTTPS)** to prevent Man-in-the-Middle (MITM) packet sniffing.
