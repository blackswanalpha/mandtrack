from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0004_merge_20250505_1156'),
    ]

    operations = [
        migrations.DeleteModel(
            name='EmailSchedule',
        ),
    ]
