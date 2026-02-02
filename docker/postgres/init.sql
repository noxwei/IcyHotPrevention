-- IETY PostgreSQL Initialization Script
-- Enables required extensions and creates schemas

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create schemas for each data source
CREATE SCHEMA IF NOT EXISTS usaspending;
CREATE SCHEMA IF NOT EXISTS sec;
CREATE SCHEMA IF NOT EXISTS legal;
CREATE SCHEMA IF NOT EXISTS gdelt;
CREATE SCHEMA IF NOT EXISTS integration;

-- Grant permissions (adjust as needed for production)
GRANT ALL PRIVILEGES ON SCHEMA usaspending TO iety;
GRANT ALL PRIVILEGES ON SCHEMA sec TO iety;
GRANT ALL PRIVILEGES ON SCHEMA legal TO iety;
GRANT ALL PRIVILEGES ON SCHEMA gdelt TO iety;
GRANT ALL PRIVILEGES ON SCHEMA integration TO iety;

-- Verify extensions are installed
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE EXCEPTION 'pgvector extension not installed';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm') THEN
        RAISE EXCEPTION 'pg_trgm extension not installed';
    END IF;
    RAISE NOTICE 'All required extensions installed successfully';
END $$;
