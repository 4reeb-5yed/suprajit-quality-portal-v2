# 🏭 Suprajit Quality Portal (V2)

![Status](https://img.shields.io/badge/Status-Production-success)
![Security](https://img.shields.io/badge/Security-OWASP_Compliant-blue)
![Database](https://img.shields.io/badge/Database-SQLite_WAL-orange)
![License](https://img.shields.io/badge/License-Proprietary-red)

An enterprise-grade, offline-first Quality Management System (QMS) built specifically for Suprajit. Designed to ingest, index, and securely serve factory quality reports to external clients (e.g., TVS, Mahindra) over the internet with zero IT maintenance overhead.

---

## 🚀 Installation & Deployment (Production)

This software is pre-compiled for deployment. The target server **does not** need Python installed.

### Option A: Standard Windows Server Deployment (Recommended)
1. **Download:** Navigate to the **[Releases](../../releases)** tab on GitHub and download the latest `SuprajitQualityPortal_V2.zip`.
2. **Extract:** Unzip the folder to a permanent location on the factory server (e.g., `C:\Program Files\SuprajitPortal`).
3. **Configure:** Inside the folder, rename `.env.example` to `.env`. Open it in Notepad and enter your SMTP email credentials (required for Password Resets).
4. **Install:** Right-click the `install_service.bat` file and select **"Run as Administrator"**. 
5. **Access:** The portal is now permanently running as a background Windows Service. Open a web browser and go to `http://localhost:5000`.

### Option B: Docker Deployment (Advanced IT Teams)
If your IT infrastructure prefers Linux or containerization:
```bash
# 1. Clone the repository
git clone <repository-url>
cd suprajit_v2

# 2. Configure environment variables
copy .env.example .env
# (Edit .env with your SMTP credentials)

# 3. Spin up the container in the background
docker-compose up -d
```

---

## 📚 Documentation Directory

To maintain a clean repository, all detailed manuals are categorized below:

* 🚀 [Full Deployment & IT Guide](docs/DEPLOYMENT.md) - Deep dive into network setup, Reverse Proxies, and HTTPS.
* 🛠️ [Administrator Guide](docs/ADMIN_GUIDE.md) - How to onboard clients, map recipes, and use the Repair Dashboard.
* 🔐 [Security Policy](SECURITY.md) - Overview of OWASP defenses, Scrypt cryptography, and CSRF.
* 🏗️ [Architecture & Decision Records](docs/ARCHITECTURE.md) - Why SQLite WAL and Waitress were chosen over traditional cloud architectures.

---
*Copyright (c) 2026 Areeb Syed. All Rights Reserved.*
