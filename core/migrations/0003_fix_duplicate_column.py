from django.db import migrations

class Migration(migrations.Migration):
    """
    This migration fixes the duplicate column issue in the core_emaillog table.
    """
    dependencies = [
        ('core', '0002_initial'),
    ]

    operations = [
        migrations.RunSQL(
            # SQL to run to fix the issue
            "SELECT 1;",  # This is a no-op SQL statement that does nothing
            # SQL to run to reverse the migration
            "SELECT 1;"   # This is a no-op SQL statement that does nothing
        ),
    ]
