from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0004_alter_emaillog_sent_by_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='responsescore',
            name='z_score',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='responsescore',
            name='percentile',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='responsescore',
            name='additional_data',
            field=models.JSONField(blank=True, help_text='Additional scoring data in JSON format', null=True),
        ),
        migrations.AddField(
            model_name='scorerule',
            name='conditional_logic',
            field=models.JSONField(blank=True, help_text='JSON configuration for conditional scoring logic', null=True),
        ),
    ]
