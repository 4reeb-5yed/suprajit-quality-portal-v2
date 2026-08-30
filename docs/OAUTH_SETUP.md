# Identity Provider (OAuth 2.0 / OIDC) Setup Guide

This document details how to configure Single Sign-On (SSO) credentials in Google Cloud, Microsoft Entra ID, and GitHub, and register them in the Suprajit Quality Portal.

---

## 1. Google Workspace SSO

1. **Google Cloud Console**:
   - Go to **APIs & Services &rarr; Credentials**.
   - Click **Create Credentials &rarr; OAuth Client ID**.
   - Application Type: **Web application**.
   - Authorized Redirect URI: `https://<YOUR_PORTAL_DOMAIN>/oauth/callback/google`
   - Save and copy the **Client ID** and **Client Secret**.
2. **Portal Configuration**:
   - Navigate to **Admin &rarr; Settings &rarr; Single Sign-On**.
   - Enable Google SSO, enter Client ID and Client Secret, and save.

---

## 2. Microsoft 365 / Entra ID (Azure AD)

1. **Microsoft Entra Admin Center**:
   - Go to **Identity &rarr; Applications &rarr; App registrations**.
   - Click **New registration**.
   - Set Redirect URI (Web): `https://<YOUR_PORTAL_DOMAIN>/oauth/callback/microsoft`
   - Under **Certificates & secrets**, create a new client secret.
   - Note the **Application (client) ID**, **Directory (tenant) ID**, and **Client Secret Value**.
2. **Portal Configuration**:
   - Navigate to **Admin &rarr; Settings &rarr; Single Sign-On**.
   - Enable Microsoft SSO, enter Client ID, Client Secret, and Tenant ID (or `common`), and save.

---

## 3. GitHub OAuth

1. **GitHub Developer Settings**:
   - Go to **Settings &rarr; Developer Settings &rarr; OAuth Apps &rarr; New OAuth App**.
   - Authorization callback URL: `https://<YOUR_PORTAL_DOMAIN>/oauth/callback/github`
   - Generate a new client secret.
2. **Portal Configuration**:
   - Enable GitHub SSO in **Admin &rarr; Settings**, input Client ID and Client Secret, and save.

---

## 4. Domain Auto-Join Setup

To automatically assign authenticated SSO users to their company organization:
1. As an Administrator, edit the customer company under **Admin &rarr; Customers &rarr; [Company Detail]**.
2. Add the corporate domain to **Allowed Email Domains** (e.g. `tvs.in`).
3. When users sign in via Google, Microsoft, or GitHub using an `@tvs.in` email, they are automatically provisioned under the corresponding company organization.
