# Administrator Operations Guide

This guide provides operational instructions for Master Administrators (`admin`) and Company Administrators (`company_admin`).

---

## 1. Role Hierarchy & Access Matrix

| Administrative Capability | Master Admin (`admin`) | Company Admin (`company_admin`) | Client Viewer (`customer_viewer`) |
| :--- | :---: | :---: | :---: |
| **System Settings & SMTP Configuration** | Full Access | Forbidden | Forbidden |
| **Dynamic Filename Regex Engine** | Full Access | Forbidden | Forbidden |
| **Cloudflare Tunnel Control** | Full Access | Forbidden | Forbidden |
| **OAuth 2.0 / SSO Configuration** | Full Access | Forbidden | Forbidden |
| **Email Template Editor** | Full Access | Forbidden | Forbidden |
| **Global Customer Tenant Suspension** | Full Access | Forbidden | Forbidden |
| **User Onboarding (Single & Bulk)** | Global (Any Company) | Own Company Only | Forbidden |
| **Corporate Domain Whitelisting** | Global | Own Company Only | Forbidden |
| **User Recipe Access Control (`ALL` vs `CUSTOM`)** | Global | Own Company Only | Forbidden |
| **Spreadsheet Search & In-Browser Viewer** | Global Scopes | Own Company Recipes | Assigned Recipes |
| **Forensic Audit Log Access** | Global | Own Company Audit | Forbidden |

---

## 2. Master Admin Workflows

### Initial Bootstrap Wizard (`/admin/setup`)
Upon first deployment, the portal enforces a setup wizard requiring the default bootstrap credentials (`bootstrap_admin` / `admin123`) to be updated with a strong password and administrative recovery email.

### Dynamic Filename Regex Configuration
Located under **Admin &rarr; Settings &rarr; Filename Regex Parser**:
- Configures regular expressions to extract metadata tokens from incoming factory filenames.
- Standard named capture groups:
  - `(?P<recipe>...)`: Part / inspection recipe name.
  - `(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})`: Inspection date.
  - `(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})`: Inspection time.
  - `(?P<serial>...)`: Serial or barcode number.

### Monitored Folder Mappings
Located under **Admin &rarr; Settings &rarr; Monitored Folders**:
- Map specific server folders or network shares directly to customer tenants.
- Files found in mapped folders are automatically associated with the assigned `customer_id`.

### Diagnostic & Repair Utilities (`/admin/repair`)
- **Dry Run Simulator**: Scans target folders and prints trace logs showing extracted metadata without inserting records into SQLite.
- **Forced Date Sync**: Bypasses N-1 logic to ingest files for a specific historic date.
- **Date Purge**: Safely deletes all records and files ingested for a specific target date.

---

## 3. Company Admin Workflows (`/company/users`)

Company administrators manage internal staff without access to global system settings:

1. **Auto-Join Corporate Email Domains**:
   - Add domain whitelists (e.g. `tvs.in`, `mahindra.com`). New users signing in via SSO or public registration with matching emails automatically join the company organization.
2. **Bulk Team Provisioning**:
   - Onboard multiple team members via CSV upload or multiline text box.
3. **Recipe Permissions (`ALL` vs `CUSTOM`)**:
   - Set user access mode to `ALL` to allow viewing all recipes granted to the company.
   - Set to `CUSTOM` and select specific recipe checkboxes to restrict an individual user or contractor to a subset of recipes.
