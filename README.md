# Suprajit Quality Portal (V3 Enterprise Edition)

A high-concurrency, multi-tenant Quality Report Indexing, In-Browser Spreadsheet Inspection, and Automated Ingestion System engineered for automotive and manufacturing environments.

It autonomously indexes factory quality inspection reports (Excel `.xlsx` / `.csv`), parses metadata via configurable dynamic regex, isolates records across customer organizations with 3-tier Role-Based Access Control (RBAC), and serves a zero-overhead in-browser spreadsheet viewer and public internet portal.

---

## 🌟 Key Architecture & Capabilities

### 1. 🛡️ 3-Tier Multi-Tenancy & Granular RBAC
- **Master Admin (`bootstrap_admin`)**: Complete system authority, global customer provisioning, dynamic regex configuration, SMTP settings, SSO credentials, and native tunnel orchestration.
- **Company Admin (`company_admin`)**: Delegated administrative portal for client companies (e.g. TVS, Mahindra, Tata). Manage internal team members, auto-join email domains, user activation toggles, and recipe assignment.
- **Client Viewer (`customer_viewer`)**: Filtered search portal with granular recipe scopes (`ALL` vs `CUSTOM` user-assigned recipes) and instant tenant isolation.
- **Instant Kill-Switch**: 1-click global customer suspension with live session termination.

### 2. ⚡ Ingestion Engine & Dynamic Regex Parser
- **N-1 Batch Ingestion**: Chronologically scans previous-day batches to mathematically avoid Windows OS file locks and partial network file copies.
- **Dynamic Filename Regex Engine**: Configure and validate custom recipe, date, time, and serial number naming patterns live in the Admin UI without restarting the server.
- **SHA-256 Deduplication & Integrity**: Cryptographic deduplication and zero-byte quarantine safeguards.

### 3. 📊 In-Browser Excel Spreadsheet Viewer (Zero Server Overhead)
- **Client-Side SheetJS WebAssembly Rendering**: In-browser preview for `.xlsx` and `.csv` files directly inside an interactive modal.
- **Multi-Sheet Navigation**: Seamlessly navigate between workbook sheets without stressing backend CPU or memory.
- **Forensic Audit Logging**: Every download and online view event is recorded in an immutable audit trail with client IP and timestamps.

### 4. 🔑 Enterprise Single Sign-On (SSO / OAuth 2.0)
- Out-of-the-box OAuth 2.0 integration for **Microsoft 365 / Outlook / Entra ID**, **Google Workspace**, and **GitHub**.
- **Corporate Domain Auto-Join**: Users signing in via SSO or self-registering with verified company email domains (`@tvs.com`, `@mahindra.com`) are automatically assigned to their respective company organization.

### 5. 🌐 Native Internet Tunneling & Configurable Notifications
- **1-Click Cloudflare Zero Trust Tunnel Runner**: Native subprocess controller for instant, free public endpoints (`trycloudflare.com`) or custom corporate domain tunnel tokens.
- **Public URL Resolution**: Automatically rewrites invitation and password reset links to use the public tunnel/domain URL.
- **Configurable Email Templates**: Live editors for Team Invites, Single User Welcomes, and Password Reset emails with dynamic tags.

---

## 🚀 Quick Start (Development & Local Run)

### 1. Clone & Setup Environment
```bash
git clone https://github.com/4reeb-5yed/suprajit-quality-portal-v2.git
cd suprajit-quality-portal-v2
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Run Development Server
```bash
python web_server.py
```
*Accessible at `http://localhost:5000`. Initial setup credentials: Username `bootstrap_admin`, Password `admin123`.*

---

## 🧪 3-Way Test Matrix (107 Tests)

The repository enforces a comprehensive 3-way test matrix executed locally and in GitHub CI Actions:

```bash
# Run complete test suite with coverage
python -m pytest tests/ -v --cov=app --cov-report=term
```

- **Tier 1 (Unit & Isolation)**: Regex parser engine, AES-256 Fernet cryptography, SHA-256 deduplication, path traversal defenses.
- **Tier 2 (Multi-Tenant Integration & Security)**: OWASP ASVS isolation, 3-tier RBAC boundaries, SSO OAuth client registration, Cloudflare tunnel management.
- **Tier 3 (End-to-End & Smoke Tests)**: Search filtering lifecycle, Excel raw stream endpoints, bulk onboarding, self-registration, and error recovery.

---

## 📦 Production Executable (.exe) Compilation

Compile the standalone single-binary package using Waitress WSGI and PyInstaller:

```cmd
.\build.bat
```
---

## 📖 Complete Documentation Index
- [Architecture & Design Records (ADR)](docs/ARCHITECTURE.md)
- [Administrator & Operations Guide](docs/ADMIN_GUIDE.md)
- [Factory IT Deployment Guide](docs/DEPLOYMENT.md)
- [OWASP ASVS 2025 Hardening & Security Policy](SECURITY.md)
- [System Internals & Database Schema](SYSTEM_INTERNALS.md)



