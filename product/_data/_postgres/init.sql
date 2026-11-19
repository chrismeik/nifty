-- @db: nifty
-- @seed: core.local_education_agencies latest
-- @seed: core.schools latest
-- @seed: core.sessions latest
-- @seed: core.sis_configurations latest

-- =============================================================================
-- SCHEMA: core
-- Ed-Fi canonical entities. SIS-agnostic. Shared across all nifty products.
-- Field and table names follow the Ed-Fi Data Standard.
-- =============================================================================

-- <product id="f93408de-b1f4-4b54-a63b-f8a4b2bba070">
CREATE SCHEMA IF NOT EXISTS core;

-- <product id="dd00f271-6b19-40e5-9d73-d9cc06410dd0">
CREATE TABLE IF NOT EXISTS core.local_education_agencies (
    local_education_agency_id   INTEGER PRIMARY KEY,
    name_of_institution         VARCHAR(255) NOT NULL,
    state_organization_id       VARCHAR(100),
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    modified_at                 TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
-- </product>

-- <product id="8a38c779-ebc0-41f4-a890-57e8041e2df1">
CREATE TABLE IF NOT EXISTS core.schools (
    school_id                   INTEGER PRIMARY KEY,
    local_education_agency_id   INTEGER NOT NULL REFERENCES core.local_education_agencies(local_education_agency_id),
    name_of_institution         VARCHAR(255) NOT NULL,
    short_name                  VARCHAR(100),
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    modified_at                 TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
-- </product>

-- <product id="896d59f0-87b7-40c7-ba25-db4a61ada2cb">
CREATE TABLE IF NOT EXISTS core.sessions (
    session_name                VARCHAR(100) NOT NULL,
    school_id                   INTEGER NOT NULL REFERENCES core.schools(school_id),
    school_year                 INTEGER NOT NULL,
    term_descriptor             VARCHAR(100) NOT NULL DEFAULT 'Full Year',
    begin_date                  DATE NOT NULL,
    end_date                    DATE NOT NULL,
    total_instructional_days    INTEGER,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    modified_at                 TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (session_name, school_id, school_year)
);
-- </product>

-- <product id="d9518aa6-aa59-4d7f-ac9d-0e43f6fcc257">
CREATE TABLE IF NOT EXISTS core.students (
    student_unique_id           VARCHAR(50) PRIMARY KEY,
    first_name                  VARCHAR(100) NOT NULL,
    last_name                   VARCHAR(100) NOT NULL,
    middle_name                 VARCHAR(100),
    birth_date                  DATE,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    modified_at                 TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
-- </product>

-- <product id="ec6bad7b-7554-4a14-ad77-c7554f8e6a99">
CREATE TABLE IF NOT EXISTS core.student_school_associations (
    student_unique_id           VARCHAR(50) NOT NULL REFERENCES core.students(student_unique_id),
    school_id                   INTEGER NOT NULL REFERENCES core.schools(school_id),
    entry_date                  DATE NOT NULL,
    entry_grade_level_descriptor VARCHAR(50),
    exit_withdraw_date          DATE,
    primary_school              BOOLEAN NOT NULL DEFAULT TRUE,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    modified_at                 TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (student_unique_id, school_id, entry_date)
);
-- </product>

-- <product id="1a3d33bc-a584-4f78-8d2b-bb6409effe96">
CREATE TABLE IF NOT EXISTS core.contacts (
    contact_unique_id           VARCHAR(50) PRIMARY KEY,
    first_name                  VARCHAR(100) NOT NULL,
    last_name                   VARCHAR(100) NOT NULL,
    telephone_number            VARCHAR(30),
    email_address               VARCHAR(255),
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    modified_at                 TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
-- </product>

-- <product id="21e23d3c-f935-42e0-a913-e1477be90f99">
CREATE TABLE IF NOT EXISTS core.student_contact_associations (
    student_unique_id           VARCHAR(50) NOT NULL REFERENCES core.students(student_unique_id),
    contact_unique_id           VARCHAR(50) NOT NULL REFERENCES core.contacts(contact_unique_id),
    relation_descriptor         VARCHAR(100),
    primary_contact_indicator   BOOLEAN NOT NULL DEFAULT FALSE,
    emergency_contact_status    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    modified_at                 TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (student_unique_id, contact_unique_id)
);
-- </product>

-- <product id="21854b64-c21d-4561-bdc1-c2374c133be8">
CREATE TABLE IF NOT EXISTS core.sis_configurations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id           INTEGER NOT NULL REFERENCES core.schools(school_id),
    sis_type            VARCHAR(100) NOT NULL,
    connection_config   JSONB NOT NULL DEFAULT '{}',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    activated_at        TIMESTAMP WITH TIME ZONE,
    deactivated_at      TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    modified_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS sis_config_active_unique
    ON core.sis_configurations (school_id)
    WHERE is_active = TRUE;
-- </product>

-- <product id="742b2e9e-880b-4219-a19b-6370c9ae321f">
CREATE TABLE IF NOT EXISTS core.student_school_attendance_events (
    student_unique_id                    VARCHAR(50) NOT NULL REFERENCES core.students(student_unique_id),
    school_id                            INTEGER NOT NULL REFERENCES core.schools(school_id),
    event_date                           DATE NOT NULL,
    attendance_event_category_descriptor VARCHAR(100) NOT NULL,
    attendance_event_reason              VARCHAR(255),
    created_at                           TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    modified_at                          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (student_unique_id, school_id, event_date, attendance_event_category_descriptor)
);
-- </product>

-- </product>
