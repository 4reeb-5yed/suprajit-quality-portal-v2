# Suprajit Quality Portal (V2)

![Status](https://img.shields.io/badge/Status-Production-success)
![Security](https://img.shields.io/badge/Security-OWASP_Compliant-blue)
![Database](https://img.shields.io/badge/Database-SQLite_WAL-orange)
![License](https://img.shields.io/badge/License-Proprietary-red)

An enterprise-grade, offline-first Quality Management System (QMS) built specifically for Suprajit. Designed to ingest, index, and securely serve factory quality reports to external clients over the internet with zero IT maintenance overhead.

---

## 1. Production Deployment

This software is pre-compiled for deployment. The target server does not need Python installed.

### Option A: Standard Windows Server Deployment (Recommended)
1. Navigate to the **Releases** tab on GitHub and download the latest `SuprajitQualityPortal_V2.zip`.
2. Unzip the folder to a permanent location on the factory server (e.g., `C:\Program Files\SuprajitPortal`).
3. Inside the folder, rename `.env.example` to `.env`. Open it in Notepad and enter your SMTP email credentials.
4. Right-click the `install_service.bat` file and select **"Run as Administrator"**. 
5. The portal is now permanently running as a background Windows Service at `http://localhost:5000`.

### Option B: Docker Containerization
If your IT infrastructure prefers Linux or containerization:
```bash
git clone <repository-url>
cd suprajit_v2
copy .env.example .env
# Edit .env with your SMTP credentials, then run:
docker-compose up -d
```

---

## 2. Local Development & Source Execution

To run, modify, or test the application directly from the Python source code:

```bash
# 1. Clone the repository
git clone <repository-url>
cd suprajit_v2

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install the application and dependencies
pip install -e .

# 4. Configure local environment variables
copy .env.example .env

# 5. Run the production Waitress server
python web_server.py
```

---

## 3. Documentation Directory

All detailed manuals are categorized below:
* [Deployment & IT Guide](docs/DEPLOYMENT.md) - Deep dive into network setup, Reverse Proxies, and HTTPS.
* [Administrator Guide](docs/ADMIN_GUIDE.md) - How to onboard clients, map recipes, and use the Repair Dashboard.
* [Security Policy](SECURITY.md) - Overview of OWASP defenses, Scrypt cryptography, and CSRF.
* [Architecture & Decision Records](docs/ARCHITECTURE.md) - Why SQLite WAL and Waitress were chosen.

---
*Copyright (c) 2026 Areeb Syed. All Rights Reserved.*
