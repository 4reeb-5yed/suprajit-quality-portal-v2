# Suprajit Quality Portal V2

An enterprise-grade, lightweight Quality Management System (QMS) built for Windows Server. It automatically parses factory Excel reports, extracts metadata via Regex, stores it in a high-concurrency SQLite WAL database, and serves it to a multi-tenant customer portal.

## Quick Start (Development)

To clone the repository and run the portal in a local development environment, run the exact commands below:

```bash
# 1. Clone the repository
git clone https://github.com/4reeb-5yed/suprajit-quality-portal-v2.git
cd suprajit-quality-portal-v2

# 2. Create and activate a Python Virtual Environment
python -m venv .venv
# On Windows Command Prompt:
.venv\Scripts\activate.bat
# On Windows PowerShell:
.venv\Scripts\Activate.ps1

# 3. Install required dependencies
pip install -r requirements.txt

# 4. Run the local development server (with hot-reloading)
python run.py
```
*Note: The application will be available at `http://localhost:5000`. The default admin login is created automatically (Username: `bootstrap_admin`, Password: `admin123`). You will be forced to change this upon first login.*

## Running the Automated Test Suite

We enforce a strict Three-Way Defense Pipeline. To verify the system's mathematical integrity before building:

```bash
python -m pytest tests/test_sync_engine_dimensions.py tests/test_ultimate.py -v
```

## Compiling for Production (Windows .exe)

To compile the entire Python ecosystem into a single standalone `.exe` (which runs via the Waitress production server):

```bash
# Run the automated build script
.\build.bat
```
This will generate the production package in the `dist/SuprajitQualityPortal` folder.

## Production Execution

1. Copy the contents of `dist/SuprajitQualityPortal` to your server's `Z:\SuprajitQualityPortal_V2` drive.
2. Double-click `SuprajitQualityPortal.exe`.
3. The server will run in the background on Port 5000 (accessible across the LAN via the server's IP address).
4. Configure the "Watched Folder" path in the Admin -> Settings UI to point to your factory's Excel output directory.
