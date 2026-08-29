# Architecture & Decision Records (ADR) - Version 3.0 Enterprise

This document captures the architectural decisions, structural constraints, and technological rationale governing the **Suprajit Quality Portal (V3)**.

---

## 🏛️ ADR Index

### 1. Ingestion Strategy: N-1 Batch Ingestion vs Real-Time Watchdogs
- **Decision**: Process files strictly from the previous calendar day ($N-1$).
- **Rationale**: Real-time file system watchers (e.g. `watchdog`) fail when manufacturing machines slowly write large Excel files over network shares or when plant workers leave spreadsheets open. The N-1 lifecycle guarantees all files are fully flushed, closed, and unlocked.
- **Safety Heuristic**: Combined with `ensure_file_safe()`, verifying OS write locks before reading.

---

### 2. High-Concurrency Storage: SQLite WAL vs Client-Server Relational DBs
- **Decision**: Dedicated single-file SQLite database configured strictly in Write-Ahead Logging (`WAL`) mode with `NORMAL` synchronous mode and 5000ms busy timeouts.
- **Rationale**: Eliminates the operational and maintenance burden of managing PostgreSQL or MySQL background services on plant PCs. SQLite WAL enables concurrent readers while batch indexing proceeds in the background with zero lock contention. Backups require copying a single `portal.db` file.

---

### 3. Spreadsheet Rendering: Client-Side SheetJS WebAssembly vs Server-Side LibreOffice/Python Conversion
- **Decision**: Stream authorized binary file blobs directly to the client browser and render interactively using **SheetJS (xlsx.js)**.
- **Rationale**: Converting complex Excel spreadsheets on the server using headless LibreOffice or Python libraries (e.g. `openpyxl`, `pandas`) consumes immense CPU and RAM, creating severe server bottlenecks under multi-user traffic. Client-side WebAssembly execution offloads 100% of rendering computational cost to the client device while preserving workbook tab navigation.

---

### 4. Enterprise Identity: Dual Authentication (Local RBAC + OAuth 2.0 / SSO)
- **Decision**: Turnkey OAuth 2.0 integration for Microsoft 365 / Entra ID, Google Workspace, and GitHub with automated Corporate Domain Whitelisting.
- **Rationale**: Tier-1 automotive clients (TVS, Mahindra, Tata) require SSO governance. Users signing in via corporate email domains automatically join their organization tenant without manual provisioning overhead, while preserving local admin fallback during internet interruptions.

---

### 5. Remote Connectivity: Cloudflare Zero Trust Tunnels vs Public Port-Forwarding
- **Decision**: Native process orchestration of Cloudflare Zero Trust Tunnels (`cloudflared`).
- **Rationale**: Factory servers sit behind restrictive corporate NATs and firewalls. Port-forwarding port 5000 exposes factory networks to brute-force attacks. Cloudflare tunnels establish outbound-only encrypted tunnels, providing enterprise DDoS protection, automatic SSL termination, and immediate public access without modifying router configurations.

---

### 6. Dynamic Parsing Architecture: Configurable Regex vs Hardcoded String Slicing
- **Decision**: Dynamic regex engine with database-persisted named capture groups (`(?P<recipe>...)`, `(?P<serial>...)`).
- **Rationale**: Manufacturing part naming conventions evolve over time. Hardcoded string parsers require rebuilding and redeploying binary executables. The dynamic engine allows IT administrators to add or adjust regex patterns directly in the web UI with interactive validation.

---

### 7. Quality Assurance: 3-Way Test Defense Matrix
- **Decision**: Layered 100+ automated test suites spanning Unit Isolation, Multi-Tenant Security (OWASP ASVS), and End-to-End browser smoke checks.
- **Rationale**: Guarantees zero regressions across cryptographic deduplication, multi-tenant company isolation boundaries, and executable binary compilation.

