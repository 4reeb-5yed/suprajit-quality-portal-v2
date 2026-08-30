# Development & Contributor Guide

This document outlines the local development setup, code quality tools, test execution workflows, and project conventions for contributors to the Suprajit Quality Portal.

---

## 1. Local Development Environment Setup

### Prerequisites
- **Python**: Python 3.10+ (Tested in CI against Python 3.13).
- **Git**: Installed and available in your shell.

### Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/4reeb-5yed/suprajit-quality-portal-v2.git
   cd suprajit-quality-portal-v2
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv

   # On Windows:
   .venv\Scripts\activate

   # On Linux / macOS:
   source .venv/bin/activate
   ```

3. **Install editable development package**:
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install Playwright browser binaries (for E2E tests)**:
   ```bash
   python -m playwright install --with-deps chromium
   ```

5. **Run the local development server**:
   ```bash
   python web_server.py
   ```
   The portal will start on `http://localhost:5000`.

---

## 2. Test Suite Execution & Markers

The test suite uses custom pytest markers to partition tests by operational requirements. See [`tests/README.md`](../tests/README.md) for full marker definitions.

### Fast Unit & Integration Tier
Runs pure algorithmic tests, database migrations, and Flask endpoint tests without launching browsers or subprocesses:
```bash
pytest -m "unit or integration" -v
```

### Full Test Suite (including Playwright and Live Network Tests)
```bash
pytest -v
```

---

## 3. Linting, Formatting & Security Scanners

Before submitting changes or opening pull requests, run all static analysis checks locally:

```bash
# 1. Ruff Lint Check
python -m ruff check app/ tests/

# 2. Ruff Formatting Check
python -m ruff format --check app/ tests/

# 3. Mypy Type Checking
python -m mypy app/ --ignore-missing-imports

# 4. Bandit Security Scan
python -m bandit -r app/ -lll

# 5. Dependency Vulnerability Audit
python -m pip_audit
```

---

## 4. Known Gotchas & Architectural Rules

### Rule A: Safe File Writing & BOM Prevention
- **Never create or modify source files via shell heredocs or PowerShell here-strings.** Shell command interpolation often corrupts indentation or inserts a UTF-8 Byte Order Mark (BOM: `\xef\xbb\xbf`), which breaks Python module parsing.
- Always use standard direct file writing tools or native Python `open(..., encoding="utf-8")`.

### Rule B: Path Traversal Argument Order
- When calling `is_safe_path()` from [`app/helpers.py`](../app/helpers.py), always supply the `base_dir` first and the `target_path` second:
  ```python
  # Correct:
  is_safe_path(current_app.config["STORAGE_FOLDER"], target_path)

  # Incorrect (Inverts containment check):
  # is_safe_path(target_path, current_app.config["STORAGE_FOLDER"])
  ```
