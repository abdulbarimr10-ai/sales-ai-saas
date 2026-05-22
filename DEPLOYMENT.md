# Production Deployment Guide — Sales AI Platform

This guide walks you through deploying the Sales AI platform to production using **Railway** (Backend API, Celery Workers, Celery Beat scheduler, and Redis) and **Vercel** (Frontend UI), with **Supabase** (PostgreSQL) as the persistent database.

---

## 1. Database Setup (Supabase)

1. Create an account or sign in to [Supabase](https://supabase.com/).
2. Create a new project.
3. Open the **SQL Editor** on the left sidebar.
4. Copy the contents of the database schema file `database/schema.sql` and run the script in the SQL editor to initialize tables (`users`, `leads`, `history`, `gmail_credentials`, etc.).
5. Go to **Project Settings -> API** and copy:
   - **Project URL** (used as `SUPABASE_URL`)
   - **service_role API key** (used as `SUPABASE_SERVICE_ROLE_KEY` - keep this secret)

---

## 2. Google OAuth Setup (Gmail Integration)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Navigate to **APIs & Services -> Library** and enable the **Gmail API**.
4. Go to **OAuth consent screen** and configure it as **External**. Add your test emails under the "Test users" tab if the application is not yet verified by Google.
5. Navigate to **Credentials -> Create Credentials -> OAuth client ID**.
6. Select **Web application** as the application type.
7. Add authorized redirect URIs:
   - **Development**: `http://localhost:5000/api/gmail/callback`
   - **Production**: `https://your-backend-service.up.railway.app/api/gmail/callback`
8. Click Create. Copy your **Client ID** and **Client Secret**.

---

## 3. Backend & Worker Deployment (Railway)

For a fully operational background task architecture, you will create **four services** in your Railway project using the same GitHub repository:

### A. Deploy Redis
1. In your Railway project, click **New -> Database -> Add Redis**.
2. Railway will spin up a private Redis instance. Note its internal connection URL (available via `${{Redis.REDIS_URL}}`).

### B. Deploy Flask API Service (web)
1. Click **New -> Github Repo** and link your Sales AI repository.
2. Under **Settings -> Service Name**, rename this service to `backend-api`.
3. Railway automatically detects `railway.json` and the `Dockerfile` to build the app.
4. Go to **Settings -> Networking** and click **Generate Domain** to get your public API URL.
5. In **Variables**, add the following environment variables (see the Environment Checklist below).

### C. Deploy Celery Worker Service (celery_worker)
1. Click **New -> Github Repo** and select the same repository.
2. Under **Settings -> Service Name**, rename this to `celery-worker`.
3. Under **Settings -> Deploy -> Custom Start Command**, input:
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info -Q outreach,ai,emails,enrichment,maintenance -c 4
   ```
4. Copy the environment variables from the `backend-api` service.

### D. Deploy Celery Beat Service (celery_beat)
1. Click **New -> Github Repo** and select the same repository.
2. Under **Settings -> Service Name**, rename this to `celery-beat`.
3. Under **Settings -> Deploy -> Custom Start Command**, input:
   ```bash
   celery -A app.workers.celery_app beat --loglevel=info
   ```
4. Copy the environment variables from the `backend-api` service.

### E. Deploy Flower Service (flower) — Optional
1. Click **New -> Github Repo** and select the same repository.
2. Under **Settings -> Service Name**, rename this to `flower`.
3. Under **Settings -> Deploy -> Custom Start Command**, input:
   ```bash
   python -m app.workers.run_flower
   ```
4. Copy the environment variables from the `backend-api` service. Ensure you set `ENABLE_FLOWER=true` and configure a secure `FLOWER_BASIC_AUTH=username:password`.

---

## 4. Environment Variables Checklist

Add these environment variables to your Railway services (`backend-api`, `celery-worker`, `celery-beat`, `flower`):

| Variable Name | Production Description | Example Value |
| :--- | :--- | :--- |
| `FLASK_ENV` | Must be set to `production` to trigger security validations | `production` |
| `FLASK_DEBUG` | Keep disabled in production | `False` |
| `SECRET_KEY` | Long, random unique key for Flask sessions | `e.g. openssl rand -hex 32` |
| `ENCRYPTION_KEY` | Secure, custom 32-byte base64 AES encryption key | `Generate with: python -c "import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8'))"` |
| `FRONTEND_URL` | Comma-separated list of origins for CORS validation | `http://localhost:5173,https://sales-ai.vercel.app` |
| `SUPABASE_URL` | Your Supabase Project API URL | `https://yourproject.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Your Supabase service_role key | `eyJhbGciOiJIUzI1Ni...` |
| `REDIS_URL` | Railway internal Redis connection URL | `${{Redis.REDIS_URL}}` |
| `GOOGLE_CLIENT_ID` | Google Console OAuth Client ID | `61433045519-xxxx.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google Console OAuth Client Secret | `GOCSPX-xxxx` |
| `GOOGLE_REDIRECT_URI` | The production redirect URI endpoint | `https://your-backend-service.up.railway.app/api/gmail/callback` |
| `SESSION_COOKIE_SECURE` | Enable secure HTTPS-only session cookies | `True` |
| `SESSION_COOKIE_HTTPONLY` | Prevent JS from reading cookies | `True` |
| `SESSION_COOKIE_SAMESITE` | Restrict cross-site requests | `Lax` |
| `ENABLE_FLOWER` | Toggle Celery Flower monitoring dashboard | `true` or `false` |
| `FLOWER_BASIC_AUTH` | Basic auth protection for Flower | `admin:yoursecurerandompassword` |

---

## 5. Frontend Deployment (Vercel)

1. Sign in to [Vercel](https://vercel.com/).
2. Click **Add New -> Project** and import your GitHub repository.
3. Vercel will auto-detect Vite. Under project configuration:
   - Set **Framework Preset** to `Vite`.
   - Set **Root Directory** to `frontend`.
4. Expand **Environment Variables** and add:
   - `VITE_API_URL`: `https://your-backend-service.up.railway.app` (your public Railway API URL without a trailing slash).
5. Click **Deploy**.
6. The `frontend/vercel.json` file automatically handles SPA route rewrites for Vite's client-side router.

---

## 6. Post-Deployment Verification

1. **OAuth Verification**: Verify that clicking "Connect Gmail" in settings redirects to Google, completes the token exchange, and successfully redirects back to the settings page displaying `gmail=connected`.
2. **CORS Enforcement**: Open the browser console on the Vercel site and trigger an API action. Confirm there are no CORS validation errors.
3. **Task Queueing**: Perform a lead search or run an audit. In the backend logs, verify that the Celery worker picks up and processes tasks from the correct queue (`ai`, `outreach`, etc.).
4. **Flower Protection**: Attempt to access the Flower dashboard. Verify that basic authentication prompts you and rejects empty credentials.
