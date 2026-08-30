# Suprajit Quality Portal

The Suprajit Quality Portal is an edge-deployed inspection report indexing, spreadsheet preview, and multi-tenant search system engineered for manufacturing and factory environments.

---

## 1. Tech Stack

| Component / Layer | Technology | Version Constraint / Dependency |
| :--- | :--- | :--- |
| **Web Framework** | Flask | `>=3.1.3` |
| **WSGI Server** | Waitress | `>=3.0.2` |
| **Database** | SQLite 3 (WAL mode) | Standard Library (`sqlite3`) |
| **Authentication & Sessions** | Flask-Login, Authlib | `flask-login>=0.6.3`, `authlib>=1.7.0` |
| **Rate Limiting & CSRF** | Flask-Limiter, Flask-WTF | `flask-limiter>=4.1.1`, `flask-wtf>=1.3.0` |
| **Cryptography** | cryptography (Fernet AES-256) | `>=41.0.0` |
| **Environment Configuration** | python-dotenv | `>=1.2.3` |
| **Spreadsheet Viewer** | SheetJS (WebAssembly) | Client-side standalone bundle |
| **Test Framework** | pytest, pytest-cov, Playwright | `pytest>=9.1.1`, `playwright>=1.40.0` |
| **Static Analysis** | Ruff, Mypy, Bandit, Pip-Audit | `ruff>=0.1.0`, `mypy>=1.8.0`, `bandit>=1.7.0` |

---

## 2. Key Features

- **Multi-Tenant Scoping & 3-Tier RBAC**: Isolates quality reports across customer companies (`admin`, `company_admin`, `customer_viewer`) with granular recipe access (`ALL` vs `CUSTOM`).
- **N-1 Batch Ingestion Engine**: Automatically indexes previous-calendar-day inspection reports to prevent Windows file lock contention and in-flight network copy errors.
- **Dynamic Filename Metadata Extraction**: Configurable regex parser capturing recipe names, inspection timestamps, and serial numbers.
- **Client-Side Spreadsheet Inspection**: In-browser preview for `.xlsx` and `.csv` inspection reports via SheetJS with multi-sheet tab navigation.
- **Enterprise Single Sign-On (SSO)**: OAuth 2.0 / OIDC integrations for Google Workspace, Microsoft 365 / Entra ID, and GitHub with domain-based auto-join.
- **Native Cloudflare Zero Trust Tunneling**: Subprocess-managed encrypted tunnels for public internet access with zero inbound open router ports.
- **Forensic Audit Logging**: Immutable tracking of report downloads, views, and authentication attempts.

---

## 3. Project Structure

```text
app/
  routes/
    admin/           # Master admin management package (dashboard, users, customers, settings, sso, tunnel, diagnostics)
    auth.py          # Session authentication, registration, OAuth callbacks, password resets
    company.py       # Delegated company admin portal for user and recipe assignment
    portal.py        # Report search interface, raw streaming, and file download
  database.py        # Database connection, schema definition, and PRAGMA user_version migrations
  sync_engine.py     # N-1 batch ingestion pipeline and file lock checks
  parser.py          # Dynamic regex filename parser and token extractor
  helpers.py         # Customer scoping, path safety validation, and Fernet encryption
  oauth.py           # Authlib OAuth client registration and database settings loader
  mail.py            # SMTP dispatch, token generation, and email templates
  scheduler.py       # Background daemon for nightly batch execution and zombie batch cleanup
  tunnel_manager.py  # Subprocess orchestration for cloudflared tunnels
  config.py          # Environment variable loader and security configurations
  auth_models.py     # User session model for Flask-Login
tests/               # Unit, integration, E2E (Playwright), and live external test suites
docs/                # In-depth architectural and operational documentation
```

---

## 4. Quickstart

### Prerequisites
- Python 3.10+ (Tested in CI against Python 3.13).

```bash
# 1. Clone repository
git clone https://github.com/4reeb-5yed/suprajit-quality-portal-v2.git
cd suprajit-quality-portal-v2

# 2. Set up virtual environment
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Linux/macOS: source .venv/bin/activate

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Run development server
python web_server.py
```

Open `http://localhost:5000` in your browser. Default initial credentials: Username `bootstrap_admin`, Password `admin123`.

---

## 5. Documentation Index

| Document | Description |
| :--- | :--- |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | High-level architecture, request lifecycles, multi-tenancy model, and ADRs. |
| [`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md) | Table catalogs, columns, indexes, FTS5 virtual tables, and `PRAGMA user_version` migrations. |
| [`docs/API_ROUTES.md`](docs/API_ROUTES.md) | Complete catalog of all endpoints across `auth`, `portal`, `company`, and `admin` blueprints. |
| [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) | Reference of all environment variables and `system_settings` key-value pairs. |
| [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) | Local developer environment, static analysis tools, test execution, and coding gotchas. |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Factory Windows server deployment, NSSM background service installation, and backups. |
| [`docs/ADMIN_GUIDE.md`](docs/ADMIN_GUIDE.md) | Operations manual for master system administrators and customer company admins. |
| [`docs/OAUTH_SETUP.md`](docs/OAUTH_SETUP.md) | Setup instructions for Google Workspace, Microsoft Entra ID, and GitHub OAuth 2.0. |
| [`docs/RELEASING.md`](docs/RELEASING.md) | Versioning details, PyInstaller standalone binary compilation, and CI gate lifecycle. |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Contribution process, branching strategy, and Conventional Commits conventions. |
| [`SECURITY.md`](SECURITY.md) | Threat mitigation matrix, transport layer requirements, and vulnerability reporting. |
| [`tests/README.md`](tests/README.md) | Test suite markers (`unit`, `integration`, `e2e`, `live_external`) and execution commands. |
| [`CHANGELOG.md`](CHANGELOG.md) | Chronological record of release features, fixes, and architectural enhancements. |

---

## 6. License & Contact

Maintained by the Suprajit Quality Engineering Team. Internal proprietary distribution for authorized automotive partners and factory plant sites.
