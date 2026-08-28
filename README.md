# Suprajit Quality Portal V2

A lightweight Multi-Tenant Quality Report Indexing, Traceability, and Retrieval System built for Windows Server. It automatically parses factory Excel reports, extracts metadata via Regex, stores it in a high-concurrency SQLite WAL database, and serves it to a multi-tenant customer portal.

## Quick Start (Development)

Follow these steps to set up the repository on your local machine. **Each command below can be copied and run individually.**

**1. Clone the repository:**
```bash
git clone https://github.com/4reeb-5yed/suprajit-quality-portal-v2.git
```

**2. Enter the directory:**
```bash
cd suprajit-quality-portal-v2
```

**3. Create a Python Virtual Environment:**
```bash
python -m venv .venv
```

**4. Activate the Virtual Environment (Windows Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

*(Or, if you are using Windows PowerShell, use this instead):*
```powershell
.venv\Scripts\Activate.ps1
```

**5. Install all required dependencies:**
```bash
pip install -e .
```

**6. Run the local development server:**
```bash
python run.py
```
*Note: The application will be available at `http://localhost:5000`. The default admin login is created automatically (Username: `bootstrap_admin`, Password: `admin123`). You will be forced to change this upon first login.*

---

## Running the Automated Test Suite

We enforce a strict Three-Way Defense Pipeline. To verify the system's mathematical integrity before building, run this command:

```bash
python -m pytest tests/test_sync_engine_dimensions.py tests/test_core.py -v
```

---

## Compiling for Production (Windows .exe)

To compile the entire Python ecosystem into a single standalone `.exe` (which runs via the Waitress production server), run the automated build script:

```cmd
.\build.bat
```
This will generate the production package in the `dist/SuprajitQualityPortal` folder.

---

## Production Execution

1. Copy the contents of `dist/SuprajitQualityPortal` to your server's `Z:\SuprajitQualityPortal_V2` drive.
2. Double-click `SuprajitQualityPortal.exe`.
3. The server will run in the background on Port 5000 (accessible across the LAN via the server's IP address).
4. Configure the "Watched Folder" path in the Admin -> Settings UI to point to your factory's Excel output directory.



