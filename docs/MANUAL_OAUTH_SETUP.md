# Enterprise OAuth2 / OIDC Manual Verification Checklist

This manual verification checklist is intended for system administrators and QA personnel performing a one-time end-to-end authentication check against production identity provider accounts (Microsoft 365 Entra ID, Google Workspace, GitHub) outside of automated CI pipelines.

---

## 1. Prerequisites
Ensure you have administrative privileges in your identity provider portal and in the Suprajit Quality Portal.

---

## 2. Google Workspace SSO Verification

1. **Google Cloud Console**:
   - Navigate to **APIs & Services > Credentials**.
   - Create an **OAuth 2.0 Client ID** (Web application).
   - Add Authorized Redirect URI: `https://<YOUR_PORTAL_DOMAIN>/oauth/callback/google`
   - Copy the Client ID and Client Secret.

2. **Suprajit Portal Setup**:
   - Log in as `bootstrap_admin` and navigate to **System Settings > Single Sign-On (SSO)**.
   - Toggle **Google SSO** to **Enabled**.
   - Enter your Client ID and Client Secret, then click **Save SSO Settings**.

3. **Domain Auto-Join Configuration**:
   - In **Customer Management**, edit your target organization (e.g. `TVS Motor Company`).
   - Add your corporate Google domain to **Allowed Email Domains** (e.g. `tvs.com`).

4. **Live Sign-In Test**:
   - Open an Incognito browser window and go to the portal login page (`/login`).
   - Click **Sign in with Google**.
   - Authenticate with a live `@tvs.com` Google account.
   - **Verification Point**: Confirm that the user is immediately redirected to `/search`, provisioned with role `customer_viewer`, assigned to `TVS Motor Company`, and recorded in the audit log.

---

## 3. Microsoft 365 / Entra ID SSO Verification

1. **Microsoft Entra Admin Center**:
   - Navigate to **App registrations > New registration**.
   - Set Supported Account Types (e.g., Accounts in this organizational directory only, or Multitenant).
   - Add Redirect URI (Web): `https://<YOUR_PORTAL_DOMAIN>/oauth/callback/microsoft`
   - Under **Certificates & Secrets**, generate a new client secret.

2. **Suprajit Portal Setup**:
   - In **System Settings > Single Sign-On (SSO)**, toggle **Microsoft SSO** to **Enabled**.
   - Enter the Application (Client) ID, Client Secret, and Directory (Tenant) ID.

3. **Live Sign-In Test**:
   - Click **Sign in with Microsoft** from `/login`.
   - Complete multi-factor authentication (MFA).
   - **Verification Point**: Confirm full name, email, and company assignment match Entra claims.

---

## 4. GitHub Enterprise SSO Verification

1. **GitHub Developer Settings**:
   - Register a new **OAuth App**.
   - Authorization callback URL: `https://<YOUR_PORTAL_DOMAIN>/oauth/callback/github`

2. **Suprajit Portal Setup**:
   - Enable **GitHub SSO** in settings and input Client ID/Secret.

3. **Live Sign-In Test**:
   - Click **Sign in with GitHub**.
   - Authorize permissions and verify seamless portal landing.