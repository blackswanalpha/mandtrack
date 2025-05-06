from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0011_add_is_active_to_scoringsystem'),
    ]

    operations = [
        migrations.AddField(
            model_name='scoringsystem',
            name='is_default',
            field=models.BooleanField(default=False),
        ),
    ]
