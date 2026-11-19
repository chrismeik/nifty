-- @db: nifty
-- @seed: marketing.leads append
-- @seed: marketing.raffle append

-- =============================================================================
-- SCHEMA: marketing
-- CRM and lead capture for the Nifty product line.
-- =============================================================================

-- <product id="93d9b7ae-3b27-4a76-82bf-ff008425627c">
CREATE SCHEMA IF NOT EXISTS marketing;

-- <product id="c5d18042-39b2-4787-8ac5-dd44f9a9a707">
CREATE TABLE IF NOT EXISTS marketing.leads (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(255) NOT NULL,
    phone_number        VARCHAR(30) NOT NULL,
    district_name       VARCHAR(255) NOT NULL,
    email               VARCHAR(255),
    source              VARCHAR(50),
    sis_name            VARCHAR(100),
    demo_availability   VARCHAR(100),
    student_count       INTEGER,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS marketing.raffle (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id             UUID NOT NULL REFERENCES marketing.leads(id),
    raffle_location     VARCHAR(255) NOT NULL DEFAULT 'Kansas City',
    raffle_group        INTEGER NOT NULL DEFAULT 1,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS leads_raffle_dedup
    ON marketing.leads (phone_number, COALESCE(email, ''))
    WHERE source = 'raffle';
-- </product>

-- </product>
