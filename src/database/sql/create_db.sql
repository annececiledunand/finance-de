BEGIN;

-- drop tables in reverse order of creation
DROP TABLE IF EXISTS job CASCADE;
DROP TABLE IF EXISTS person CASCADE;
DROP TABLE IF EXISTS organization CASCADE;

-- Create person table
CREATE TABLE IF NOT EXISTS person (
    person_id SERIAL PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    middle_name VARCHAR(255),
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR NOT NULL,
    phone VARCHAR(20),  -- in number would generate very big numbers in memory, not needed. Longest phone number is under 20 char ?
    fax VARCHAR,
    title VARCHAR,
    UNIQUE (first_name, middle_name, last_name)
);

-- Create organization table
CREATE TABLE IF NOT EXISTS organization (
    org_id SERIAL PRIMARY KEY,
    org_name VARCHAR(255) NOT NULL,
    org_vivo_uri VARCHAR(255)
);

-- drop if exists and create mimics create if not exists for type
DROP TYPE IF EXISTS job_type_enum CASCADE;
CREATE TYPE job_type_enum AS ENUM (
    'professor',
    'assistant_professor',
    'curator',
    'associate_curator'
);


-- Create job table with foreign key references to person & organization
CREATE TABLE IF NOT EXISTS job (
    job_id SERIAL PRIMARY KEY,
    person_id INT REFERENCES person(person_id) ON DELETE CASCADE,
    org_id INT REFERENCES organization(org_id) ON DELETE CASCADE,
    job_type VARCHAR NOT NULL,  -- TODO: go back to enum. Issue with insert
    job_title VARCHAR NOT NULL,
    start_date DATE DEFAULT CURRENT_DATE
);

COMMIT;