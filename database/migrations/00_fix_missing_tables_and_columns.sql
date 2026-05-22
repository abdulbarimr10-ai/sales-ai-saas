-- Migration: 00_fix_missing_tables_and_columns.sql
-- Purpose: Create missing tables (history, leads) and add missing columns to users table.
-- Safe to run multiple times (uses IF NOT EXISTS / IF NOT EXISTS patterns).

-- =============================================
-- 1. Fix users table - add missing columns
-- =============================================
DO $$
BEGIN
    -- Add serper_api_key if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='serper_api_key') THEN
        ALTER TABLE users ADD COLUMN serper_api_key TEXT;
    END IF;

    -- Add openai_api_key if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='openai_api_key') THEN
        ALTER TABLE users ADD COLUMN openai_api_key TEXT;
    END IF;

    -- Add apollo_api_key if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='apollo_api_key') THEN
        ALTER TABLE users ADD COLUMN apollo_api_key TEXT;
    END IF;

    -- Add gemini_api_key if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='gemini_api_key') THEN
        ALTER TABLE users ADD COLUMN gemini_api_key TEXT;
    END IF;

    -- Add claude_api_key if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='claude_api_key') THEN
        ALTER TABLE users ADD COLUMN claude_api_key TEXT;
    END IF;

    -- Add preferred_model if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='preferred_model') THEN
        ALTER TABLE users ADD COLUMN preferred_model TEXT DEFAULT 'ollama';
    END IF;

    -- Add gmail_credentials if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='gmail_credentials') THEN
        ALTER TABLE users ADD COLUMN gmail_credentials TEXT;
    END IF;

    -- Add gmail_address if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='gmail_address') THEN
        ALTER TABLE users ADD COLUMN gmail_address TEXT;
    END IF;
END $$;

-- =============================================
-- 2. Create history table if missing
-- =============================================
CREATE TABLE IF NOT EXISTS history (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    intent TEXT,
    command TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- 3. Create leads table if missing
-- =============================================
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
