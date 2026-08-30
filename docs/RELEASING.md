# Release & Build Process

This document describes versioning conventions, executable binary compilation, CI quality gates, and the release lifecycle for the Suprajit Quality Portal.

---

## 1. Versioning & Package Declarations

### Versioning Scheme
The project adheres to [Semantic Versioning](https://semver.org/).

> **Note on Versioning Contexts**:
> - `pyproject.toml` declares version `0.1.0` (standard Python packaging initial release baseline).
> - The application UI, changelog, and documentation refer to the **V3** series, representing the multi-tenant architecture with dynamic filename parsing, SSO, and native tunneling.

`CHANGELOG.md` is maintained following the [Keep a Changelog](https://keepachangelog.com/) standard with an `[Unreleased]` section tracking pending updates.

---

## 2. CI Pipeline & Quality Gates

Automated continuous integration is defined in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) and runs on pushes/PRs to `master` and `v3`:

1. **Stage 1: Static Analysis & Security Gate**:
   - `bandit`: Scans for security vulnerabilities (`bandit -r app/ -lll`).
   - `ruff`: Checks Python linting and formatting (`ruff check app/`, `ruff format --check app/`).
   - `mypy`: Type checks code (`mypy app/ --ignore-missing-imports`).
   - `pip-audit`: Checks dependencies for known CVEs.
   - `gitleaks`: Scans commits for accidental secret leakage.
2. **Stage 2: Fast Unit & Integration Gate**:
   - Installs project dependencies.
   - Runs `pytest -m "unit or integration"` with branch coverage.
3. **Stage 3: E2E & Live External Validation Gate**:
   - Provisions `cloudflared` binary and LibreOffice.
   - Installs Playwright Chromium browser binaries.
   - Runs `pytest -m "e2e or live_external"`.
   - Executes mutation testing quality checks via `mutmut`.

---

## 3. Building the Standalone Windows Executable

The production distribution is packaged as a standalone executable directory using PyInstaller and Waitress WSGI.

### Prerequisites
- Windows 10/11 or Windows Server (64-bit).
- Python 3.10+ virtual environment with dependencies installed (`pip install -e ".[dev]"`).

### Build Script (`build.bat`)
Run the compilation batch script from the repository root:

```cmd
.\build.bat
```

### Build Workflow:
1. Cleans existing `build/` and `dist/` directories.
2. Invokes PyInstaller with [`SuprajitQualityPortal.spec`](../SuprajitQualityPortal.spec):
   - Bundles `app/templates` and `app/static` into the distribution.
   - Generates `dist/SuprajitQualityPortal/SuprajitQualityPortal.exe`.
3. Copies configuration templates and deployment scripts into `dist/SuprajitQualityPortal/`:
   - `.env.example`
   - `install_service.bat`
   - `uninstall_service.bat`
   - `service/nssm.exe` (Non-Sucking Service Manager)

---

## 4. Verifying the Production Binary

1. Navigate to the build output directory:
   ```cmd
   cd dist\SuprajitQualityPortal
   ```
2. Create a test `.env` file:
   ```cmd
   copy .env.example .env
   ```
3. Run the executable directly:
   ```cmd
   .\SuprajitQualityPortal.exe
   ```
4. Verify `http://localhost:5000` loads the login/bootstrap interface.
