from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0013_merge_20250505_1322'),
    ]

    operations = [
        # This is now a no-op migration since the column already exists
        # We'll keep it for migration history consistency
        migrations.RunSQL(
            sql="""
            -- No-op migration - column already exists
            SELECT 1;
            """,
            reverse_sql="""
            -- No-op reverse migration
            SELECT 1;
            """
        ),
    ]
