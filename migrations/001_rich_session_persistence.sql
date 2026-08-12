-- Migration 001: Rich Session Persistence & Analytics Pipeline
-- Modifies analytics metric columns in public.pose_sessions so NULL indicates unmeasured/unavailable metrics

ALTER TABLE public.pose_sessions
    ADD COLUMN IF NOT EXISTS reps integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS symmetry_score double precision NULL,
    ADD COLUMN IF NOT EXISTS balance_score double precision NULL,
    ADD COLUMN IF NOT EXISTS stability_score double precision NULL,
    ADD COLUMN IF NOT EXISTS rom_score double precision NULL,
    ADD COLUMN IF NOT EXISTS hold_time double precision NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS tracking_quality double precision NULL,
    ADD COLUMN IF NOT EXISTS failed_rules jsonb NOT NULL DEFAULT '[]'::jsonb;

-- Remove default 100.0 if present from prior migrations
ALTER TABLE public.pose_sessions
    ALTER COLUMN symmetry_score DROP DEFAULT,
    ALTER COLUMN balance_score DROP DEFAULT,
    ALTER COLUMN stability_score DROP DEFAULT,
    ALTER COLUMN rom_score DROP DEFAULT,
    ALTER COLUMN tracking_quality DROP DEFAULT;
