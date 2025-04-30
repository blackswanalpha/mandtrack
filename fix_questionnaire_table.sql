-- Check if surveys_questionnaire exists and create it as a view if it doesn't
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
        AND c.relname = 'surveys_questionnaire'
    ) THEN
        -- Create a view that points to the actual table
        EXECUTE 'CREATE VIEW surveys_questionnaire AS SELECT * FROM surveys_survey';
    END IF;
END
$$;
