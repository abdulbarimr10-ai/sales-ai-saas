# Sales AI SaaS Platform

Sales AI is an automated B2B sales automation and email outreach platform. It automates lead search, runs deep business audits using multi-LLM orchestration (OpenAI, Gemini, Claude), calculates lead-specific ROI, and sends personalized Gmail outreach emails.

## 🏗️ Project Architecture

```
├── app/                  # Flask Backend API
│   ├── api/              # Blueprint endpoints (auth, gmail, keys, health, etc.)
│   ├── core/             # Central configurations & error handlers
│   ├── services/         # Business logic & integrations (Gmail, LLMs, sessions)
│   ├── workers/          # Celery task definitions & runner configurations
│   └── main.py           # Flask App Factory entrypoint
├── database/             # Supabase schema definitions & queries
├── frontend/             # React + Vite + Tailwind CSS User Interface
├── pipeline/             # Agentic pipeline workflows (Audits, Outreach, Discovery)
├── tools/                # Auxiliary automation utilities
├── Dockerfile            # Multi-service Production Container configuration
├── Procfile              # Process manager configuration for Railway
└── railway.json          # Deployment build instructions for Railway
```

## 🛠️ Tech Stack
- **Backend API**: Flask (Python) with Gunicorn
- **Task Worker Queue**: Celery (orchestrated with Redis)
- **Frontend SPA**: React (Vite, Tailwind CSS)
- **Database**: Supabase (PostgreSQL)
- **Caching & Sessions**: Redis
- **Integrations**: Google APIs (Gmail OAuth 2.0), OpenAI, Anthropic, Google Gemini

---

## 🚀 Quickstart Local Development

### 1. Backend Setup
1. Navigate to the root directory and create a virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate # Windows
   # or source venv/bin/activate # Unix
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
   Fill in `.env` with your Supabase credentials, Google client details, and secrets.
4. Launch local Redis (required for sessions and Celery):
   ```bash
   # If you have Docker:
   docker run -d -p 6379:6379 redis:alpine
   ```
5. Start local Celery workers:
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info -Q outreach,ai,emails,enrichment,maintenance
   ```
6. Start the Flask dev server:
   ```bash
   python run.py
   ```

### 2. Frontend Setup
1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install Node packages:
   ```bash
   npm install
   ```
3. Copy the local `.env` setup:
   ```bash
   cp .env.example .env
   ```
4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

## 🔒 Production Deployment

For step-by-step production deployment instructions using **Vercel** (frontend), **Railway** (API, workers, scheduler, Redis), and **Supabase**, please read the [DEPLOYMENT.md](file:///c:/Users/hp/OneDrive/Desktop/sales_AI%20-%20Copy/DEPLOYMENT.md) guide.

### Key Production Requirements:
- Always run Gunicorn (`run:app`) and run containers under non-root users.
- Configure `FLASK_ENV=production` to trigger strict environment validation.
- Set secure session cookies (`SESSION_COOKIE_SECURE=True`).
- Disable `OAUTHLIB_INSECURE_TRANSPORT` to protect Gmail OAuth tokens.
- Add basic credentials to Flower dashboards using `FLOWER_BASIC_AUTH`.
