-- @db: nifty

-- =============================================================================
-- SCHEMA: analytics
-- Derived and aggregated tables owned by the notify pipeline.
-- =============================================================================

-- <product id="a1977afe-0e10-441d-a41d-be2028637ed2">
CREATE SCHEMA IF NOT EXISTS analytics;

-- <product id="0940e4f2-762b-458b-9f5b-cae909108ec7">
CREATE TABLE IF NOT EXISTS analytics.student_absence_summary (
    student_unique_id   VARCHAR(50) NOT NULL REFERENCES core.students(student_unique_id),
    school_id           INTEGER NOT NULL REFERENCES core.schools(school_id),
    session_name        VARCHAR(100) NOT NULL,
    school_year         INTEGER NOT NULL,
    total_absences      INTEGER NOT NULL DEFAULT 0,
    last_updated        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (student_unique_id, school_id, session_name, school_year)
);
-- </product>

-- <product id="4c296ba1-bbe7-4fd4-87bd-e6914c022219">
CREATE TABLE IF NOT EXISTS analytics.notification_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id              UUID,
    student_unique_id   VARCHAR(50) REFERENCES core.students(student_unique_id),
    contact_unique_id   VARCHAR(50) REFERENCES core.contacts(contact_unique_id),
    phone_number        VARCHAR(30),
    event_date          DATE NOT NULL,
    status              VARCHAR(50) NOT NULL
                            CHECK (status IN ('sent', 'failed', 'skipped')),
    broadcast_id        VARCHAR(255),
    error_message       TEXT,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
-- </product>

-- </product>
