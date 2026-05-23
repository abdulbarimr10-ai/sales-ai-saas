# 🚀 Sales AI SaaS Platform

A production-grade AI-powered B2B sales automation platform built with Flask, React, Supabase, and multi-LLM integrations.

Sales AI helps businesses automate lead discovery, AI-driven auditing, outreach generation, and Gmail-based email automation through a scalable SaaS architecture.

---

# 🌐 Live Deployment

## Frontend

Deployed on Vercel

## Backend API

Deployed on Render

---

# ✨ Features

## 🔍 Lead Discovery

* Discover business leads by niche and region
* Google search enrichment
* Apollo-style workflow support
* Intelligent filtering pipeline

## 🧠 AI Deep Audits

* AI-generated lead analysis
* Website & business presence audits
* Pain-point detection
* ROI estimation engine
* Multi-provider LLM orchestration

## ✍️ Outreach Automation

* Personalized email generation
* Gmail OAuth integration
* Automated outreach workflows
* AI-assisted messaging

## 🔑 BYOK (Bring Your Own Key)

Users can securely connect:

* OpenAI
* Google Gemini
* Anthropic Claude
* Ollama

## 🔐 Secure Authentication

* Session-based authentication
* Supabase PostgreSQL persistence
* Secure cookie handling
* Cross-domain production auth support

## 📦 Production Infrastructure

* Dockerized deployment
* Gunicorn production server
* Redis-compatible architecture
* Async-ready worker system
* Free-tier optimized deployment

---

# 🏗️ Tech Stack

## Frontend

* React
* Vite
* Tailwind CSS
* React Context API

## Backend

* Flask
* Gunicorn
* Flask-CORS
* Pydantic configuration system

## Database

* Supabase (PostgreSQL)
* SQLite (local fallback)

## AI Providers

* OpenAI
* Gemini
* Anthropic Claude
* Ollama

## Infrastructure

* Docker
* Render
* Vercel
* Redis-compatible architecture

## Authentication & Security

* Google OAuth 2.0
* AES encryption for credential storage
* Secure session cookies
* CORS hardening

---

# 🧠 Architecture Overview

```text
Frontend (React/Vite)
        ↓
Flask API (Gunicorn)
        ↓
Authentication Layer
        ↓
AI Provider Factory
        ↓
Lead Discovery Pipeline
        ↓
Audit Engine
        ↓
Outreach Generation
        ↓
Gmail OAuth Delivery
        ↓
Supabase PostgreSQL
```

---

# 🔥 Engineering Challenges Solved

## Cross-Domain Authentication

Implemented secure cross-domain session persistence between:

* Vercel frontend
* Render backend

Using:

* SameSite=None
* Secure cookies
* Credentialed CORS requests

## Production Memory Optimization

Optimized deployment for Render free-tier constraints:

* Lazy-loading AI SDKs
* Reduced Gunicorn workers
* Lightweight startup sequence
* Production-safe imports

## OAuth Integration

Built a full Gmail OAuth workflow:

* Google Cloud integration
* OAuth callback handling
* Secure token persistence
* Gmail account verification

## Production Deployment Debugging

Resolved:

* Docker container import issues
* Gunicorn boot failures
* Vercel SPA routing problems
* Session persistence issues
* Redis compatibility constraints

---

# 📸 UI Highlights

## Dashboard

* AI-powered lead discovery
* Real-time logs
* Search orchestration

## Lead Management

* Grid/table views
* Batch outreach actions
* Deep audit workflows

## AI Audit Modal

* Pain-point analysis
* Business insights
* ROI estimation
* Personalized recommendations

## Integrations

* Gmail OAuth connection
* API key management
* AI provider configuration

---

# ⚙️ Local Development Setup

## 1. Clone Repository

```bash
git clone https://github.com/abdulbarimr10-ai/sales-ai-saas.git
cd sales-ai-saas
```

---

## 2. Backend Setup

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run backend

```bash
python run.py
```

Backend runs on:

```text
http://localhost:5000
```

---

## 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on:

```text
http://localhost:5173
```

---

# 🔐 Environment Variables

## Backend

```env
FLASK_ENV=production
FLASK_DEBUG=False

SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

SECRET_KEY=
ENCRYPTION_KEY=

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=

REDIS_URL=

FRONTEND_URL=
```

## Frontend

```env
VITE_API_URL=
```

---

# 🚀 Deployment

## Frontend Deployment

* Vercel

## Backend Deployment

* Render

## Database

* Supabase PostgreSQL

## Production Features

* Dockerized backend
* Gunicorn production server
* HTTPS deployment
* Secure session handling
* OAuth integration

---

# 📈 Future Improvements

* Re-enable distributed Celery workers
* Advanced analytics dashboard
* Team collaboration features
* AI workflow orchestration
* CRM integrations
* Multi-tenant scaling
* Real-time notifications
* Queue monitoring dashboard

---

# 🧪 Current Status

✅ Production frontend deployed

✅ Production backend deployed

✅ Gmail OAuth integrated

✅ Multi-LLM architecture working

✅ Supabase authentication active

✅ Dockerized infrastructure

✅ Cross-domain authentication fixed

✅ SaaS MVP launch-ready

---

# 👨‍💻 Author

Md Abdul Bari

Passionate about:

* AI Engineering
* SaaS Architecture
* Full-Stack Development
* DevOps & Deployment
* Production Systems

---

# 📬 Connect

## GitHub

[https://github.com/abdulbarimr10-ai/sales-ai-saas](https://github.com/abdulbarimr10-ai/sales-ai-saas)

## LinkedIn

Add your LinkedIn profile here.

---

# ⭐ Final Note

This project was not just about building features.

It became a deep learning experience in:

* production debugging
* infrastructure engineering
* OAuth security
* deployment workflows
* memory optimization
* scalable SaaS architecture

Building software locally is one thing.
Deploying and stabilizing it in production is where real engineering begins.
