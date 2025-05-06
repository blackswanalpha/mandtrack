from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='aianalysis',
            name='risk_level',
            field=models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical'), ('unknown', 'Unknown')], default='unknown', max_length=20),
        ),
        migrations.AddField(
            model_name='aianalysis',
            name='risk_justification',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='aianalysis',
            name='trends',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='aianalysis',
            name='follow_up_areas',
            field=models.TextField(blank=True),
        ),
    ]
