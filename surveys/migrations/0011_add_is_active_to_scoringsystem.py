from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0010_add_fields_to_responsescore_manual'),
    ]

    operations = [
        migrations.AddField(
            model_name='scoringsystem',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
