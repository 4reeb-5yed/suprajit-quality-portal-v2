# Changelog

All notable changes to the Suprajit Quality Portal will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Modular `app/routes/admin/` package structure partitioned into `dashboard`, `users`, `customers`, `settings`, `sso`, `tunnel`, and `diagnostics`.
- Native SQLite `PRAGMA user_version` ordered migration engine in `app/database.py` with legacy schema inference and transaction safety.
- Custom pytest markers (`unit`, `integration`, `e2e`, `live_external`) with staged GitHub Actions CI execution.
- Comprehensive contributor guide (`CONTRIBUTING.md`) and test documentation (`tests/README.md`).

### Removed
- Unused legacy `src/suprajit_v2/` package scaffold and corresponding `[project.scripts]` entry from `pyproject.toml`.

---

## [3.0.0] - 2026-08-30

### Added
- **Multi-Tenant RBAC & Isolation**: 3-tier Role-Based Access Control (`admin`, `company_admin`, `customer_viewer`) with customer suspension kill-switch and granular recipe permission assignment (`ALL` vs `CUSTOM`).
- **Dynamic Regex Parser**: Configurable filename metadata extraction engine capturing recipe, date, time, and serial tokens without hardcoded patterns.
- **Enterprise Single Sign-On (SSO / OAuth 2.0)**: Built-in support for Google Workspace, Microsoft 365 / Outlook, and GitHub OAuth 2.0 with corporate domain auto-join.
- **Native Cloudflare Tunnel Integration**: Integrated 1-click TryCloudflare quick tunnel and named corporate tunnel runners directly from the admin dashboard.
- **In-Browser Spreadsheet Viewer**: Client-side SheetJS / WebAssembly workbook rendering with multi-sheet tabs and zero server compute overhead.
- **Evidence & Quality Metrics**: ASVS 5.0 and ISO 9001 quality observability dashboard (`/admin/evidence`) tracking search latency (p50/p95), index accuracy, and system recovery metrics.
- **Configurable Email Templates**: Dynamic template editors for customer onboarding invites, welcome credentials, and password resets.

### Security
- OWASP ASVS 5.0 Level 2 compliance verification across authentication, tenant isolation, rate limiting, and password hashing (PBKDF2/bcrypt).
- Session fixation protection, strict Content Security Policy (CSP), and HTTP security headers.
