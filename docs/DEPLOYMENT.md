# Factory IT & Production Deployment Guide (V3)

This guide is for the Systems Administrator deploying the standalone **Suprajit Quality Portal (V3)** on a factory server or plant PC.

---

## 💻 Server Prerequisites
- **Operating System**: Windows Server 2016+, Windows 10/11 (64-bit).
- **Network Requirements**: Local LAN access to the factory report directory.
- **Port**: Local Port `5000` (internal only).
- **Internet Exposure**: Zero incoming ports needed when using the integrated Cloudflare Zero Trust Tunnel.

---

## 🛠️ Step-by-Step Installation

### Step 1: Extract Release Artifacts
1. Download `SuprajitQualityPortal_V2.zip` from GitHub Releases or build via `.\build.bat`.
2. Extract to a permanent drive directory (recommended: `C:\Program Files\SuprajitQualityPortal` or `Z:\SuprajitQualityPortal`).

### Step 2: Configure Environment (`.env`)
1. Copy `.env.example` to `.env`.
2. Open in Notepad and set your secret key and initial configuration:
   ```ini
   SECRET_KEY=generate_a_random_32_character_string
   DATABASE_PATH=data/portal.db
   STORAGE_FOLDER=data/storage
   WATCHED_FOLDER=Z:\Factory_Quality_Outputs
   ```

### Step 3: Install Windows Background Service (NSSM)
To ensure the application starts automatically upon server reboot and auto-heals from crashes:
1. Open PowerShell / Command Prompt as **Administrator**.
2. Run:
   ```cmd
   .\install_service.bat
   ```
3. This registers the Windows Service `SuprajitQualityPortal` and opens local Port 5000 in Windows Defender Firewall.

---

## 🌐 Internet Exposure (Zero Open Inbound Ports)

### Option A: Integrated 1-Click Cloudflare Tunnel (Recommended)
1. Download `cloudflared.exe` (or place in system PATH).
2. Login to the portal as `bootstrap_admin` &rarr; Go to **Admin &rarr; Settings &rarr; Cloudflare Tunnel Manager**.
3. Choose either **Free Ephemeral Tunnel** or enter your **Named Cloudflare Zero Trust Token**.
4. Click **Start Tunnel**.
5. The portal is now immediately live over encrypted HTTPS with automatic DDoS mitigation.

### Option B: On-Premise Reverse Proxy (IIS / NGINX)
If using an internal enterprise load balancer:
1. Bind your SSL certificate to your corporate domain (e.g. `quality.suprajit.com`).
2. Set reverse proxy upstream to `http://127.0.0.1:5000`.
3. Ensure the `X-Forwarded-For` and `X-Forwarded-Proto` headers are passed.

---

## 🔐 Initial Setup Wizard & Security Hardening
1. Navigate to `http://localhost:5000` in your browser.
2. The **Mandatory Setup Wizard** will force you to change the initial `admin123` password and register your administrator email.
3. Configure your corporate SMTP server in **Admin &rarr; Settings** for transactional password reset and invite deliveries.
4. Enter the **Watched Folder** containing plant Excel files.
5. In **Admin &rarr; Repair & Diagnostics**, click **Dry Run** to verify metadata parsing against live factory files.

