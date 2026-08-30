# API & Route Reference

This document catalogs every endpoint across all four Flask blueprints (`auth`, `portal`, `company`, `admin`).

---

## 1. Authentication Blueprint (`auth_bp`)

| Method | Path | Auth Required | Role Required | Request Parameters / Form Body | Response / Redirect | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET`, `POST` | `/login` | None | None | Form: `username`, `password` | 200 HTML or 302 Redirect to `/search`, `/admin/`, or `/company/users` | Authenticates user; enforces 15-minute lockout on 5 failed attempts; respects customer suspension. |
| `GET` | `/logout` | Authenticated | Any | None | 302 Redirect to `/login` | Terminates user session. |
| `GET`, `POST` | `/register` | None | None | Form: `username`, `email`, `password`, `display_name`, `customer_id` | 200 HTML or 302 Redirect to `/login` | Public registration with automatic company auto-join when email matches allowed domains. |
| `GET`, `POST` | `/forgot-password` | None | None | Form: `email` | 200 HTML or 302 Redirect to `/login` | Generates secure single-use password reset token and sends email. |
| `GET`, `POST` | `/reset-password/<token>` | None | None | URL: `token`; Form: `password`, `confirm_password` | 200 HTML or 302 Redirect to `/login` | Validates serializer token (1-hour expiry) and updates password hash. |
| `GET` | `/oauth/login/<provider_name>` | None | None | URL: `provider_name` (`google`, `microsoft`, `github`) | 302 Redirect to Identity Provider OAuth URL | Initiates OAuth 2.0 / OIDC authorization flow. |
| `GET` | `/oauth/callback/<provider_name>` | None | None | URL: `provider_name`; OAuth callback query params | 302 Redirect to `/search` or `/login` | Processes OAuth callback token, provisions or links user, auto-joins company by domain. |

---

## 2. Portal Blueprint (`portal_bp`)

| Method | Path | Auth Required | Role Required | Request Parameters / Form Body | Response / Redirect | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Authenticated | Any | None | 302 Redirect to `/search` | Default root redirect. |
| `GET` | `/search` | Authenticated | Any | None | 200 HTML (`portal/search.html`) | Main quality report search interface with accessible recipes dropdown. |
| `GET` | `/search/results` | Authenticated | Any | Query: `recipe`, `date`, `serial` | 200 HTML snippet (`partials/results_table.html`) | HTMX/AJAX search endpoint returning matching report records and logging latency metrics. |
| `GET` | `/download/<int:report_id>` | Authenticated | Authorized Scope | URL: `report_id` | 200 File attachment download or 404 | Streams physical file download; validates path safety (`is_safe_path`); logs audit record. |
| `GET` | `/view-raw/<int:report_id>` | Authenticated | Authorized Scope | URL: `report_id` | 200 Inline binary stream or 404 | Streams file with `Content-Disposition: inline` for client-side SheetJS rendering; logs audit. |

---

## 3. Company Blueprint (`company_bp`, URL Prefix: `/company`)

| Method | Path | Auth Required | Role Required | Request Parameters / Form Body | Response / Redirect | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/company/users` | Authenticated | `company_admin` or `admin` | None | 200 HTML (`company/users.html`) | Company management console: team member list, recipe assignment, domain whitelists. |
| `POST` | `/company/users/add` | Authenticated | `company_admin` or `admin` | Form: `username`, `email`, `password`, `display_name`, `role` | 302 Redirect to `/company/users` | Creates a new user in the administrator's company tenant. |
| `POST` | `/company/users/bulk_import` | Authenticated | `company_admin` or `admin` | Form: `bulk_text`, `send_invites`, or `bulk_file` (CSV) | 302 Redirect to `/company/users` | Bulk provisions users for the administrator's company organization. |
| `POST` | `/company/users/toggle_active` | Authenticated | `company_admin` or `admin` | Form: `user_id`, `is_active` | 302 Redirect to `/company/users` | Enables or disables an individual company user's login access. |
| `POST` | `/company/users/delete` | Authenticated | `company_admin` or `admin` | Form: `user_id` | 302 Redirect to `/company/users` | Deletes a user account belonging to the administrator's company tenant. |
| `POST` | `/company/users/update_permissions` | Authenticated | `company_admin` or `admin` | Form: `user_id`, `access_mode`, `recipes[]` | 302 Redirect to `/company/users` | Configures recipe access mode (`ALL` vs `CUSTOM`) and assigns specific recipes to a user. |
| `POST` | `/company/domains/update` | Authenticated | `company_admin` or `admin` | Form: `allowed_domains` | 302 Redirect to `/company/users` | Updates comma-separated allowed corporate email domains for auto-join. |

---

## 4. Admin Blueprint (`admin_bp`, URL Prefix: `/admin`)

