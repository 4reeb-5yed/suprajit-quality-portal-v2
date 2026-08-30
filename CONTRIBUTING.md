# Contributing to Suprajit Quality Portal

Thank you for contributing to the Suprajit Quality Portal. This document outlines how to propose changes, commit conventions, and code review expectations.

For local environment setup, testing commands, and linting instructions, please refer to [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

---

## 1. Proposing Changes & Branch Strategy

1. **Active Branches**:
   - `master`: Production release branch.
   - `v3`: Active development and refactoring branch for the V3 release series.
2. **Branching Model**:
   - Create a feature or bugfix branch from `v3`:
     ```bash
     git checkout -b fix/issue-description
     ```
3. **Submitting a Pull Request**:
   - Open a pull request against the `v3` branch.
   - Ensure all automated CI gates pass before requesting review.

---

## 2. Commit Message Conventions

We adhere to [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New features or functional additions.
- `fix:` Bug fixes and security patches.
- `refactor:` Code restructuring without behavior changes.
- `build:` Build configuration, packaging, or dependency changes.
- `docs:` Documentation additions or updates.
- `test:` Test suite additions or refactoring.
- `chore:` Maintenance tasks, CI updates, or housekeeping.

### Example:
```text
feat(auth): add Microsoft 365 OAuth 2.0 provider integration
fix(parser): handle filenames with multiple space-delimited copy suffixes
```

---

## 3. Code Review & Quality Expectations

Every pull request is evaluated against:
1. **Verification**: Zero regressions across all 170+ unit and integration tests.
2. **Security Standards**: Parameterized database queries, strict tenancy isolation via `customer_scope()`, and path safety checks via `is_safe_path()`.
3. **Static Analysis**: Zero errors reported by `ruff`, `mypy`, `bandit`, and `pip-audit`.
4. **Documentation**: Updates to [`docs/API_ROUTES.md`](docs/API_ROUTES.md), [`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md), or [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) when routes, schemas, or config keys are modified.
