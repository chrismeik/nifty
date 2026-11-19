-- @db: nifty

-- =============================================================================
-- SCHEMA: powerschool
-- Raw staging tables that mirror PowerSchool's field shapes.
-- Data lands here first before being transformed into core.
-- =============================================================================

-- <product id="b6d00b3f-f621-47d7-b15a-f1c8a7845f19">
CREATE SCHEMA IF NOT EXISTS powerschool;

-- <product id="48f7abe0-cfc7-4baa-9cdc-a381a455faf2">
CREATE TABLE IF NOT EXISTS powerschool.students (
    id                  SERIAL PRIMARY KEY,
    ps_student_id       INTEGER NOT NULL UNIQUE,
    student_number      VARCHAR(50),
    first_name          VARCHAR(100),
    last_name           VARCHAR(100),
    middle_name         VARCHAR(100),
    dob                 DATE,
    grade_level         INTEGER,
    school_id           INTEGER,
    enroll_status       INTEGER,
    home_room           VARCHAR(100),
    ingested_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
-- </product>

-- <product id="d5f37e73-87b7-4250-bfa4-a4755889ce14">
CREATE TABLE IF NOT EXISTS powerschool.attendance (
    id                  SERIAL PRIMARY KEY,
    ps_attendance_id    INTEGER NOT NULL UNIQUE,
    ps_student_id       INTEGER NOT NULL,
    school_id           INTEGER,
    att_date            DATE NOT NULL,
    period_abbreviation VARCHAR(50),
    att_code            VARCHAR(20),
    description         VARCHAR(255),
    ingested_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
-- </product>

-- <product id="3467cec7-e290-48b4-a148-f7f242985945">
CREATE TABLE IF NOT EXISTS powerschool.contacts (
    id                  SERIAL PRIMARY KEY,
    ps_contact_id       INTEGER NOT NULL UNIQUE,
    ps_student_id       INTEGER NOT NULL,
    first_name          VARCHAR(100),
    last_name           VARCHAR(100),
    relationship        VARCHAR(100),
    priority_order      INTEGER,
    phone               VARCHAR(30),
    email               VARCHAR(255),
    ingested_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
-- </product>

-- </product>
