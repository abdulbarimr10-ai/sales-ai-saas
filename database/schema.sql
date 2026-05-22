-- schema.sql

-- 1. Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    serper_api_key TEXT,
    openai_api_key TEXT,
    apollo_api_key TEXT,
    gemini_api_key TEXT,
    claude_api_key TEXT,
    preferred_model TEXT DEFAULT 'ollama',
    gmail_credentials TEXT, -- JSON string for OAuth tokens
    gmail_address TEXT
);

-- 2. History table
CREATE TABLE IF NOT EXISTS history (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    intent TEXT,
    command TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Leads table
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT,
    industry TEXT,
    website TEXT,
    description TEXT,
    analysis TEXT,
    outreach_email TEXT,
    email_draft TEXT DEFAULT '',
    roi_data TEXT DEFAULT '',
    linkedin_url TEXT DEFAULT '',
    google_rating REAL DEFAULT 0.0,
    review_summary TEXT DEFAULT '',
    detected_problem TEXT DEFAULT '',
    priority TEXT DEFAULT 'low',
    email_sent INTEGER DEFAULT 0,
    send_status TEXT DEFAULT '',
    last_contacted TEXT DEFAULT '',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
