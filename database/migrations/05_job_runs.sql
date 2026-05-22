-- Migration: 05_job_runs.sql

CREATE TABLE IF NOT EXISTS job_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_job_runs_user_id ON job_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_job_runs_status ON job_runs(status);
CREATE INDEX IF NOT EXISTS idx_job_runs_created_at ON job_runs(created_at);
