-- =============================================================================
-- SCHEMA: platform
-- Platform-level operational tables shared across all products.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS platform;

CREATE TABLE IF NOT EXISTS platform.jobs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product     VARCHAR(100) NOT NULL,
    job_type    VARCHAR(100) NOT NULL,
    target_date DATE,
    scope       VARCHAR(255),
    status      VARCHAR(50) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'running', 'done', 'failed')),
    started_at  TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    error       TEXT,
    metadata    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE platform.jobs ADD COLUMN IF NOT EXISTS scope VARCHAR(255);

-- One completed job per product/job_type/date/scope — prevents duplicate runs.
-- scope is nullable so NULLIF is used to treat NULL as a distinct value per row.
CREATE UNIQUE INDEX IF NOT EXISTS jobs_done_unique
    ON platform.jobs (product, job_type, target_date, COALESCE(scope, ''))
    WHERE status = 'done';


-- =============================================================================
-- SCHEMA: system
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS system;

CREATE TABLE IF NOT EXISTS system.products (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL UNIQUE,
    type        VARCHAR(50),
    description TEXT,
    status      VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


-- Tracks parent/child relationships between products.
-- source_id → target_id with a typed edge (child, parent).
CREATE TABLE IF NOT EXISTS system.product_relationships (
    source_id   UUID NOT NULL REFERENCES system.products(id) ON DELETE CASCADE,
    target_id   UUID NOT NULL REFERENCES system.products(id) ON DELETE CASCADE,
    kind        VARCHAR(50) NOT NULL CHECK (kind IN ('child', 'parent', 'dependency')),
    PRIMARY KEY (source_id, target_id, kind)
);
