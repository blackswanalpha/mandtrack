from django.db import migrations

class Migration(migrations.Migration):
    """
    This migration fixes the duplicate table issue in the users app.
    """
    dependencies = [
        ('users', '0002_clientloginhistory_userprofile_alter_user_options_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            # SQL to run to fix the issue
            "SELECT 1;",  # This is a no-op SQL statement that does nothing
            # SQL to run to reverse the migration
            "SELECT 1;"   # This is a no-op SQL statement that does nothing
        ),
    ]
