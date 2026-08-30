# Configuration Reference

This document details all environment variables read by [`app/config.py`](../app/config.py) and `.env.example`, as well as all runtime key-value settings managed in the `system_settings` SQLite table.

---

## 1. Environment Variables (`.env`)

Environment variables are loaded on startup via `python-dotenv` in [`app/config.py`](../app/config.py).

| Variable Name | Required / Default | Purpose |
| :--- | :--- | :--- |
| `SECRET_KEY` | **Required** (Raises `RuntimeError` in production if missing) | Cryptographic secret key used for session signing, CSRF tokens, and Fernet encryption for credentials stored in SQLite. Generated automatically in test contexts. |
| `DATABASE_PATH` | Default: `data/portal.db` (resolved relative to app root or `.exe` directory) | Filesystem path to the SQLite database file. |
| `STORAGE_FOLDER` | Default: `storage/` (resolved relative to app root or `.exe` directory) | Directory where ingested report files are stored and categorized into `YYYY-MM-DD` subdirectories. |
| `HOST` | Default: `0.0.0.0` | Bind IP address for the Waitress WSGI server. |
| `PORT` | Default: `5000` | HTTP port for the Waitress WSGI server. |
| `MAIL_SERVER` | Default: `smtp.gmail.com` | Fallback SMTP server hostname. Overridden at runtime by `system_settings.mail_server` if present. |
| `MAIL_PORT` | Default: `587` | Fallback SMTP port. Overridden by `system_settings.mail_port`. |
| `MAIL_USERNAME` | Default: `None` | Fallback SMTP username. Overridden by `system_settings.mail_username`. |
| `MAIL_PASSWORD` | Default: `None` | Fallback SMTP password. Overridden by `system_settings.mail_password`. |
| `MAIL_DEFAULT_SENDER`| Default: Value of `MAIL_USERNAME` | Outbound sender email address. |

---

## 2. Dynamic Runtime Settings (`system_settings` Table)

Runtime settings are persisted in SQLite and managed directly through **Admin &rarr; Settings** without restarting the application:

| Setting Key | Default Value | Purpose |
| :--- | :--- | :--- |
| `setup_completed` | `"0"` | Set to `"1"` after the master admin completes the initial bootstrap setup wizard (`/admin/setup`). |
| `sync_time` | `"02:00"` | Daily execution time (`HH:MM`) when the background scheduler triggers the N-1 ingestion batch. |
| `last_sync_date` | `None` | Tracks the last calendar date (`YYYY-MM-DD`) on which the scheduled batch executed to prevent multiple runs on the same day. |
| `root_search_path` | `""` | Semicolon-separated list of monitored folder paths (legacy fallback for `folder_mappings`). |
| `filename_regex_pattern` | Standard manufacturing regex pattern | Regular expression pattern used by `app.parser.parse_filename()` to extract recipe, date, time, and serial number from report filenames. |
| `public_portal_url` | `""` | Public HTTPS URL (e.g., Cloudflare tunnel or corporate domain) used to construct password reset links and team invitation emails. |
| `mail_server` | `"smtp.gmail.com"` | Primary SMTP server hostname for transactional emails. |
| `mail_port` | `"587"` | Primary SMTP port. |
| `mail_username` | `""` | Primary SMTP username / account. |
| `mail_password` | `""` | AES-256 Fernet-encrypted SMTP password. |
| `mail_use_tls` | `"1"` | Boolean flag (`"1"` or `"0"`) for SMTP STARTTLS encryption. |
| `developer_email` | `""` | Recipient email address for system alerts and critical diagnostics. |
| `telemetry_frequency` | `"daily"` | Frequency for system telemetry reports. |
| `sso_google_enabled` | `"0"` | Boolean flag (`"1"` or `"0"`) enabling Google Workspace OAuth 2.0. |
| `sso_google_client_id` | `""` | Google OAuth Client ID. |
| `sso_google_client_secret` | `""` | Google OAuth Client Secret. |
| `sso_google_server_metadata_url` | OpenID config URL | Google OpenID Discovery URL. |
| `sso_microsoft_enabled` | `"0"` | Boolean flag enabling Microsoft 365 / Entra ID OAuth 2.0. |
| `sso_microsoft_client_id` | `""` | Microsoft Entra Application (Client) ID. |
| `sso_microsoft_client_secret` | `""` | Microsoft Entra Client Secret. |
| `sso_microsoft_tenant_id` | `"common"` | Microsoft Entra Directory (Tenant) ID. |
| `sso_microsoft_server_metadata_url` | OpenID config URL | Microsoft OpenID Discovery URL. |
| `sso_github_enabled` | `"0"` | Boolean flag enabling GitHub OAuth 2.0. |
| `sso_github_client_id` | `""` | GitHub OAuth App Client ID. |
| `sso_github_client_secret` | `""` | GitHub OAuth App Client Secret. |
| `sso_github_api_base_url` | `"https://api.github.com/"` | GitHub API base endpoint. |
| `sso_github_access_token_url` | Token URL | GitHub OAuth token endpoint. |
| `sso_github_authorize_url` | Authorize URL | GitHub OAuth authorization endpoint. |
| `template_welcome_email` | Built-in welcome text | Custom template for new user welcome emails. |
| `template_invite_email` | Built-in invite text | Custom template for company team invitation emails. |
| `template_reset_password` | Built-in reset text | Custom template for password reset link emails. |
