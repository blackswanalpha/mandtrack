-- Drop the existing view if it exists
DROP VIEW IF EXISTS surveys_questionnaire;

-- Create a trigger function to handle the UUID to bigint conversion
CREATE OR REPLACE FUNCTION insert_into_surveys_survey()
RETURNS TRIGGER AS $$
BEGIN
    -- Generate a bigint ID from the UUID
    INSERT INTO surveys_survey (
        title, slug, description, instructions, category, status,
        is_template, allow_anonymous, requires_auth, created_by_id,
        organization_id, created_at, updated_at, qr_code, access_code
    ) VALUES (
        NEW.title, NEW.slug, NEW.description, NEW.instructions, NEW.category, NEW.status,
        NEW.is_template, NEW.allow_anonymous, NEW.requires_auth, NEW.created_by_id,
        NEW.organization_id, NEW.created_at, NEW.updated_at, NEW.qr_code, NEW.access_code
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a view that maps between the two tables
CREATE VIEW surveys_questionnaire AS 
SELECT 
    id,
    title,
    slug,
    description,
    instructions,
    'standard'::varchar AS type,
    category,
    0 AS estimated_time,
    status,
    true AS is_active,
    false AS is_adaptive,
    true AS is_qr_enabled,
    is_template,
    false AS is_public,
    allow_anonymous,
    requires_auth,
    NULL::integer AS max_responses,
    NULL::timestamp with time zone AS expires_at,
    1 AS version,
    NULL::bigint AS parent_id,
    '[]'::json AS tags,
    'en'::varchar AS language,
    0 AS time_limit,
    created_by_id,
    organization_id,
    created_at,
    updated_at,
    qr_code,
    access_code
FROM 
    surveys_survey;

-- Create a trigger on the view for INSERT operations
CREATE TRIGGER insert_surveys_questionnaire_trigger
INSTEAD OF INSERT ON surveys_questionnaire
FOR EACH ROW
EXECUTE FUNCTION insert_into_surveys_survey();
