# Contributing to Suprajit Quality Portal (V3)

Thank you for contributing to the Suprajit Quality Portal! This guide details local setup, test execution, architectural conventions, and critical safety rules for maintainers and contributors.

---

## 1. Local Development Setup

Follow the standard setup instructions from [README.md](README.md):

1. **Clone the repository**:
   ```bash
   git clone https://github.com/4reeb-5yed/suprajit-quality-portal-v2.git
   cd suprajit-quality-portal-v2
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   # source .venv/bin/activate
   ```

3. **Install dependencies in editable development mode**:
   ```bash
   pip install -e ".[dev]"
   python -m playwright install --with-deps chromium
   ```

4. **Launch development server**:
   ```bash
   python web_server.py
   ```

---

## 2. Test Suite Tiers & Markers

The test suite uses custom pytest markers to separate fast feedback from live external operations. Please consult [tests/README.md](tests/README.md) for full execution commands, marker details, and environment prerequisites.

- **Fast Tier (Unit + Integration)**: `pytest -m "unit or integration" -v`
- **Live Tier (E2E + Live External)**: `pytest -m "e2e or live_external" -v`
- **Complete Suite**: `pytest -v`

---

## 3. Package Architecture: `app/routes/admin/`

The admin subsystem is modularized into cohesive functional areas:

- `app/routes/admin/__init__.py`: Defines the `admin_bp` blueprint, the `before_request` security guard (enforcing the bootstrap setup wizard trap), and registers sibling submodules.
- `app/routes/admin/dashboard.py`: Top-level admin metrics dashboard, batch run history, and security/quality evidence metrics (`/evidence`).
- `app/routes/admin/users.py`: Master admin user management, bulk CSV/text onboarding, user activation toggling, and user deletion.
- `app/routes/admin/customers.py`: Client tenant CRUD, recipe grant/revocation, granular user recipe scopes (`ALL` vs `CUSTOM`), allowed auto-join domains, and customer suspension toggles.
- `app/routes/admin/settings.py`: System-wide settings (ingestion schedule, storage paths, SMTP credentials, telemetry alerts, regex pattern configuration).
- `app/routes/admin/sso.py`: Enterprise Single Sign-On configuration persistence (Google Workspace, Microsoft 365, GitHub OAuth credentials).
- `app/routes/admin/tunnel.py`: Subprocess orchestration for Cloudflare Zero Trust tunnels (quick tunnels and named token-authenticated tunnels).
- `app/routes/admin/diagnostics.py`: Live system log viewer, SQLite WAL database size telemetry, schema migration versioning display, and manual repair/sync tools.

---

## 4. Known Gotchas & Coding Rules

### Rule A: File-Writing Encoding & BOM Prevention
- **Never generate code files via shell scripts, PowerShell here-strings, or heredocs.** These mechanisms frequently introduce UTF-8 Byte Order Marks (BOM `\xef\xbb\xbf`) or corrupt tab/backtick characters (`\t`, ``` ` ```) due to shell variable interpolation.
- Write files directly through standard editor tooling or Python's native `open(path, 'w', encoding='utf-8')`.
- Always verify that written files start with valid content and not a BOM byte sequence.

### Rule B: Path Traversal Argument Order
- When validating file paths with `is_safe_path()`, always pass `base_dir` first and `target_path` second:
  ```python
  # Correct:
  is_safe_path(base_folder, requested_file_path)

  # Incorrect (Vulnerability / Bug):
  # is_safe_path(requested_file_path, base_folder)
  ```

---

## 5. Commit Message Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/) for all contributions:

- `feat:` New features or functional enhancements
- `fix:` Bug fixes and security patches
- `refactor:` Code restructuring without behavior changes
- `docs:` Documentation additions or updates
- `test:` New tests or test infrastructure refactoring
- `chore:` Dependency bumps, CI/CD tweaks, or build configurations