| Method | Path | Auth Required | Role Required | Request Parameters / Form Body | Response / Redirect | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/admin/` | Authenticated | `admin` | None | 200 HTML (`admin/dashboard.html`) | System dashboard with summary cards, recent batch runs, and audit trail modal. |
| `GET`, `POST` | `/admin/setup` | Authenticated | `admin` | Form: `password`, `confirm_password`, `email` | 200 HTML or 302 Redirect to `/admin/` | Mandatory first-boot bootstrap wizard to change default credentials. |
| `GET` | `/admin/evidence` | Authenticated | `admin` | None | 200 HTML (`admin/evidence.html`) | ISO 9001 and ASVS quality and security telemetry dashboard. |
| `POST` | `/admin/trigger_sync` | Authenticated | `admin` | None | 302 Redirect to `/admin/` | Triggers a full background ingestion batch manually. |
| `GET` | `/admin/customers` | Authenticated | `admin` | None | 200 HTML (`admin/customers.html`) | Global customer organization management and recipe assignment list. |
| `POST` | `/admin/customers/add` | Authenticated | `admin` | Form: `id`, `company_name` | 302 Redirect to `/admin/customers` | Provisions a new customer tenant organization. |
| `GET` | `/admin/customers/<customer_id>` | Authenticated | `admin` | URL: `customer_id` | 200 HTML (`admin/customer_detail.html`) | Detailed customer management: users, allowed domains, recipes. |
| `POST` | `/admin/customers/edit` | Authenticated | `admin` | Form: `customer_id`, `company_name` | 302 Redirect to `/admin/customers` | Edits customer organization name. |
| `POST` | `/admin/customers/toggle` | Authenticated | `admin` | Form: `customer_id`, `suspended` | 302 Redirect to `/admin/customers` | Toggles global customer portal suspension. |
| `POST` | `/admin/customers/delete` | Authenticated | `admin` | Form: `customer_id` | 302 Redirect to `/admin/customers` | Permanently deletes a customer organization. |
| `POST` | `/admin/customers/add_recipe` | Authenticated | `admin` | Form: `customer_id`, `recipe_name` | 302 Redirect to customer detail | Grants recipe access to a customer organization. |
| `POST` | `/admin/customers/delete_recipe` | Authenticated | `admin` | Form: `customer_id`, `recipe_name` | 302 Redirect to customer detail | Revokes recipe access from a customer organization. |
| `POST` | `/admin/customers/update_domains` | Authenticated | `admin` | Form: `customer_id`, `allowed_domains` | 302 Redirect to customer detail | Updates customer organization allowed auto-join email domains. |
| `POST` | `/admin/customers/update_user_permissions` | Authenticated | `admin` | Form: `user_id`, `access_mode`, `recipes[]` | 302 Redirect to customer detail | Updates granular recipe permissions for a user. |
| `POST` | `/admin/customers/add_user` | Authenticated | `admin` | Form: `username`, `password`, `email`, `display_name`, `role`, `customer_id`, `access_mode` | 302 Redirect | Creates a user under any role or customer organization. |
| `POST` | `/admin/users/bulk_import` | Authenticated | `admin` | Form: `customer_id`, `role`, `bulk_text`, `send_invites`, or `bulk_file` (CSV) | 302 Redirect | Bulk provisions users across any customer organization. |
| `POST` | `/admin/customers/toggle_user` | Authenticated | `admin` | Form: `user_id`, `is_active` | 302 Redirect | Toggles activation status for any user account. |
| `POST` | `/admin/users/delete` | Authenticated | `admin` | Form: `user_id` | 302 Redirect | Deletes a user account. |
| `GET`, `POST` | `/admin/settings` | Authenticated | `admin` | Form: System settings, SMTP, SSO, Regex, Email templates | 200 HTML (`admin/settings/index.html`) or 302 Redirect | System configuration dashboard. |
| `POST` | `/admin/folder_mappings/add` | Authenticated | `admin` | Form: `folder_path`, `customer_id` | 302 Redirect to settings | Adds a monitored folder path with customer association. |
| `POST` | `/admin/folder_mappings/delete` | Authenticated | `admin` | Form: `mapping_id` | 302 Redirect to settings | Deletes a monitored folder mapping. |
| `POST` | `/admin/tunnel/action` | Authenticated | `admin` | Form: `action` (`start_quick`, `start_token`, `stop`), `tunnel_token` | 302 Redirect to settings | Starts or stops native Cloudflare Zero Trust tunnel background processes. |
| `GET` | `/admin/diagnostics` | Authenticated | `admin` | None | 200 HTML (`admin/diagnostics.html`) | Live log stream, SQLite WAL database size, and schema version display. |
| `GET`, `POST` | `/admin/repair` | Authenticated | `admin` | Form: `action` (`dry_run`, `force_sync`, `purge_date`), `target_date`, `regex_pattern` | 200 HTML (`admin/repair.html`) | Dry-run parser testing, forced ingestion of historic dates, and batch purge tool. |
| `GET` | `/admin/logs/download` | Authenticated | `admin` | None | 200 File attachment download or 404 | Downloads full system rotating log file (`suprajit_system.log`). |
