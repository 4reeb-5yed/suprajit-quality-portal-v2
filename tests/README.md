# Test Suite Guide: Categories, Execution & Prerequisites

The Suprajit Quality Portal test suite is partitioned into four distinct categories via custom pytest markers. This enables fast local feedback cycles as well as staged CI pipeline execution.

---

## 1. Test Categories & Markers

| Marker | Category Description | Included Test Files | Local Execution Command |
| :--- | :--- | :--- | :--- |
| unit | Pure mathematical & algorithmic functions. No Flask application context, no database access. | 	est_property_filename_parser.py, 	est_property_security_helpers.py | pytest -m "unit" |
| integration | Multi-endpoint Flask routes, database schema/transactions, RBAC, ASVS security rules, rate limiting. | 	est_admin_deep_coverage.py, 	est_auth_deep_coverage.py, 	est_v3_company_rbac.py, 	est_portal_deep_coverage.py, 	est_company_deep_coverage.py, etc. | pytest -m "integration" |
| e2e | Full end-to-end browser journeys via Playwright (login, search, table rendering, exports). | 	est_e2e_playwright_journeys.py | pytest -m "e2e" |
| live_external | Live integration with network sockets, local background processes, real SMTP servers, OIDC providers, and Cloudflare tunnel binaries. | 	est_live_smtp_mail_delivery.py, 	est_live_oauth_oidc_protocol.py, 	est_attack_surface_tunnel_manager.py, 	est_tunnel_manager_coverage.py | pytest -m "live_external" |

---

## 2. Local Execution Commands

### Fast Feedback (Unit + Integration)
Runs in ~3 minutes without requiring browser binaries or external subprocesses:
\\\ash
pytest -m "unit or integration" -v
\\\

### Real Browser & Subprocess Validation (E2E + Live External)
\\\ash
pytest -m "e2e or live_external" -v
\\\

### Complete Test Suite (All 199 Items)
\\\ash
pytest -v
\\\

---

## 3. Environment & Tooling Prerequisites

1. **Python Dependencies**:
   \\\ash
   pip install -e ".[dev]"
   \\\

2. **Playwright Browser Binaries (For e2e)**:
   \\\ash
   python -m playwright install --with-deps chromium
   \\\

3. **Cloudflare Tunnel Executable (For live_external tunnel tests)**:
   - Ensure cloudflared is installed and available in the system \PATH\ (or placed in the project root).
   - On Windows: winget install Cloudflare.cloudflared or download cloudflared.exe.
   - On Linux/CI: Download official cloudflared-linux-amd64.deb and install via dpkg.
