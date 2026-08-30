# Factory Deployment & Operations Guide

This guide details how to install, configure, and maintain the Suprajit Quality Portal on a factory Windows server or edge PC.

---

## 1. System Requirements & Prerequisites

- **Operating System**: Windows Server 2016+, Windows 10/11 (64-bit).
- **Network**: Local Area Network (LAN) access to factory quality output folders.
- **Port**: Local Port `5000` (internal WSGI listener).
- **Inbound Ports**: 0 inbound ports required when using Cloudflare Zero Trust Tunnels.

---

## 2. Installation via Standalone Distribution

The compiled distribution requires no separate Python or database installation.

1. **Extract Distribution Package**:
   - Extract the compiled `SuprajitQualityPortal/` directory to a permanent path (e.g. `C:\Program Files\SuprajitQualityPortal` or `C:\SuprajitQualityPortal`).

2. **Configure Environment (`.env`)**:
   - Copy `.env.example` to `.env`:
     ```ini
     SECRET_KEY=generate_a_secure_random_string
     PORT=5000
     HOST=0.0.0.0
     DATABASE_PATH=data/portal.db
     STORAGE_FOLDER=storage/
     ```

3. **Install Background Windows Service (`install_service.bat`)**:
   - Open Command Prompt or PowerShell as **Administrator**.
   - Run:
     ```cmd
     install_service.bat
     ```
   - This script registers `SuprajitQualityPortal.exe` as a native Windows service via NSSM, configures automatic restart on reboot/crash, and opens port 5000 in Windows Defender Firewall.

---

## 3. Remote Access & Tunneling

### Option A: Cloudflare Zero Trust Tunnel (Outbound Encrypted HTTPS)
1. Ensure `cloudflared.exe` is placed in the project folder or system `PATH`.
2. Navigate to **Admin &rarr; Settings &rarr; Cloudflare Tunnel Manager**.
3. Choose either:
   - **Quick Tunnel**: Starts a free, ephemeral `trycloudflare.com` tunnel.
   - **Named Tunnel Token**: Enter your persistent Cloudflare Zero Trust Tunnel token.
4. Click **Start Tunnel**. Outbound invitation emails and password reset links will automatically use the active public URL.

### Option B: Local Network / Reverse Proxy (IIS / NGINX)
- Configure an internal reverse proxy upstream to `http://127.0.0.1:5000`.
- Ensure `X-Forwarded-For` and `X-Forwarded-Proto` headers are passed.

---

## 4. Backup & Disaster Recovery

Because all application data and metadata are stored in SQLite:

1. **Backup Procedure**:
   - Copy the database file `data/portal.db` to a backup directory or network drive. Because SQLite is operating in WAL mode, ensure `data/portal.db-wal` and `data/portal.db-shm` are copied if active.
2. **Restore Procedure**:
   - Stop the Windows Service:
     ```cmd
     net stop SuprajitQualityPortal
     ```
   - Replace `data/portal.db` with the backup copy.
   - Restart the Windows Service:
     ```cmd
     net start SuprajitQualityPortal
     ```
