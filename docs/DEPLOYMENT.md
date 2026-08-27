# 🚀 Factory IT Deployment Guide

This guide is for the Systems Administrator deploying the pre-compiled `SuprajitQualityPortal_V2.zip` executable onto a factory server.

## Prerequisites
* A Windows Server / PC (Windows 10/11 or Windows Server 2016+).
* Port `5000` available on the host machine.
* A target folder containing the daily PDF/Excel quality reports.

---

## Step-by-Step Installation

### 1. Extract the Application
1. Download `SuprajitQualityPortal_V2.zip` from the GitHub Releases page.
2. Extract the folder to a permanent location (e.g., `C:\Program Files\SuprajitQualityPortal`).

### 2. Configure the SMTP Email Server (Required)
For the "Forgot Password" self-service workflow to function, the application must be able to send emails.
1. Inside the extracted folder, locate `.env.example`.
2. Rename it to `.env`.
3. Open it in Notepad and enter your SMTP credentials.
   *(Example for Office365: `MAIL_SERVER=smtp.office365.com`)*

### 3. Install the Windows Background Service
To ensure the portal automatically starts when the server reboots and recovers from crashes, we use a service wrapper (NSSM).
1. Right-click `install_service.bat` and select **"Run as Administrator"**.
2. The script will automatically register the `.exe` as a Windows Service and open Port 5000 in the Windows Defender Firewall.
3. The portal is now live at `http://localhost:5000`.

### 4. Configure the Application (First Boot)
1. Open a web browser on the server and navigate to `http://localhost:5000`.
2. You will be automatically redirected to the **Setup Wizard**.
3. Create the Master Admin account. (Do not lose these credentials).
4. Go to **Settings** and configure the "Search Root" (the path to the factory report folder).

---

## Network Exposure (HTTPS)
To expose this portal to the public internet securely:
1. Do **not** port-forward port 5000 directly to the internet.
2. Install a Reverse Proxy (like IIS, NGINX, or an internal enterprise load balancer).
3. Bind an SSL Certificate (HTTPS) to your domain (`quality.suprajit.com`).
4. Route the proxy traffic to `localhost:5000`.
