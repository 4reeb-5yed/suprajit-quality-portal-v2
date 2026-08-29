# Enterprise Administrator & Operations Manual (V3)

This manual provides authoritative operational guidance for both **Master System Administrators** (`bootstrap_admin` / Suprajit Corporate IT) and **Customer Company Administrators** (`company_admin` e.g., TVS, Tata Motors, Mahindra).

---

## 🏛️ 1. Multi-Tier Role Hierarchy & Permissions

| Functionality | Master Admin (`admin`) | Company Admin (`company_admin`) | Viewer (`customer_viewer`) |
| :--- | :---: | :---: | :---: |
| **System Settings & Search Root** | ✅ Full Access | ❌ Forbidden | ❌ Forbidden |
| **Dynamic Filename Regex Engine** | ✅ Full Access | ❌ Forbidden | ❌ Forbidden |
| **Cloudflare Tunnel Runner** | ✅ Full Access | ❌ Forbidden | ❌ Forbidden |
| **OAuth 2.0 / SSO Configuration** | ✅ Full Access | ❌ Forbidden | ❌ Forbidden |
| **Email Template Customization** | ✅ Full Access | ❌ Forbidden | ❌ Forbidden |
| **Customer Global Suspension** | ✅ Full Access | ❌ Forbidden | ❌ Forbidden |
| **Company Team Onboarding (Single & Bulk)**| ✅ Global | ✅ Own Company Only | ❌ Forbidden |
| **Team Domain Whitelist (Auto-Join)**| ✅ Global | ✅ Own Company Only | ❌ Forbidden |
| **User Recipe Access Mode (`ALL` vs `CUSTOM`)**| ✅ Global | ✅ Own Company Only | ❌ Forbidden |
| **In-Browser Spreadsheet Viewer & Search**| ✅ Global Scopes | ✅ Own Recipes | ✅ Assigned Recipes |
| **Forensic Audit Trail & Telemetry** | ✅ Global | ✅ Own Company Audit | ❌ Forbidden |

---

## ⚙️ 2. Dynamic Filename Regex Configuration (Master Admin)

The portal dynamically parses metadata from factory output files without opening them in Excel. System administrators can customize and test regex patterns live from **Admin &rarr; Settings &rarr; Custom Filename Parser**:

### Standard Named Regex Groups
The parser matches against these capture group names:
- `(?P<recipe>[a-zA-Z0-9_-]+)` &rarr; Product Recipe / Part family.
- `(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})` &rarr; Inspection Date (ISO format or separated by delimiters).
- `(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})` &rarr; Time of inspection.
- `(?P<serial>[a-zA-Z0-9_-]+)` &rarr; Serial / Barcode identifier.

### Live Testing & Fallback
The Admin Settings dashboard includes an **Interactive Regex Tester**. Enter a sample filename (e.g. `BRAKE_CABLE_20260829_103045_SN98412_PASS.xlsx`) to see real-time parsing extraction before saving.

---

## 🔑 3. Single Sign-On (SSO / OAuth 2.0) Integration

The portal features turnkey enterprise authentication across three identity providers:

### A. Microsoft 365 / Entra ID (Azure AD)
1. Register an App Registration in the **Azure Portal**.
2. Set Redirect URI to: `https://<YOUR_PUBLIC_DOMAIN>/auth/callback/microsoft`
3. In **Admin &rarr; Settings &rarr; Single Sign-On**:
   - Enable Microsoft SSO.
   - Enter **Client ID**, **Client Secret**, and **Tenant ID** (or `common`).

### B. Google Workspace
1. Create OAuth Credentials in **Google Cloud Console**.
2. Set Redirect URI to: `https://<YOUR_PUBLIC_DOMAIN>/auth/callback/google`
3. Enter Client ID and Client Secret in Admin Settings.

### C. GitHub Enterprise / Public
1. Create OAuth App in GitHub Settings.
2. Set Redirect URI to: `https://<YOUR_PUBLIC_DOMAIN>/auth/callback/github`
3. Enter Client ID and Client Secret.

---

## 🌐 4. Cloudflare Zero Trust Native Tunnel Runner

Expose the internal server to the internet with zero open router ports and enterprise DDoS protection:

1. Navigate to **Admin &rarr; Settings &rarr; Cloudflare Tunnel Manager**.
2. Select your mode:
   - **Quick Free Tunnel (`trycloudflare.com`)**: Generates a free, instant HTTPS tunnel directly from the local `cloudflared` binary with one click.
   - **Persistent Custom Domain Tunnel**: Paste your Cloudflare Zero Trust Named Tunnel Token (`ey...`).
3. Click **"Start Cloudflare Tunnel"**.
4. The system will launch a managed background process and automatically register the live public URL into `public_base_url`. All outgoing invitation emails and reset tokens will automatically link to this live HTTPS URL.

---

## 📧 5. Configurable Email Templates

Administrators can customize transactional notifications under **Admin &rarr; Settings &rarr; Email Templates**:

### Available Templates:
1. **User Welcome & Invitation**: Sent when a user is manually or bulk provisioned.
2. **Password Reset**: Sent for self-service forgotten passwords.
3. **Company Admin Notification**: Sent when a company admin account is created.

### Supported Dynamic Variables:
- `{{ user_name }}`: Display name of recipient.
- `{{ company_name }}`: Associated organization name.
- `{{ login_url }}`: Direct portal URL (resolved with public tunnel).
- `{{ reset_url }}`: Secure single-use token link.
- `{{ temp_password }}`: Temporary password (if auto-generated).

---

## 👥 6. Company Admin Workflows (`/company/dashboard`)

Company administrators have a dedicated, branded workspace to manage their internal staff:

### A. Auto-Join Email Domains
Configure corporate email domains (e.g. `tvs.in`, `tvs-motor.com`). Anyone registering on the public registration page with an `@tvs.in` email is automatically verified and joined to the TVS tenant organization.

### B. Bulk User Provisioning
Import multiple engineers simultaneously via CSV or multiline textarea:
```text
john.doe@tvs.in, John Doe, ALL
jane.smith@tvs.in, Jane Smith, CUSTOM
```

### C. User Recipe Filtering (`ALL` vs `CUSTOM`)
- **`ALL`**: User can view every recipe associated with the company.
- **`CUSTOM`**: Restrict specific engineers or third-party auditors to only view designated recipes.

---

## 📊 7. Zero-Overhead In-Browser Spreadsheet Viewer

- When viewing search results, click **"View"** next to any record to open the full spreadsheet modal.
- The browser downloads the raw binary via an isolated, authorized streaming endpoint (`/view-raw/<id>`) and renders the workbook via **SheetJS WebAssembly** entirely in the client browser.
- **Zero Server CPU Overhead**: Complex formulas, sheets, and tables are parsed on the client machine.
- Every view and download event is logged in the `audit_logs` table.

---

## 🛠️ 8. Diagnostics & Repair Utilities

Under **Admin &rarr; Repair & Diagnostics**:
- **Dry-Run Trace Simulator**: Simulates indexing of the watched folder and prints a detailed execution log without writing to SQLite.
- **Batch Date Purge**: Safely purges an entire day's corrupted ingestions in one transaction.
- **Database Vacuum & Integrity Check**: Runs `PRAGMA integrity_check` and `VACUUM` to compact SQLite storage.
- **Live System Telemetry**: View SQLite WAL cache status, memory usage, and background scheduler heartbeats.
