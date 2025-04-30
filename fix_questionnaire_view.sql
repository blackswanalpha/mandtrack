-- Drop the existing view if it exists
DROP VIEW IF EXISTS surveys_questionnaire;

-- Create a new view with all the columns from surveys_survey plus the missing columns
CREATE VIEW surveys_questionnaire AS 
SELECT 
    id,
    title,
    slug,
    description,
    instructions,
    'standard'::varchar AS type,  -- Add default value for type
    category,
    0 AS estimated_time,  -- Add default value for estimated_time
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
