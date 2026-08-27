# 🏭 Suprajit Quality Portal (V2)

![Status](https://img.shields.io/badge/Status-Production-success)
![Security](https://img.shields.io/badge/Security-OWASP_Compliant-blue)
![Database](https://img.shields.io/badge/Database-SQLite_WAL-orange)
![License](https://img.shields.io/badge/License-Proprietary-red)

An enterprise-grade, offline-first Quality Management System (QMS) portal built specifically for Suprajit. Designed to ingest, index, and securely serve factory quality reports to external clients (e.g., TVS, Mahindra) over the internet with zero IT maintenance overhead.

---

## 🏗 Architecture Overview

This software is heavily armored for both Factory environments (offline file ingestion) and Public Web environments (secure client portal). 

* **The Web Server:** Powered by **Waitress**, a production-grade WSGI server capable of defending against slow-loris attacks and handling high concurrent traffic.
* **The Database:** Powered by **SQLite WAL (Write-Ahead Logging)**, guaranteeing 100% ACID compliance and complete immunity to deadlocks/race conditions during massive background ingestions.
* **The Frontend:** Built with **Tailwind CSS** and **HTMX**, providing a frictionless, lightning-fast Single Page Application (SPA) experience without the bloat of React/Angular.
* **The Engine:** Features an N-1 day ingestion lifecycle and an `ensure_file_safe()` heuristic module to mathematically prevent OS file-locking crashes.

## 📚 Documentation Directory

To maintain a clean repository, all detailed documentation is categorized below:

* 🔐 [Security & Cryptography](SECURITY.md) - Overview of OWASP defenses, Scrypt, and CSRF.
* 🚀 [Deployment & IT Guide](docs/DEPLOYMENT.md) - Step-by-step installation instructions for Factory IT.
* 🛠️ [Admin & Troubleshooting Guide](docs/ADMIN_GUIDE.md) - How to use the Repair Dashboard, Purge tool, and manage clients.
* 🏗️ [Core Blueprint](ARCHITECTURE_BLUEPRINT.md) - Detailed breakdown of the N-1 ingestion engine.

## 🚀 Quick Start (Development)

If you are a developer compiling this software from source:

```bash
# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install dependencies
pip install -r pyproject.toml

# 3. Configure local environment
copy .env.example .env

# 4. Build executable
.\build.bat
```
