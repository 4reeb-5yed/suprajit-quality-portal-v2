# Test Suite Guide: Categories, Execution & Prerequisites

The Suprajit Quality Portal test suite is partitioned into four distinct categories via custom pytest markers. This enables fast local feedback cycles as well as staged CI pipeline execution.

---

## 1. Test Categories & Markers

| Marker | Category Description | Included Test Files | Local Execution Command |
| :--- | :--- | :--- | :--- |
| `unit` | Pure mathematical & algorithmic functions. No Flask application context, no database access. | `test_property_filename_parser.py`, `test_property_security_helpers.py` | `pytest -m "unit"` |
| `integration` | Multi-endpoint Flask routes, database schema/transactions, RBAC, ASVS security rules, rate limiting. | `test_admin_deep_coverage.py`, `test_auth_deep_coverage.py`, `test_v3_company_rbac.py`, `test_portal_deep_coverage.py`, `test_company_deep_coverage.py`, `test_schema_migrations.py`, etc. | `pytest -m "integration"` |
| `e2e` | Full end-to-end browser journeys via Playwright (login, search, table rendering, exports). | `test_e2e_playwright_journeys.py` | `pytest -m "e2e"` |
| `live_external` | Live integration with network sockets, local background processes, real SMTP servers, OIDC providers, and Cloudflare tunnel binaries. | `test_live_smtp_mail_delivery.py`, `test_live_oauth_oidc_protocol.py`, `test_attack_surface_tunnel_manager.py`, `test_tunnel_manager_coverage.py` | `pytest -m "live_external"` |

---

## 2. Local Execution Commands

### Fast Feedback (Unit + Integration)
Runs quickly without requiring browser binaries or external subprocesses:
```bash
pytest -m "unit or integration" -v
```

### Real Browser & Subprocess Validation (E2E + Live External)
```bash
pytest -m "e2e or live_external" -v
```

### Complete Test Suite
```bash
pytest -v
```

---

## 3. Environment & Tooling Prerequisites

1. **Python Dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

2. **Playwright Browser Binaries (For e2e)**:
   ```bash
   python -m playwright install --with-deps chromium
   ```

3. **Cloudflare Tunnel Executable (For live_external tunnel tests)**:
   - Ensure `cloudflared` is installed and available in the system `PATH` (or placed in the project root).
   - On Windows: `winget install Cloudflare.cloudflared` or download `cloudflared.exe`.
   - On Linux/CI: Download official `cloudflared-linux-amd64.deb` and install via `dpkg`.
